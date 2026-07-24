from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .build import build
from .check_freshness import freshness
from .project import git_head, repository_root


def prepare(root: Path) -> dict[str, object]:
    runtime_root = root / ".agent-runtime/knowledge"
    runtime_root.mkdir(parents=True, exist_ok=True)
    committed_manifest = root / "docs/agent-knowledge/generated/manifest.json"
    state = freshness(root, committed_manifest)

    if state["fresh"]:
        shutil.rmtree(runtime_root / "generated", ignore_errors=True)
        shutil.rmtree(runtime_root / "codegraph", ignore_errors=True)
        generated_path = "docs/agent-knowledge/generated"
        graph_path = "artifacts/codegraph"
    else:
        build(
            root=root,
            generated_dir=runtime_root / "generated",
            graph_dir=runtime_root / "codegraph",
        )
        generated_path = ".agent-runtime/knowledge/generated"
        graph_path = ".agent-runtime/knowledge/codegraph"

    head = git_head(root) or "uncommitted-or-not-a-git-repository"
    context_path = root / ".agent-runtime/active-context.md"
    context = "\n".join(
        [
            "# Active agent knowledge context",
            "",
            f"- Git HEAD: `{head}`",
            f"- Committed knowledge status: `{'fresh' if state['fresh'] else 'stale'}`",
            f"- Freshness reason: `{state['reason']}`",
            f"- Generated knowledge path: `{generated_path}`",
            f"- Code graph path: `{graph_path}`",
            "- Curated rules path: `docs/agent-knowledge/curated`",
            "",
            "## Precedence",
            "",
            "1. Current working-tree source code.",
            "2. Runtime-generated branch knowledge under `.agent-runtime` when present.",
            "3. Committed generated knowledge under `docs/agent-knowledge/generated`.",
            "4. Curated domain and test rules.",
            "5. Historical issues, pull requests, Wiki pages, and session logs.",
            "",
            "Never treat a generated graph edge as proof of runtime behavior. Verify the current implementation and run tests.",
            "",
        ]
    )
    context_path.write_text(context, encoding="utf-8")
    return {
        "fresh": state["fresh"],
        "reason": state["reason"],
        "head": head,
        "context_path": context_path.relative_to(root).as_posix(),
        "generated_path": generated_path,
        "graph_path": graph_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare branch-aware agent context.")
    parser.add_argument("--hook", action="store_true")
    args = parser.parse_args()
    root = repository_root()
    result = prepare(root)
    if args.hook:
        message = (
            "Agent knowledge context prepared. "
            f"Read `{result['context_path']}` before planning. "
            f"Committed knowledge is {'fresh' if result['fresh'] else 'stale'}; "
            f"use `{result['generated_path']}` and `{result['graph_path']}`."
        )
        print(json.dumps({"additionalContext": message}, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
