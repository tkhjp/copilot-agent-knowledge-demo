from __future__ import annotations

import filecmp
import shutil
import tempfile
from pathlib import Path

from .build import build
from .project import repository_root


def _compare_dirs(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    comparison = filecmp.dircmp(expected, actual)
    for name in comparison.left_only:
        differences.append(f"missing from regenerated output: {expected / name}")
    for name in comparison.right_only:
        differences.append(f"unexpected regenerated output: {actual / name}")
    for name in comparison.diff_files:
        differences.append(f"content differs: {expected / name}")
    for name, subcomparison in comparison.subdirs.items():
        differences.extend(_compare_dirs(expected / name, actual / name))
    return differences


def main() -> int:
    root = repository_root()
    expected_generated = root / "docs/agent-knowledge/generated"
    expected_graph = root / "artifacts/codegraph"
    with tempfile.TemporaryDirectory(prefix="agent-knowledge-") as temporary:
        temp_root = Path(temporary)
        regenerated = temp_root / "generated"
        graph = temp_root / "codegraph"
        build(root=root, generated_dir=regenerated, graph_dir=graph)
        differences = _compare_dirs(expected_generated, regenerated)
        differences.extend(_compare_dirs(expected_graph, graph))
    if differences:
        print("generated knowledge is out of date:")
        for difference in differences:
            print(f"- {difference}")
        print("run `make knowledge` and commit the resulting files")
        return 1
    print("generated knowledge matches the current source tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
