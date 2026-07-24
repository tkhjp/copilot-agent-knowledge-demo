from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable

from . import GENERATOR_VERSION, SCHEMA_VERSION

INPUT_GLOBS = ("src/**/*.py", "tests/**/*.py")


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=candidate,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return Path(completed.stdout.strip()).resolve()
    return candidate


def git_head(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def input_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in INPUT_GLOBS:
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def digest_files(root: Path, files: Iterable[Path]) -> tuple[str, dict[str, str]]:
    aggregate = hashlib.sha256()
    per_file: dict[str, str] = {}
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        per_file[relative] = digest
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(content)
        aggregate.update(b"\0")
    return aggregate.hexdigest(), per_file


def source_state(root: Path) -> dict[str, object]:
    files = input_files(root)
    digest, per_file = digest_files(root, files)
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "source_digest": digest,
        "source_files": per_file,
    }


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
