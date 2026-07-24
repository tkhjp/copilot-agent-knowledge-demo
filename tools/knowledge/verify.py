from __future__ import annotations

import filecmp
import gzip
import shutil
import tempfile
from pathlib import Path

from .build import build
from .project import repository_root


def _files_equal(expected: Path, actual: Path) -> bool:
    if expected.name.endswith(".jsonl.gz") and actual.name.endswith(".jsonl.gz"):
        try:
            return gzip.decompress(expected.read_bytes()) == gzip.decompress(
                actual.read_bytes()
            )
        except (OSError, EOFError):
            return False
    return expected.read_bytes() == actual.read_bytes()


def _compare_dirs(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    comparison = filecmp.dircmp(expected, actual)
    for name in comparison.left_only:
        differences.append(f"missing from regenerated output: {expected / name}")
    for name in comparison.right_only:
        differences.append(f"unexpected regenerated output: {actual / name}")
    for name in comparison.common_files:
        expected_file = expected / name
        actual_file = actual / name
        if not _files_equal(expected_file, actual_file):
            differences.append(f"content differs: {expected_file}")
    for name in comparison.common_funny:
        differences.append(f"cannot compare generated path: {expected / name}")
    for name in comparison.common_dirs:
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
