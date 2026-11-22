import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ojek_ledger.checkpoints import (
    CheckpointError,
    build_checkpoint,
    create_inclusion_proof,
    leaf_hash,
    merkle_root,
    verify_checkpoint,
    verify_inclusion_proof,
)


def record(record_id, digest_char="a"):
    return {"record_id": record_id, "integrity": {"digest": digest_char * 64}}


class CheckpointTests(unittest.TestCase):
    def test_deterministic_order(self):
        records = [record("b", "b"), record("a", "a")]
        first = build_checkpoint(records, "2026-01-01T00:00:00Z")
        second = build_checkpoint(list(reversed(records)), "2026-01-01T00:00:00Z")
        self.assertEqual(first, second)

    def test_empty_checkpoint(self):
        checkpoint = build_checkpoint([], "2026-01-01T00:00:00Z")
        self.assertTrue(verify_checkpoint(checkpoint)["valid"])
        self.assertEqual(checkpoint["leaf_count"], 0)

    def test_duplicate_record_ids_rejected(self):
        with self.assertRaises(CheckpointError):
            build_checkpoint([record("duplicate"), record("duplicate", "b")])

    def test_malformed_records_rejected_cleanly(self):
        for value in (None, "not-a-record", [], {"record_id": "x"}, {"record_id": "x", "integrity": None}):
            with self.subTest(value=value), self.assertRaises(CheckpointError):
                build_checkpoint([value])

    def test_digest_must_be_lowercase_sha256(self):
        for digest in ("bad", "g" * 64, "A" * 64, "a" * 63):
            with self.subTest(digest=digest), self.assertRaises(CheckpointError):
                build_checkpoint([{"record_id": "x", "integrity": {"digest": digest}}])

    def test_timestamp_and_previous_digest_validation(self):
        with self.assertRaises(CheckpointError):
            build_checkpoint([], "not-a-date")
        with self.assertRaises(CheckpointError):
            build_checkpoint([], "2026-01-01T00:00:00Z", "bad")

    def test_tampered_checkpoint_rejected(self):
        checkpoint = build_checkpoint([record("a"), record("b", "b")], "2026-01-01T00:00:00Z")
        checkpoint["leaves"][0]["record_digest"] = "c" * 64
        self.assertFalse(verify_checkpoint(checkpoint)["valid"])

    def test_malformed_checkpoint_does_not_raise_unexpected_errors(self):
        checkpoint = build_checkpoint([record("a")], "2026-01-01T00:00:00Z")
        for mutate in (
            lambda value: value.update(leaf_count=True),
            lambda value: value.update(leaves=[None]),
            lambda value: value.update(created_at="not-a-date"),
            lambda value: value.update(authentication=[]),
        ):
            damaged = copy.deepcopy(checkpoint)
            mutate(damaged)
            self.assertFalse(verify_checkpoint(damaged)["valid"])

    def test_proofs_for_odd_and_even_tree_sizes(self):
        for count in (1, 2, 3, 5, 8):
            checkpoint = build_checkpoint(
                [record(f"urn:test:{index}", format(index + 1, "x")) for index in range(count)],
                "2026-01-01T00:00:00Z",
            )
            for item in checkpoint["leaves"]:
                proof = create_inclusion_proof(checkpoint, item["record_id"])
                self.assertTrue(verify_inclusion_proof(
                    proof,
                    expected_root=checkpoint["merkle_root"],
                    expected_checkpoint_digest=checkpoint["checkpoint_digest"],
                ))
                altered_digest = copy.deepcopy(proof)
                altered_digest["record_digest"] = "f" * 64
                self.assertFalse(verify_inclusion_proof(altered_digest))
                altered_id = copy.deepcopy(proof)
                altered_id["record_id"] = "urn:test:forged"
                self.assertFalse(verify_inclusion_proof(altered_id))
                extra_path = copy.deepcopy(proof)
                extra_path["path"].append({"side": "right", "hash": "0" * 64})
                self.assertFalse(verify_inclusion_proof(extra_path))
                wrong_root = copy.deepcopy(proof)
                self.assertFalse(verify_inclusion_proof(wrong_root, expected_root="0" * 64))
                wrong_checkpoint = copy.deepcopy(proof)
                self.assertFalse(verify_inclusion_proof(wrong_checkpoint, expected_checkpoint_digest="0" * 64))

    def test_proof_verifier_rejects_malformed_values(self):
        for value in (None, [], "proof", {"format": "ojek-merkle-inclusion-proof", "protocol_version": "0.1.0"}):
            self.assertFalse(verify_inclusion_proof(value))

    def test_published_test_vectors(self):
        fixture_path = Path(__file__).resolve().parent / "fixtures" / "merkle-checkpoint-v0.1.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            leaves = [leaf_hash(item["record_id"], item["record_digest"]) for item in case["records"]]
            self.assertEqual(leaves, case["leaf_hashes"], case["name"])
            self.assertEqual(merkle_root(leaves), case["expected_root"], case["name"])

    def test_record_identity_is_bound_into_leaf(self):
        digest = "a" * 64
        self.assertNotEqual(leaf_hash("record:a", digest), leaf_hash("record:b", digest))

    def test_empty_root_is_stable(self):
        self.assertEqual(merkle_root([]), merkle_root([]))


if __name__ == "__main__":
    unittest.main()
