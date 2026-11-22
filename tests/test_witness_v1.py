import copy
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator, FormatChecker

from ojek_ledger.transparency_v2 import build_tree_head
from ojek_ledger.witness_v1 import (
    build_conflict_bundle,
    build_key_transition,
    build_witness_key_document,
    consistency_proof_digest,
    generate_witness_keypair,
    sign_witness_statement,
    verify_conflict_bundle,
    verify_key_transition,
    verify_witness_key_document,
    verify_witness_statement,
    witness_statement_digest,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "witness-v0.1.json"


class WitnessV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.old_private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
        cls.new_private = Ed25519PrivateKey.from_private_bytes(bytes(range(32, 64)))

    def test_frozen_key_statement_transition_and_proof_vectors(self):
        f = self.fixture
        self.assertTrue(verify_witness_key_document(f["old_key_document"]))
        self.assertTrue(verify_witness_key_document(f["new_key_document"]))
        self.assertEqual(witness_statement_digest(f["first_statement"]), f["first_statement_digest"])
        self.assertEqual(consistency_proof_digest(f["consistency_proof"]), f["consistency_proof_digest"])
        self.assertTrue(verify_key_transition(
            f["key_transition"], f["old_key_document"], f["new_key_document"]
        ))
        first = verify_witness_statement(
            f["first_statement"], f["old_key_document"], f["old_tree_head"]
        )
        self.assertTrue(first["valid"], first["errors"])
        self.assertEqual(first["continuity_status"], "first_observation")
        second = verify_witness_statement(
            f["second_statement"], f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            f["consistency_proof"], f["key_transition"],
        )
        self.assertTrue(second["valid"], second["errors"])
        self.assertTrue(second["continuity_verified"])

    def test_builders_reproduce_frozen_signatures(self):
        f = self.fixture
        old_public = bytes.fromhex(f["old_key_document"]["public_key"])
        new_public = bytes.fromhex(f["new_key_document"]["public_key"])
        old_key = build_witness_key_document(
            f["old_key_document"]["witness_id"], old_public, f["old_key_document"]["created_at"]
        )
        new_key = build_witness_key_document(
            f["new_key_document"]["witness_id"], new_public, f["new_key_document"]["created_at"]
        )
        self.assertEqual(old_key, f["old_key_document"])
        self.assertEqual(new_key, f["new_key_document"])
        transition = build_key_transition(
            old_key, new_key, self.old_private, self.new_private, "2026-11-22T00:02:00Z"
        )
        self.assertEqual(transition, f["key_transition"])
        first = sign_witness_statement(
            old_key, self.old_private, f["old_tree_head"], "2026-11-22T00:01:05Z", "baseline-v0.1"
        )
        self.assertEqual(first, f["first_statement"])
        second = sign_witness_statement(
            new_key, self.new_private, f["new_tree_head"], "2026-11-22T00:03:05Z",
            "baseline-v0.1", first, old_key, f["old_tree_head"],
            f["consistency_proof"], transition,
        )
        self.assertEqual(second, f["second_statement"])

    def test_tampering_wrong_key_and_revocation_fail_closed(self):
        f = self.fixture
        altered = copy.deepcopy(f["second_statement"])
        altered["root_hash"] = "0" * 64
        result = verify_witness_statement(
            altered, f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            f["consistency_proof"], f["key_transition"],
        )
        self.assertFalse(result["valid"])
        result = verify_witness_statement(
            f["first_statement"], f["new_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])
        result = verify_witness_statement(
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            revoked_key_ids={f["old_key_document"]["key_id"]},
        )
        self.assertFalse(result["valid"])
        altered_transition = copy.deepcopy(f["key_transition"])
        altered_transition["new_key_signature"] = "0" * 128
        self.assertFalse(verify_key_transition(
            altered_transition, f["old_key_document"], f["new_key_document"]
        ))

    def test_verified_status_requires_exact_consistency_proof(self):
        f = self.fixture
        result = verify_witness_statement(
            f["second_statement"], f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            None, f["key_transition"],
        )
        self.assertFalse(result["valid"])
        altered_proof = copy.deepcopy(f["consistency_proof"])
        altered_proof["new_root"] = "0" * 64
        result = verify_witness_statement(
            f["second_statement"], f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            altered_proof, f["key_transition"],
        )
        self.assertFalse(result["valid"])

    def test_key_rotation_requires_dual_signed_transition(self):
        f = self.fixture
        with self.assertRaises(ValueError):
            sign_witness_statement(
                f["new_key_document"], self.new_private, f["new_tree_head"],
                "2026-11-22T00:03:05Z", "baseline-v0.1",
                f["first_statement"], f["old_key_document"], f["old_tree_head"],
                f["consistency_proof"], None,
            )

    def test_rollback_and_same_size_fork_are_reported(self):
        f = self.fixture
        fork_head = build_tree_head(
            f["old_tree_head"]["log_id"], [b"independent-fork"],
            "2026-11-22T00:02:00Z",
        )
        failed_statement = sign_witness_statement(
            f["old_key_document"], self.old_private, fork_head,
            "2026-11-22T00:02:05Z", "baseline-v0.1",
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
        )
        self.assertEqual(failed_statement["consistency_status"], "failed")
        verified = verify_witness_statement(
            failed_statement, f["old_key_document"], fork_head,
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
        )
        self.assertTrue(verified["valid"], verified["errors"])
        self.assertEqual(verified["continuity_status"], "failed")
        bundle = build_conflict_bundle([
            {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
            {"statement": failed_statement, "key_document": f["old_key_document"], "tree_head": fork_head,
             "previous_statement": f["first_statement"], "previous_key_document": f["old_key_document"],
             "previous_tree_head": f["old_tree_head"]},
        ])
        result = verify_conflict_bundle(bundle)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["conflict_detected"])
        self.assertIn("same-size-root-conflict", [item["type"] for item in result["conflicts"]])
        self.assertIn("witness-reported-continuity-failure", [item["type"] for item in result["conflicts"]])

    def test_independent_witness_same_size_split_view(self):
        f = self.fixture
        private, key_doc = generate_witness_keypair("witness:independent-archive", "2026-11-22T00:00:00Z")
        fork_head = build_tree_head(f["old_tree_head"]["log_id"], [b"another-fork"], "2026-11-22T00:01:00Z")
        statement = sign_witness_statement(
            key_doc, private, fork_head, "2026-11-22T00:01:05Z", "archive-policy-v1"
        )
        bundle = build_conflict_bundle([
            {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
            {"statement": statement, "key_document": key_doc, "tree_head": fork_head},
        ])
        result = verify_conflict_bundle(bundle)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["conflict_detected"])

    def test_witness_schemas_validate_frozen_artifacts(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        pairs = [
            ("witness-key.v0.1.schema.json", self.fixture["old_key_document"]),
            ("witness-statement.v0.1.schema.json", self.fixture["first_statement"]),
            ("witness-key-transition.v0.1.schema.json", self.fixture["key_transition"]),
        ]
        for filename, value in pairs:
            schema = json.loads((schema_dir / filename).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(value)), [], filename)
            invalid = copy.deepcopy(value)
            invalid["unrecognized_field"] = "reject"
            self.assertTrue(list(validator.iter_errors(invalid)), filename)


if __name__ == "__main__":
    unittest.main()
