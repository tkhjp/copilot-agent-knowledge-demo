from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

from .model import Edge, Graph, Node
from .project import write_json


def _canonical_jsonl(records: list[dict[str, object]]) -> bytes:
    return "".join(
        json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        for record in records
    ).encode("utf-8")


def write_jsonl_gzip(path: Path, records: list[dict[str, object]]) -> str:
    """Write JSON Lines as gzip and return the canonical content digest.

    The gzip container is a transport detail: zlib implementations may emit
    different, valid DEFLATE streams for identical input. The stable identity
    of a graph artifact is therefore the SHA-256 of its uncompressed canonical
    JSONL payload.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_jsonl(records)
    digest = hashlib.sha256(payload).hexdigest()

    if path.exists():
        try:
            if gzip.decompress(path.read_bytes()) == payload:
                return digest
        except (OSError, EOFError):
            pass

    archive = bytearray(gzip.compress(payload, compresslevel=9, mtime=0))
    # Python 3.11 and 3.12 may copy a platform-specific OS byte from zlib.
    # Normalizing it reduces avoidable binary churn, while semantic validation
    # remains authoritative across zlib versions.
    if len(archive) >= 10:
        archive[9] = 255
    path.write_bytes(bytes(archive))
    return digest


def render_graph(graph: Graph, graph_dir: Path) -> dict[str, str]:
    nodes_path = graph_dir / "nodes.jsonl.gz"
    edges_path = graph_dir / "edges.jsonl.gz"
    expected_names = {nodes_path.name, edges_path.name}
    graph_dir.mkdir(parents=True, exist_ok=True)
    for child in graph_dir.iterdir():
        if child.name not in expected_names:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    node_digest = write_jsonl_gzip(
        nodes_path, [node.to_dict() for node in graph.nodes]
    )
    edge_digest = write_jsonl_gzip(
        edges_path, [edge.to_dict() for edge in graph.edges]
    )
    return {
        nodes_path.name: node_digest,
        edges_path.name: edge_digest,
    }


def render_knowledge(
    *,
    graph: Graph,
    generated_dir: Path,
    source_state: dict[str, object],
    graph_artifacts: dict[str, str],
) -> dict[str, object]:
    generated_dir.mkdir(parents=True, exist_ok=True)
    modules_dir = generated_dir / "modules"
    impact_dir = generated_dir / "test-impact"
    modules_dir.mkdir(parents=True, exist_ok=True)
    impact_dir.mkdir(parents=True, exist_ok=True)

    system_path = generated_dir / "system-overview.md"
    system_path.write_text(_system_overview(graph), encoding="utf-8")

    package_names = sorted(
        {
            _package_name(node)
            for node in graph.nodes
            if node.path.startswith("src/") and node.kind == "module"
        }
    )
    generated_files = [system_path]
    for package_name in package_names:
        slug = package_name.replace("_", "-")
        module_path = modules_dir / f"{slug}.md"
        impact_path = impact_dir / f"{slug}.md"
        module_path.write_text(_module_page(graph, package_name), encoding="utf-8")
        impact_path.write_text(_test_impact_page(graph, package_name), encoding="utf-8")
        generated_files.extend([module_path, impact_path])

    artifact_digests = {
        path.relative_to(generated_dir).as_posix(): _sha256(path)
        for path in generated_files
    }
    manifest: dict[str, object] = {
        **source_state,
        "graph": {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "artifact_digest_basis": "sha256-uncompressed-canonical-jsonl",
            "artifacts": graph_artifacts,
        },
        "knowledge_artifacts": artifact_digests,
        "packages": package_names,
    }
    write_json(generated_dir / "manifest.json", manifest)
    return manifest


def _system_overview(graph: Graph) -> str:
    production = [node for node in graph.nodes if node.path.startswith("src/")]
    tests = [node for node in graph.nodes if node.kind == "test"]
    classes = [node for node in production if node.kind == "class"]
    call_edges = [edge for edge in graph.edges if edge.kind == "calls"]
    external_calls = [edge for edge in call_edges if edge.target.startswith("external:")]

    lines = [
        "# Generated system overview",
        "",
        "> Generated deterministically from the current Python source tree. Do not edit by hand.",
        "",
        "## Inventory",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| Production symbols | {len(production)} |",
        f"| Classes | {len(classes)} |",
        f"| Test functions | {len(tests)} |",
        f"| Call edges | {len(call_edges)} |",
        f"| External or unresolved calls | {len(external_calls)} |",
        "",
        "## Production modules",
        "",
    ]
    for node in production:
        if node.kind == "module":
            summary = _first_sentence(node.doc) or "No module docstring."
            lines.append(f"- `{node.qualified_name}` — {summary}")
    lines.extend(
        [
            "",
            "## Agent usage",
            "",
            "Use the `test-knowledge` skill to check freshness and query a narrow symbol neighborhood before generating tests.",
            "The current source code remains authoritative when any generated knowledge conflicts with implementation.",
            "",
        ]
    )
    return "\n".join(lines)


def _module_page(graph: Graph, package_name: str) -> str:
    nodes = [
        node
        for node in graph.nodes
        if node.path.startswith("src/") and _package_name(node) == package_name
    ]
    node_ids = {node.id for node in nodes}
    edges = [edge for edge in graph.edges if edge.source in node_ids]
    lines = [
        f"# Generated module knowledge: `{package_name}`",
        "",
        "> Generated deterministically. Verify claims against the current source before editing code.",
        "",
        "## Responsibilities",
        "",
    ]
    module_docs = [node for node in nodes if node.kind == "module" and node.doc]
    if module_docs:
        for node in module_docs:
            lines.append(f"- `{node.qualified_name}`: {_first_sentence(node.doc)}")
    else:
        lines.append("- No module-level responsibility was documented.")

    lines.extend(["", "## Symbols", ""])
    for node in nodes:
        if node.kind == "module":
            continue
        description = _first_sentence(node.doc) or "No docstring."
        lines.append(
            f"- `{node.qualified_name}` ({node.kind}, `{node.path}:{node.line}`) — {description}"
        )

    lines.extend(["", "## Static branch inventory", ""])
    branch_count = 0
    for node in nodes:
        for branch in node.branches:
            branch_count += 1
            lines.append(
                f"- `{node.qualified_name}` at `{node.path}:{branch.line}`: `{branch.condition}`"
            )
    if branch_count == 0:
        lines.append("- No `if` branches found.")

    lines.extend(["", "## Raised exceptions", ""])
    raised = False
    for node in nodes:
        if node.raises:
            raised = True
            lines.append(f"- `{node.qualified_name}`: {', '.join(f'`{item}`' for item in node.raises)}")
    if not raised:
        lines.append("- No explicit `raise` statements found.")

    lines.extend(["", "## Outbound calls", ""])
    call_edges = [edge for edge in edges if edge.kind == "calls"]
    node_map = graph.node_map()
    for edge in call_edges:
        source = node_map.get(edge.source)
        target = node_map.get(edge.target)
        source_name = source.qualified_name if source else edge.source
        target_name = target.qualified_name if target else edge.target.removeprefix("external:")
        lines.append(
            f"- `{source_name}` → `{target_name}` ({edge.resolution}, `{edge.path}:{edge.line}`)"
        )
    if not call_edges:
        lines.append("- No calls found.")

    lines.extend(["", "## Test generation guidance", ""])
    lines.extend(
        [
            "- Query the exact target symbol before writing a test.",
            "- Treat branch inventory as candidate cases, not proof of coverage.",
            "- Check curated domain rules and the current implementation before asserting behavior.",
            "- Prefer ports and protocols as mock boundaries.",
            "",
        ]
    )
    return "\n".join(lines)


def _test_impact_page(graph: Graph, package_name: str) -> str:
    production = [
        node
        for node in graph.nodes
        if node.path.startswith("src/")
        and _package_name(node) == package_name
        and node.kind in {"class", "function", "method"}
    ]
    test_nodes = {node.id: node for node in graph.nodes if node.kind == "test"}
    inbound: dict[str, list[Edge]] = defaultdict(list)
    for edge in graph.edges:
        if edge.kind == "calls" and edge.source in test_nodes:
            inbound[edge.target].append(edge)

    lines = [
        f"# Generated test-impact index: `{package_name}`",
        "",
        "> Static call relationships only. This is not a runtime coverage report.",
        "",
        "| Production symbol | Direct test callers | Static branches |",
        "|---|---|---:|",
    ]
    for node in production:
        callers = sorted(
            {
                test_nodes[edge.source].qualified_name
                for edge in inbound.get(node.id, [])
                if edge.source in test_nodes
            }
        )
        caller_text = "<br>".join(f"`{caller}`" for caller in callers) or "—"
        lines.append(f"| `{node.qualified_name}` | {caller_text} | {len(node.branches)} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A symbol with a direct test caller may still have untested branches. Use the graph query tool, read the current implementation, and run tests before making coverage claims.",
            "",
        ]
    )
    return "\n".join(lines)


def _package_name(node: Node) -> str:
    return node.qualified_name.split(".", 1)[0]


def _first_sentence(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    first = normalized.split(". ", 1)[0]
    return first if first.endswith(".") else first + "."


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
