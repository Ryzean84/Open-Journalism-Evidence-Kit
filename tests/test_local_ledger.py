"""Integration tests for the local ledger CLI and storage format."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ojek_ledger.core import add_record, correct_record, export_package, init_workspace, record_notice, validate_workspace, verify_package, verify_workspace


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

    def test_correction_preserves_original_and_links_successor(self):
        original = self.add_sample()
        corrected = correct_record(
            self.workspace, original["record_id"], "Publisher corrected the title",
            {"title": "Corrected synthetic report"},
        )
        self.assertEqual(corrected["supersedes"], original["record_id"])
        self.assertEqual(corrected["source"]["title"], "Corrected synthetic report")
        original_path = self.workspace / "records" / (original["record_id"].removeprefix("urn:uuid:") + ".json")
        self.assertEqual(json.loads(original_path.read_text(encoding="utf-8"))["source"]["title"], "Synthetic test report")
        self.assertTrue(verify_workspace(self.workspace)["valid"])

    def test_dispute_notice_is_append_only(self):
        record = self.add_sample()
        event = record_notice(self.workspace, record["record_id"], "record.disputed", "Conflicting public evidence")
        self.assertEqual(event["event_type"], "record.disputed")
        self.assertTrue(verify_workspace(self.workspace)["valid"])

    def test_exported_package_can_be_verified_independently(self):
        self.add_sample()
        package_path = export_package(self.workspace, Path(self.temp.name) / "portable.json")
        result = verify_package(package_path)
        self.assertTrue(result["valid"], result["problems"])
        package = json.loads(package_path.read_text(encoding="utf-8"))
        package["records"][0]["source"]["title"] = "tampered"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        self.assertFalse(verify_package(package_path)["valid"])

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
