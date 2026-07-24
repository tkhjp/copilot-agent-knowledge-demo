from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from tools.knowledge.render import write_jsonl_gzip
from tools.knowledge.verify import _compare_dirs


class GeneratedKnowledgeVerificationTest(unittest.TestCase):
    def test_recompressed_jsonl_is_semantically_equal(self) -> None:
        payload = b"".join(
            json.dumps({"id": index, "value": "x" * 80}, sort_keys=True).encode()
            + b"\n"
            for index in range(500)
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            expected_archive = gzip.compress(payload, compresslevel=1, mtime=0)
            actual_archive = gzip.compress(payload, compresslevel=9, mtime=0)
            self.assertNotEqual(expected_archive, actual_archive)
            (expected / "nodes.jsonl.gz").write_bytes(expected_archive)
            (actual / "nodes.jsonl.gz").write_bytes(actual_archive)

            self.assertEqual([], _compare_dirs(expected, actual))

    def test_invalid_gzip_is_reported_as_content_difference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            expected_file = expected / "nodes.jsonl.gz"
            actual_file = actual / "nodes.jsonl.gz"
            expected_file.write_bytes(b"invalid gzip payload")
            actual_file.write_bytes(gzip.compress(b'{}\n', mtime=0))

            self.assertEqual(
                [f"content differs: {expected_file}"],
                _compare_dirs(expected, actual),
            )

    def test_invalid_existing_archive_is_rewritten(self) -> None:
        records = [{"b": 2, "a": 1}]
        canonical = b'{"a": 1, "b": 2}\n'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nodes.jsonl.gz"
            path.write_bytes(b"invalid gzip payload")

            digest = write_jsonl_gzip(path, records)

            self.assertEqual(hashlib.sha256(canonical).hexdigest(), digest)
            self.assertEqual(canonical, gzip.decompress(path.read_bytes()))

    def test_plain_files_are_compared_by_content_not_shallow_stat(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            expected_file = expected / "manifest.json"
            actual_file = actual / "manifest.json"
            expected_file.write_text("alpha", encoding="utf-8")
            actual_file.write_text("omega", encoding="utf-8")
            timestamp = 1_700_000_000
            os.utime(expected_file, (timestamp, timestamp))
            os.utime(actual_file, (timestamp, timestamp))

            self.assertEqual(
                [f"content differs: {expected_file}"],
                _compare_dirs(expected, actual),
            )

    def test_graph_digest_uses_uncompressed_canonical_jsonl(self) -> None:
        records = [{"b": 2, "a": 1}]
        canonical = b'{"a": 1, "b": 2}\n'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nodes.jsonl.gz"
            digest = write_jsonl_gzip(path, records)

            self.assertEqual(hashlib.sha256(canonical).hexdigest(), digest)
            self.assertEqual(canonical, gzip.decompress(path.read_bytes()))


if __name__ == "__main__":
    unittest.main()
