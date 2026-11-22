import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JournalistTemplateTests(unittest.TestCase):
    def test_source_register_has_required_columns_and_synthetic_example(self):
        with (ROOT / "templates" / "source-register.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            required = {
                "source_id", "canonical_url", "publisher_or_issuer",
                "source_type", "language_bcp47", "observed_at_utc",
                "rights_status", "limitations",
            }
            self.assertTrue(required.issubset(set(reader.fieldnames or [])))
            rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "S-001")
        self.assertEqual(rows[0]["rights_status"], "unknown")
        self.assertIn("example.org", rows[0]["canonical_url"])

    def test_claim_matrix_separates_claim_type_and_uncertainty(self):
        with (ROOT / "templates" / "claim-evidence-matrix.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            required = {
                "claim_id", "claim_text", "claim_type", "source_ids",
                "contradictory_evidence", "limitations",
                "confidence_language", "status",
            }
            self.assertTrue(required.issubset(set(reader.fieldnames or [])))
            rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["confidence_language"], "unverified lead")


if __name__ == "__main__":
    unittest.main()
