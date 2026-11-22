"""Integration tests for the local ledger CLI and storage format."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ojek_ledger.core import add_record, export_package, init_workspace, validate_workspace, verify_workspace


class LocalLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / "ledger"
        init_workspace(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def add_sample(self):
        return add_record(self.workspace, {
            "url": "https://example.org/report",
            "title": "Synthetic test report",
            "publisher": "Example",
            "language": "en",
            "method": "manual",
            "rights_status": "link_only",
        })

    def test_add_validate_verify(self):
        record = self.add_sample()
        self.assertTrue(record["record_id"].startswith("urn:uuid:"))
        count, problems = validate_workspace(self.workspace)
        self.assertEqual(count, 1)
        self.assertEqual(problems, [])
        result = verify_workspace(self.workspace)
        self.assertTrue(result["valid"], result["problems"])
        self.assertEqual(result["event_count"], 1)

    def test_export_is_deterministic(self):
        self.add_sample()
        first = export_package(self.workspace, Path(self.temp.name) / "one.json").read_bytes()
        second = export_package(self.workspace, Path(self.temp.name) / "two.json").read_bytes()
        self.assertEqual(first, second)
        package = json.loads(first)
        self.assertEqual(package["format"], "ojek-evidence-package")
        self.assertEqual(len(package["records"]), 1)

    def test_tampered_record_is_detected(self):
        record = self.add_sample()
        path = self.workspace / "records" / (record["record_id"].removeprefix("urn:uuid:") + ".json")
        changed = json.loads(path.read_text(encoding="utf-8"))
        changed["source"]["title"] = "Altered after recording"
        path.write_text(json.dumps(changed), encoding="utf-8")
        result = verify_workspace(self.workspace)
        self.assertFalse(result["valid"])
        self.assertTrue(any("record digest mismatch" in problem for problem in result["problems"]))

    def test_tampered_event_is_detected(self):
        self.add_sample()
        event_path = self.workspace / "events.jsonl"
        event = json.loads(event_path.read_text(encoding="utf-8"))
        event["event_type"] = "record.modified"
        event_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        result = verify_workspace(self.workspace)
        self.assertFalse(result["valid"])
        self.assertTrue(any("event hash mismatch" in problem for problem in result["problems"]))


if __name__ == "__main__":
    unittest.main()
