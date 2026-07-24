from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import GENERATOR_VERSION, SCHEMA_VERSION
from .project import read_json, repository_root, source_state


def freshness(root: Path, manifest_path: Path) -> dict[str, object]:
    current = source_state(root)
    if not manifest_path.exists():
        return {
            "fresh": False,
            "reason": "manifest-missing",
            "manifest": manifest_path.relative_to(root).as_posix()
            if manifest_path.is_relative_to(root)
            else str(manifest_path),
            "current_source_digest": current["source_digest"],
        }

    manifest = read_json(manifest_path)
    reasons: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        reasons.append("schema-version-mismatch")
    if manifest.get("generator_version") != GENERATOR_VERSION:
        reasons.append("generator-version-mismatch")
    if manifest.get("source_digest") != current["source_digest"]:
        reasons.append("source-digest-mismatch")
    return {
        "fresh": not reasons,
        "reason": ",".join(reasons) if reasons else "current",
        "manifest_source_digest": manifest.get("source_digest"),
        "current_source_digest": current["source_digest"],
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check committed knowledge freshness.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/agent-knowledge/generated/manifest.json"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = repository_root(args.root)
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    result = freshness(root, manifest_path)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"knowledge freshness: {'fresh' if result['fresh'] else 'stale'}")
        print(f"reason: {result['reason']}")
    return 0 if result["fresh"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
