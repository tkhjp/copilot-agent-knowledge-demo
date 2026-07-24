from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .project import input_files, repository_root, source_state
from .render import render_graph, render_knowledge
from .scanner import scan_repository


def build(
    *,
    root: Path,
    generated_dir: Path,
    graph_dir: Path,
    clean: bool = True,
) -> dict[str, object]:
    if clean:
        shutil.rmtree(generated_dir, ignore_errors=True)
        # Keep existing graph archives long enough for render_graph() to avoid
        # rewriting semantically identical gzip payloads with different zlib
        # bitstreams. Unexpected files are pruned by render_graph().
        graph_dir.mkdir(parents=True, exist_ok=True)
    paths = input_files(root)
    graph = scan_repository(root, paths)
    graph_artifacts = render_graph(graph, graph_dir)
    return render_knowledge(
        graph=graph,
        generated_dir=generated_dir,
        source_state=source_state(root),
        graph_artifacts=graph_artifacts,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic agent knowledge.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path("docs/agent-knowledge/generated"),
    )
    parser.add_argument(
        "--graph-dir",
        type=Path,
        default=Path("artifacts/codegraph"),
    )
    args = parser.parse_args()

    root = repository_root(args.root)
    generated_dir = args.generated_dir
    graph_dir = args.graph_dir
    if not generated_dir.is_absolute():
        generated_dir = root / generated_dir
    if not graph_dir.is_absolute():
        graph_dir = root / graph_dir

    manifest = build(
        root=root,
        generated_dir=generated_dir,
        graph_dir=graph_dir,
    )
    print(
        f"generated {manifest['graph']['node_count']} nodes and "
        f"{manifest['graph']['edge_count']} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
