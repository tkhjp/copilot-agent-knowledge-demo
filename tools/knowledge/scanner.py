from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .model import Branch, Edge, Graph, Node


@dataclass
class _RawCall:
    source: str
    name: str
    path: str
    line: int


@dataclass
class _RawImport:
    source: str
    name: str
    path: str
    line: int


class _FileScanner(ast.NodeVisitor):
    def __init__(self, *, root: Path, path: Path) -> None:
        self.root = root
        self.path = path
        self.relative = path.relative_to(root).as_posix()
        self.module_name = _module_name(root, path)
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []
        self.calls: list[_RawCall] = []
        self.imports: list[_RawImport] = []
        self._parents: list[str] = []
        self._function_nodes: list[str] = []

    def scan(self) -> None:
        tree = ast.parse(self.path.read_text(encoding="utf-8"), filename=self.relative)
        module_id = f"module:{self.module_name}"
        self.nodes.append(
            Node(
                id=module_id,
                kind="module",
                name=self.module_name.rsplit(".", 1)[-1],
                qualified_name=self.module_name,
                path=self.relative,
                line=1,
                end_line=max(1, getattr(tree, "end_lineno", 1) or 1),
                doc=ast.get_docstring(tree) or "",
            )
        )
        self._parents.append(module_id)
        self.generic_visit(tree)
        self._parents.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified = self._qualified(node.name)
        node_id = f"class:{qualified}"
        self.nodes.append(
            Node(
                id=node_id,
                kind="class",
                name=node.name,
                qualified_name=qualified,
                path=self.relative,
                line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                parent=self._parents[-1],
                doc=ast.get_docstring(node) or "",
            )
        )
        self.edges.append(
            Edge(
                source=self._parents[-1],
                target=node_id,
                kind="defines",
                path=self.relative,
                line=node.lineno,
            )
        )
        for base in node.bases:
            self.imports.append(
                _RawImport(
                    source=node_id,
                    name=_expression_name(base),
                    path=self.relative,
                    line=node.lineno,
                )
            )
        self._parents.append(node_id)
        self.generic_visit(node)
        self._parents.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = self._qualified(node.name)
        is_test = self.relative.startswith("tests/") and node.name.startswith("test_")
        kind = "test" if is_test else ("method" if self._parents[-1].startswith("class:") else "function")
        node_id = f"function:{qualified}"
        branches = tuple(
            Branch(line=item.lineno, condition=_safe_unparse(item.test))
            for item in ast.walk(node)
            if isinstance(item, ast.If)
        )
        raises = tuple(
            sorted(
                {
                    _expression_name(item.exc)
                    for item in ast.walk(node)
                    if isinstance(item, ast.Raise) and item.exc is not None
                }
            )
        )
        self.nodes.append(
            Node(
                id=node_id,
                kind=kind,
                name=node.name,
                qualified_name=qualified,
                path=self.relative,
                line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                parent=self._parents[-1],
                doc=ast.get_docstring(node) or "",
                branches=branches,
                raises=raises,
            )
        )
        self.edges.append(
            Edge(
                source=self._parents[-1],
                target=node_id,
                kind="defines",
                path=self.relative,
                line=node.lineno,
            )
        )
        self._parents.append(node_id)
        self._function_nodes.append(node_id)
        self.generic_visit(node)
        self._function_nodes.pop()
        self._parents.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._function_nodes:
            name = _call_name(node.func)
            if name:
                self.calls.append(
                    _RawCall(
                        source=self._function_nodes[-1],
                        name=name,
                        path=self.relative,
                        line=node.lineno,
                    )
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                _RawImport(
                    source=self._parents[0],
                    name=alias.name,
                    path=self.relative,
                    line=node.lineno,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(
                _RawImport(
                    source=self._parents[0],
                    name=name,
                    path=self.relative,
                    line=node.lineno,
                )
            )

    def _qualified(self, name: str) -> str:
        parts = [self.module_name]
        for parent in self._parents[1:]:
            parts.append(parent.split(":", 1)[1].rsplit(".", 1)[-1])
        parts.append(name)
        return ".".join(parts)


def scan_repository(root: Path, paths: list[Path]) -> Graph:
    nodes: list[Node] = []
    direct_edges: list[Edge] = []
    calls: list[_RawCall] = []
    imports: list[_RawImport] = []

    for path in paths:
        scanner = _FileScanner(root=root, path=path)
        scanner.scan()
        nodes.extend(scanner.nodes)
        direct_edges.extend(scanner.edges)
        calls.extend(scanner.calls)
        imports.extend(scanner.imports)

    by_simple_name: dict[str, list[Node]] = defaultdict(list)
    by_qualified_name: dict[str, Node] = {}
    for node in nodes:
        by_simple_name[node.name].append(node)
        by_qualified_name[node.qualified_name] = node

    resolved_edges = list(direct_edges)
    for raw in calls:
        candidates = _resolve_candidates(raw.name, by_simple_name, by_qualified_name)
        if not candidates:
            resolved_edges.append(
                Edge(
                    source=raw.source,
                    target=f"external:{raw.name}",
                    kind="calls",
                    path=raw.path,
                    line=raw.line,
                    resolution="external",
                )
            )
            continue
        resolution = "exact" if len(candidates) == 1 else "ambiguous"
        for candidate in candidates:
            resolved_edges.append(
                Edge(
                    source=raw.source,
                    target=candidate.id,
                    kind="calls",
                    path=raw.path,
                    line=raw.line,
                    resolution=resolution,
                )
            )

    for raw in imports:
        candidates = _resolve_candidates(raw.name, by_simple_name, by_qualified_name)
        if candidates:
            for candidate in candidates:
                resolved_edges.append(
                    Edge(
                        source=raw.source,
                        target=candidate.id,
                        kind="imports" if not raw.source.startswith("class:") else "inherits",
                        path=raw.path,
                        line=raw.line,
                        resolution="exact" if len(candidates) == 1 else "ambiguous",
                    )
                )
        else:
            resolved_edges.append(
                Edge(
                    source=raw.source,
                    target=f"external:{raw.name}",
                    kind="imports" if not raw.source.startswith("class:") else "inherits",
                    path=raw.path,
                    line=raw.line,
                    resolution="external",
                )
            )

    unique_edges = {
        (edge.source, edge.target, edge.kind, edge.path, edge.line, edge.resolution): edge
        for edge in resolved_edges
    }
    return Graph(
        nodes=tuple(sorted(nodes, key=lambda node: node.id)),
        edges=tuple(
            sorted(
                unique_edges.values(),
                key=lambda edge: (
                    edge.source,
                    edge.kind,
                    edge.target,
                    edge.path,
                    edge.line,
                ),
            )
        ),
    )


def _resolve_candidates(
    name: str,
    by_simple_name: dict[str, list[Node]],
    by_qualified_name: dict[str, Node],
) -> list[Node]:
    if name in by_qualified_name:
        return [by_qualified_name[name]]
    simple = name.rsplit(".", 1)[-1]
    candidates = by_simple_name.get(simple, [])
    production = [node for node in candidates if node.path.startswith("src/")]
    return production or candidates


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[0] in {"src", "tests"}:
        parts = parts[1:]
    return ".".join(parts)


def _safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def _expression_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expression_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _expression_name(node.func)
    return _safe_unparse(node)


def _call_name(node: ast.AST) -> str:
    return _expression_name(node)
