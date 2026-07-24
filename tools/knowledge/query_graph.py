from __future__ import annotations

import argparse
import gzip
import json
from collections import deque
from pathlib import Path
from typing import Any

from .project import repository_root


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = gzip.decompress(path.read_bytes()).decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def _graph_dir(root: Path) -> Path:
    runtime = root / ".agent-runtime/knowledge/codegraph"
    if (runtime / "nodes.jsonl.gz").exists():
        return runtime
    return root / "artifacts/codegraph"


def query(root: Path, symbol: str, depth: int) -> dict[str, object]:
    graph_dir = _graph_dir(root)
    nodes = _load_jsonl(graph_dir / "nodes.jsonl.gz")
    edges = _load_jsonl(graph_dir / "edges.jsonl.gz")
    node_map = {node["id"]: node for node in nodes}
    matches = [
        node
        for node in nodes
        if symbol.lower() in node["qualified_name"].lower()
        or symbol.lower() == node["name"].lower()
    ]
    if not matches:
        return {
            "graph_dir": graph_dir.relative_to(root).as_posix(),
            "matches": [],
            "message": f"no symbol matched {symbol!r}",
        }

    seed_ids = {node["id"] for node in matches}
    visited = set(seed_ids)
    queue: deque[tuple[str, int]] = deque((node_id, 0) for node_id in seed_ids)
    selected_edges: list[dict[str, Any]] = []
    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        for edge in edges:
            if edge["source"] == current or edge["target"] == current:
                selected_edges.append(edge)
                other = edge["target"] if edge["source"] == current else edge["source"]
                if other in node_map and other not in visited:
                    visited.add(other)
                    queue.append((other, current_depth + 1))

    unique_edges = {
        (
            edge["source"],
            edge["target"],
            edge["kind"],
            edge["path"],
            edge["line"],
            edge["resolution"],
        ): edge
        for edge in selected_edges
    }
    selected_edges = [unique_edges[key] for key in sorted(unique_edges)]
    selected_nodes = [node_map[node_id] for node_id in sorted(visited) if node_id in node_map]
    tests = [node for node in selected_nodes if node["kind"] == "test"]
    branches = [
        {
            "symbol": node["qualified_name"],
            "path": node["path"],
            **branch,
        }
        for node in selected_nodes
        for branch in node.get("branches", [])
    ]
    return {
        "graph_dir": graph_dir.relative_to(root).as_posix(),
        "matches": matches,
        "nodes": selected_nodes,
        "edges": selected_edges,
        "tests": tests,
        "branches": branches,
    }


def _render_text(result: dict[str, object]) -> str:
    if not result.get("matches"):
        return str(result.get("message"))
    lines = [
        f"Graph source: {result['graph_dir']}",
        "",
        "Matched symbols:",
    ]
    for node in result["matches"]:  # type: ignore[index]
        lines.append(
            f"- {node['qualified_name']} ({node['kind']}, {node['path']}:{node['line']})"
        )
    lines.extend(["", "Neighborhood:"])
    for edge in result["edges"]:  # type: ignore[index]
        lines.append(
            f"- {edge['source']} --{edge['kind']}--> {edge['target']} "
            f"[{edge['resolution']}]"
        )
    lines.extend(["", "Static branches:"])
    branches = result["branches"]  # type: ignore[index]
    if branches:
        for branch in branches:
            lines.append(
                f"- {branch['symbol']} at {branch['path']}:{branch['line']}: "
                f"{branch['condition']}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "Directly related tests:"])
    tests = result["tests"]  # type: ignore[index]
    if tests:
        for node in tests:
            lines.append(f"- {node['qualified_name']} ({node['path']}:{node['line']})")
    else:
        lines.append("- none found by static call analysis")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query a narrow code-graph neighborhood.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = repository_root()
    result = query(root, args.symbol, max(0, args.depth))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(_render_text(result))
    return 0 if result.get("matches") else 1


if __name__ == "__main__":
    raise SystemExit(main())
