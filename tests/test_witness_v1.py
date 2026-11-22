import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator, FormatChecker

from ojek_ledger.cli import main
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
        altered_signature = copy.deepcopy(f["first_statement"])
        altered_signature["signature"] = "0" * 128
        result = verify_witness_statement(altered_signature, f["old_key_document"], f["old_tree_head"])
        self.assertFalse(result["valid"])
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

    def test_nested_witness_values_fail_closed_and_numeric_bounds_are_enforced(self):
        f = self.fixture
        nested = {"nested": [{"value": []}]}

        statement_cases = ["witness_id", "log_id", "tree_size", "root_hash", "observed_at",
                           "policy_id", "consistency_status", "signature"]
        for field in statement_cases:
            changed = copy.deepcopy(f["first_statement"])
            changed[field] = copy.deepcopy(nested)
            result = verify_witness_statement(changed, f["old_key_document"], f["old_tree_head"])
            self.assertFalse(result["valid"], field)
            self.assertTrue(result["errors"], field)

        changed_key = copy.deepcopy(f["old_key_document"])
        changed_key["public_key"] = copy.deepcopy(nested)
        result = verify_witness_statement(f["first_statement"], changed_key, f["old_tree_head"])
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])

        changed_head = copy.deepcopy(f["old_tree_head"])
        changed_head["tree_size"] = copy.deepcopy(nested)
        result = verify_witness_statement(f["first_statement"], f["old_key_document"], changed_head)
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])

        malformed_bundle = build_conflict_bundle([
            {"statement": nested, "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
            {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
        ])
        bundle_result = verify_conflict_bundle(malformed_bundle)
        self.assertFalse(bundle_result["valid"])
        self.assertTrue(bundle_result["errors"])

        for invalid_size in (-1, 1 << 53, True):
            changed = copy.deepcopy(f["first_statement"])
            changed["tree_size"] = invalid_size
            result = verify_witness_statement(changed, f["old_key_document"], f["old_tree_head"])
            self.assertFalse(result["valid"], repr(invalid_size))
            self.assertTrue(result["errors"], repr(invalid_size))

        for invalid_size in (-1, 1 << 53, True):
            changed = copy.deepcopy(f["second_statement"])
            changed["consistency_from_tree_size"] = invalid_size
            result = verify_witness_statement(
                changed, f["new_key_document"], f["new_tree_head"],
                f["first_statement"], f["old_key_document"], f["old_tree_head"],
                f["consistency_proof"], f["key_transition"],
            )
            self.assertFalse(result["valid"], repr(invalid_size))
            self.assertTrue(result["errors"], repr(invalid_size))

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
        bundle = build_conflict_bundle([
            {"statement": self.fixture["first_statement"], "key_document": self.fixture["old_key_document"], "tree_head": self.fixture["old_tree_head"]},
            {"statement": self.fixture["second_statement"], "key_document": self.fixture["new_key_document"], "tree_head": self.fixture["new_tree_head"], "previous_statement": self.fixture["first_statement"], "previous_key_document": self.fixture["old_key_document"], "previous_tree_head": self.fixture["old_tree_head"], "consistency_proof": self.fixture["consistency_proof"], "key_transition": self.fixture["key_transition"]},
        ])
        pairs.append(("witness-conflict-bundle.v0.1.schema.json", bundle))
        for filename, value in pairs:
            schema = json.loads((schema_dir / filename).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(value)), [], filename)
            invalid = copy.deepcopy(value)
            invalid["unrecognized_field"] = "reject"
            self.assertTrue(list(validator.iter_errors(invalid)), filename)

    def test_offline_witness_cli_verifies_first_and_rotated_statements(self):
        f = self.fixture
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = {
                "first.json": f["first_statement"],
                "first-key.json": f["old_key_document"],
                "old-head.json": f["old_tree_head"],
                "second.json": f["second_statement"],
                "second-key.json": f["new_key_document"],
                "new-head.json": f["new_tree_head"],
                "proof.json": f["consistency_proof"],
                "transition.json": f["key_transition"],
            }
            paths = {}
            for filename, value in artifacts.items():
                path = root / filename
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[filename] = str(path)

            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = main([
                    "witness", "verify", paths["first.json"], paths["first-key.json"], paths["old-head.json"],
                ])
            self.assertEqual(result, 0, output.getvalue())
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = main([
                    "witness", "verify", paths["second.json"], paths["second-key.json"], paths["new-head.json"],
                    "--previous-statement", paths["first.json"],
                    "--previous-key", paths["first-key.json"],
                    "--previous-tree-head", paths["old-head.json"],
                    "--consistency-proof", paths["proof.json"],
                    "--key-transition", paths["transition.json"],
                ])
            self.assertEqual(result, 0, output.getvalue())

            bundle = build_conflict_bundle([
                {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
                {"statement": f["second_statement"], "key_document": f["new_key_document"], "tree_head": f["new_tree_head"],
                 "previous_statement": f["first_statement"], "previous_key_document": f["old_key_document"],
                 "previous_tree_head": f["old_tree_head"], "consistency_proof": f["consistency_proof"],
                 "key_transition": f["key_transition"]},
            ])
            bundle_path = root / "bundle.json"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = main(["witness", "verify-bundle", str(bundle_path)])
            self.assertEqual(result, 0, output.getvalue())

    def test_runtime_verifier_rejects_unknown_fields_and_type_confusion(self):
        f = self.fixture

        unknown_statement = copy.deepcopy(f["first_statement"])
        unknown_statement["unrecognized_field"] = "reject"
        result = verify_witness_statement(
            unknown_statement, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

        boolean_tree_size = copy.deepcopy(f["first_statement"])
        boolean_tree_size["tree_size"] = True
        result = verify_witness_statement(
            boolean_tree_size, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

        unknown_key_field = copy.deepcopy(f["old_key_document"])
        unknown_key_field["unrecognized_field"] = "reject"
        self.assertFalse(verify_witness_key_document(unknown_key_field))

        mismatched_key_id = copy.deepcopy(f["old_key_document"])
        mismatched_key_id["key_id"] = "0" * 64
        self.assertFalse(verify_witness_key_document(mismatched_key_id))

        altered_tree_head = copy.deepcopy(f["old_tree_head"])
        altered_tree_head["root_hash"] = "0" * 64
        result = verify_witness_statement(
            f["first_statement"], f["old_key_document"], altered_tree_head
        )
        self.assertFalse(result["valid"])

    def test_conflict_bundle_rejects_malformed_observation_shape(self):
        f = self.fixture
        bundle = build_conflict_bundle([
            {
                "statement": f["first_statement"],
                "key_document": f["old_key_document"],
                "tree_head": f["old_tree_head"],
            },
            {
                "statement": f["first_statement"],
                "key_document": f["old_key_document"],
                "tree_head": f["old_tree_head"],
                "unexpected": "reject",
            },
        ])
        result = verify_conflict_bundle(bundle)
        self.assertFalse(result["valid"])
        self.assertFalse(result["conflict_detected"])
        self.assertTrue(result["errors"])

    def test_revoked_prior_key_invalidates_rotated_observation_chain(self):
        f = self.fixture
        result = verify_witness_statement(
            f["second_statement"], f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            f["consistency_proof"], f["key_transition"],
            revoked_key_ids={f["old_key_document"]["key_id"]},
        )
        self.assertFalse(result["valid"])
        self.assertFalse(result["continuity_verified"])

    def test_witness_and_log_identity_binding_fail_closed(self):
        f = self.fixture

        altered_witness = copy.deepcopy(f["first_statement"])
        altered_witness["witness_id"] = "witness:other-operator"
        result = verify_witness_statement(
            altered_witness, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

        altered_log = copy.deepcopy(f["first_statement"])
        altered_log["log_id"] = "another-log/main"
        result = verify_witness_statement(
            altered_log, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

        malformed_digest = copy.deepcopy(f["first_statement"])
        malformed_digest["root_hash"] = "z" * 64
        result = verify_witness_statement(
            malformed_digest, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

    def test_signature_with_wrong_domain_separator_is_rejected(self):
        from ojek_ledger.core import canonical_bytes

        f = self.fixture
        statement = copy.deepcopy(f["first_statement"])
        payload = {key: value for key, value in statement.items() if key != "signature"}
        statement["signature"] = self.old_private.sign(
            b"not-the-ojek-witness-domain" + canonical_bytes(payload)
        ).hex()
        result = verify_witness_statement(
            statement, f["old_key_document"], f["old_tree_head"]
        )
        self.assertFalse(result["valid"])

    def test_invalid_consistency_proof_encoding_is_rejected(self):
        from ojek_ledger import witness_v1
        from ojek_ledger.core import canonical_bytes

        f = self.fixture
        bad_proof = copy.deepcopy(f["consistency_proof"])
        bad_proof["proof"][0] = "not-a-lowercase-sha256-digest"
        statement = copy.deepcopy(f["second_statement"])
        statement["consistency_proof_digest"] = consistency_proof_digest(bad_proof)
        payload = {key: value for key, value in statement.items() if key != "signature"}
        statement["signature"] = self.new_private.sign(
            witness_v1._STATEMENT_DOMAIN + canonical_bytes(payload)
        ).hex()
        result = verify_witness_statement(
            statement, f["new_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            bad_proof, f["key_transition"],
        )
        self.assertFalse(result["valid"])

    def test_witness_cli_rejects_invalid_and_duplicate_member_json(self):
        f = self.fixture
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key_path = root / "key.json"
            head_path = root / "head.json"
            statement_path = root / "statement.json"
            key_path.write_text(json.dumps(f["old_key_document"]), encoding="utf-8")
            head_path.write_text(json.dumps(f["old_tree_head"]), encoding="utf-8")

            for raw in ('{"protocol":', '{"protocol":"a","protocol":"b"}'):
                statement_path.write_text(raw, encoding="utf-8")
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    result = main([
                        "witness", "verify", str(statement_path), str(key_path), str(head_path),
                    ])
                self.assertEqual(result, 2)
                self.assertIn("error:", output.getvalue())

    def test_witness_bundle_cli_exit_codes_distinguish_agreement_conflict_and_invalid(self):
        f = self.fixture
        agreeing_bundle = build_conflict_bundle([
            {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
            {"statement": f["second_statement"], "key_document": f["new_key_document"], "tree_head": f["new_tree_head"],
             "previous_statement": f["first_statement"], "previous_key_document": f["old_key_document"],
             "previous_tree_head": f["old_tree_head"], "consistency_proof": f["consistency_proof"],
             "key_transition": f["key_transition"]},
        ])

        fork_head = build_tree_head(
            f["old_tree_head"]["log_id"], [b"cli-exit-code-fork"],
            "2026-11-22T00:03:00Z",
        )
        other_private, other_key = generate_witness_keypair(
            "witness:cli-independent", "2026-11-22T00:00:00Z"
        )
        other_statement = sign_witness_statement(
            other_key, other_private, fork_head,
            "2026-11-22T00:03:05Z", "cli-independent-policy-v1",
        )
        conflict_bundle = build_conflict_bundle([
            {"statement": f["first_statement"], "key_document": f["old_key_document"], "tree_head": f["old_tree_head"]},
            {"statement": other_statement, "key_document": other_key, "tree_head": fork_head},
        ])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [
                (agreeing_bundle, 0),
                (conflict_bundle, 1),
                ({"protocol": "unsupported", "observations": []}, 2),
            ]
            for index, (bundle, expected_code) in enumerate(cases):
                path = root / f"bundle-{index}.json"
                path.write_text(json.dumps(bundle), encoding="utf-8")
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    result = main(["witness", "verify-bundle", str(path)])
                self.assertEqual(result, expected_code, output.getvalue())

    def test_witness_cli_input_limits_bound_bytes_depth_and_utf8(self):
        from ojek_ledger.cli import (
            MAX_WITNESS_ARTIFACT_BYTES, MAX_WITNESS_JSON_DEPTH, _read_witness_json,
        )

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "artifact.json"
            limit = MAX_WITNESS_ARTIFACT_BYTES["statement"]
            exact = "{}" + (" " * (limit - 2))
            path.write_bytes(exact.encode("utf-8"))
            self.assertEqual(_read_witness_json(path, "statement"), {})

            path.write_bytes((exact + " ").encode("utf-8"))
            with self.assertRaisesRegex(ValueError, "exceeds the CLI size limit"):
                _read_witness_json(path, "statement")

            nested = ("[" * MAX_WITNESS_JSON_DEPTH) + "0" + ("]" * MAX_WITNESS_JSON_DEPTH)
            path.write_text(nested, encoding="utf-8")
            value = _read_witness_json(path, "statement")
            for _ in range(MAX_WITNESS_JSON_DEPTH):
                self.assertIsInstance(value, list)
                value = value[0]
            self.assertEqual(value, 0)

            too_deep = "[" + nested + "]"
            path.write_text(too_deep, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON nesting exceeds the CLI limit"):
                _read_witness_json(path, "statement")

            # Brackets inside a JSON string are data, not nesting delimiters.
            path.write_text(json.dumps("[" * 256 + "{" * 256), encoding="utf-8")
            self.assertEqual(len(_read_witness_json(path, "statement")), 512)

            path.write_bytes(b"{\xff}")
            with self.assertRaisesRegex(ValueError, "must be UTF-8 JSON"):
                _read_witness_json(path, "statement")

    def test_witness_cli_oversized_artifact_returns_stable_error_code(self):
        from ojek_ledger.cli import MAX_WITNESS_ARTIFACT_BYTES

        f = self.fixture
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            statement_path = root / "statement.json"
            key_path = root / "key.json"
            head_path = root / "head.json"
            statement_path.write_bytes(b" " * (MAX_WITNESS_ARTIFACT_BYTES["statement"] + 1))
            key_path.write_text(json.dumps(f["old_key_document"]), encoding="utf-8")
            head_path.write_text(json.dumps(f["old_tree_head"]), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = main(["witness", "verify", str(statement_path), str(key_path), str(head_path)])
            self.assertEqual(result, 2)
            self.assertIn("exceeds the CLI size limit", output.getvalue())
            self.assertNotIn("Traceback", output.getvalue())

    def test_consistency_proof_node_limit_is_enforced_before_node_validation(self):
        from ojek_ledger.transparency_v2 import MAX_CONSISTENCY_PROOF_NODES, verify_consistency_proof_v2

        f = self.fixture
        proof = ["not-a-digest"] * (MAX_CONSISTENCY_PROOF_NODES + 1)
        self.assertFalse(verify_consistency_proof_v2(
            f["old_tree_head"]["tree_size"], f["new_tree_head"]["tree_size"],
            f["old_tree_head"]["root_hash"], f["new_tree_head"]["root_hash"], proof,
        ))

        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "transparency-consistency-proof.v0.2.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        oversized_document = copy.deepcopy(f["consistency_proof"])
        oversized_document["proof"] = ["0" * 64] * (MAX_CONSISTENCY_PROOF_NODES + 1)
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(oversized_document)))

    def test_unavailable_and_failed_proof_states_are_distinct(self):
        f = self.fixture
        unavailable = sign_witness_statement(
            f["old_key_document"], self.old_private, f["new_tree_head"],
            "2026-11-22T00:03:10Z", "baseline-v0.1",
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
        )
        self.assertEqual(unavailable["consistency_status"], "unavailable")
        result = verify_witness_statement(
            unavailable, f["old_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
        )
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(result["continuity_verified"])

        invalid_proof = copy.deepcopy(f["consistency_proof"])
        invalid_proof["new_root"] = "0" * 64
        failed = sign_witness_statement(
            f["old_key_document"], self.old_private, f["new_tree_head"],
            "2026-11-22T00:03:11Z", "baseline-v0.1",
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            invalid_proof,
        )
        self.assertEqual(failed["consistency_status"], "failed")
        result = verify_witness_statement(
            failed, f["old_key_document"], f["new_tree_head"],
            f["first_statement"], f["old_key_document"], f["old_tree_head"],
            invalid_proof,
        )
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(result["continuity_verified"])

    def test_conflict_bundle_observation_limit_is_enforced_by_builder_and_verifier(self):
        from ojek_ledger.witness_v1 import MAX_CONFLICT_BUNDLE_OBSERVATIONS, CONFLICT_PROTOCOL

        observations = [{} for _ in range(MAX_CONFLICT_BUNDLE_OBSERVATIONS + 1)]
        with self.assertRaisesRegex(ValueError, "exceeds the limit"):
            build_conflict_bundle(observations)

        oversized_bundle = {
            "protocol": CONFLICT_PROTOCOL,
            "observations": observations,
        }
        result = verify_conflict_bundle(oversized_bundle)
        self.assertFalse(result["valid"])
        self.assertFalse(result["conflict_detected"])
        self.assertIn("exceeds the limit", result["errors"][0])

    def test_conflict_bundle_accepts_exact_observation_limit_before_validation(self):
        from ojek_ledger.witness_v1 import MAX_CONFLICT_BUNDLE_OBSERVATIONS

        observations = [{} for _ in range(MAX_CONFLICT_BUNDLE_OBSERVATIONS)]
        bundle = build_conflict_bundle(observations)
        self.assertEqual(len(bundle["observations"]), MAX_CONFLICT_BUNDLE_OBSERVATIONS)
        result = verify_conflict_bundle(bundle)
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
