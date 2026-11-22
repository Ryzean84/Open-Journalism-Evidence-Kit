import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from ojek_ledger.cli import main
from ojek_ledger.transparency_v2 import (
    PROOF_PROTOCOL,
    TransparencyLogError,
    build_consistency_proof_document,
    build_log_entry,
    build_tree_head,\n    canonical_bytes,
    entry_bytes,
    generate_consistency_proof_v2,
    merkle_root_v2,
    strict_json_loads,
    validate_log_entry,
    verify_consistency_proof_document,
    verify_consistency_proof_v2,
    verify_tree_head,
)


FIXTURE = Path(__file__).parent / "fixtures" / "transparency-log-v0.2.json"


class TransparencyV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.entries = [item.encode("utf-8") for item in cls.fixture["entries"]]

    def test_canonical_entry_interoperability_vector(self):
        encoded = canonical_bytes(self.fixture["canonical_entry"])
        self.assertEqual(encoded.decode("utf-8"), self.fixture["canonical_entry_bytes"])
        from ojek_ledger.transparency_v2 import leaf_hash_v2
        self.assertEqual(leaf_hash_v2(encoded).hex(), self.fixture["canonical_entry_leaf_hash"])

    def test_frozen_roots(self):
        for vector in self.fixture["roots"]:
            size = vector["tree_size"]
            self.assertEqual(merkle_root_v2(self.entries[:size]), vector["root_hash"], size)

    def test_frozen_consistency_proofs(self):
        for case in self.fixture["consistency_cases"]:
            proof = generate_consistency_proof_v2(self.entries[:case["new_size"]], case["old_size"])
            self.assertEqual(proof, case["proof"])
            self.assertTrue(verify_consistency_proof_v2(
                case["old_size"], case["new_size"], case["old_root"], case["new_root"], proof
            ))

    def test_all_prefix_pairs_verify(self):
        entries = [f"property-entry-{i}".encode() for i in range(40)]
        roots = [merkle_root_v2(entries[:n]) for n in range(len(entries) + 1)]
        for old_size in range(len(entries) + 1):
            for new_size in range(old_size, len(entries) + 1):
                proof = generate_consistency_proof_v2(entries[:new_size], old_size)
                self.assertTrue(verify_consistency_proof_v2(
                    old_size, new_size, roots[old_size], roots[new_size], proof
                ), (old_size, new_size))
                self.assertFalse(verify_consistency_proof_v2(
                    old_size, new_size, "0" * 64, roots[new_size], proof
                ))

    def test_rejects_truncated_extra_reordered_and_malformed_proofs(self):
        for case in self.fixture["consistency_cases"]:
            m, n = case["old_size"], case["new_size"]
            proof = case["proof"]
            if proof:
                self.assertFalse(verify_consistency_proof_v2(m, n, case["old_root"], case["new_root"], proof[:-1]))
                self.assertFalse(verify_consistency_proof_v2(m, n, case["old_root"], case["new_root"], proof + ["0" * 64]))
                self.assertFalse(verify_consistency_proof_v2(m, n, case["old_root"], case["new_root"], ["z" * 64]))
                if len(proof) > 1:
                    self.assertFalse(verify_consistency_proof_v2(m, n, case["old_root"], case["new_root"], list(reversed(proof))))

    def test_empty_and_equal_size_semantics(self):
        empty = self.fixture["roots"][0]["root_hash"]
        one = self.fixture["roots"][1]["root_hash"]
        self.assertTrue(verify_consistency_proof_v2(0, 0, empty, empty, []))
        self.assertTrue(verify_consistency_proof_v2(0, 1, empty, one, []))
        self.assertFalse(verify_consistency_proof_v2(0, 1, "0" * 64, one, []))
        self.assertTrue(verify_consistency_proof_v2(1, 1, one, one, []))
        self.assertFalse(verify_consistency_proof_v2(1, 1, one, "0" * 64, []))
        self.assertFalse(verify_consistency_proof_v2(1, 1, one, one, ["0" * 64]))

    def test_rejects_invalid_sizes_and_types(self):
        root = self.fixture["roots"][1]["root_hash"]
        for m, n in ((True, 2), (1, True), (-1, 2), (3, 2), (1.0, 2)):
            self.assertFalse(verify_consistency_proof_v2(m, n, root, root, []))
        with self.assertRaises(TransparencyLogError):
            generate_consistency_proof_v2(self.entries, True)
        with self.assertRaises(TransparencyLogError):
            generate_consistency_proof_v2(self.entries, len(self.entries) + 1)

    def test_forked_history_is_rejected(self):
        old = self.entries[:4]
        fork = old[:3] + [b"attacker-substitution"]
        later = fork + [b"another-entry"]
        old_root = merkle_root_v2(old)
        fork_root = merkle_root_v2(later)
        honest_root = merkle_root_v2(self.entries[:5])
        self.assertNotEqual(fork_root, honest_root)
        proof = generate_consistency_proof_v2(later, len(old))
        self.assertFalse(verify_consistency_proof_v2(
            len(old), 5, old_root, honest_root, proof
        ))

    def test_entry_validation_and_canonical_bytes(self):
        entry = build_log_entry(
            "newsroom.example/log-1", 0, "record-reference", "a" * 64,
            "application/vnd.ojek.record-digest+json", "2026-11-22T00:00:00Z",
        )
        self.assertEqual(json.loads(entry_bytes(entry)), entry)
        validate_log_entry(entry, expected_log_id="newsroom.example/log-1", expected_index=0)
        invalid = copy.deepcopy(entry)
        invalid["extra"] = "not permitted"
        with self.assertRaises(TransparencyLogError):
            validate_log_entry(invalid)
        invalid = copy.deepcopy(entry)
        invalid["leaf_index"] = True
        with self.assertRaises(TransparencyLogError):
            validate_log_entry(invalid)
        invalid = copy.deepcopy(entry)
        invalid["created_at"] = "2026-11-22 00:00:00Z"
        with self.assertRaises(TransparencyLogError):
            validate_log_entry(invalid)

    def test_tree_head_digest_and_consistency_document_binding(self):
        old_entries = self.entries[:4]
        new_entries = self.entries[:9]
        old_head = build_tree_head("newsroom.example/log-1", old_entries, "2026-11-22T00:00:00Z")
        new_head = build_tree_head("newsroom.example/log-1", new_entries, "2026-11-22T00:01:00Z")
        self.assertTrue(verify_tree_head(old_head))
        self.assertTrue(verify_tree_head(new_head))
        invalid_empty = build_tree_head("newsroom.example/log-1", [], "2026-11-22T00:00:00Z")
        invalid_empty["root_hash"] = "0" * 64
        invalid_empty["tree_head_digest"] = "0" * 64
        self.assertFalse(verify_tree_head(invalid_empty))
        proof = generate_consistency_proof_v2(new_entries, 4)
        document = build_consistency_proof_document("newsroom.example/log-1", old_head, new_head, proof)
        self.assertEqual(document["protocol"], PROOF_PROTOCOL)
        self.assertTrue(verify_consistency_proof_document(old_head, new_head, document))
        altered = copy.deepcopy(document)
        altered["new_tree_size"] += 1
        self.assertFalse(verify_consistency_proof_document(old_head, new_head, altered))
        altered = copy.deepcopy(document)
        altered["old_tree_size"] = True
        self.assertFalse(verify_consistency_proof_document(old_head, new_head, altered))
        altered_head = copy.deepcopy(new_head)
        altered_head["root_hash"] = "0" * 64
        self.assertFalse(verify_tree_head(altered_head))
        self.assertFalse(verify_consistency_proof_document(old_head, altered_head, document))

    def test_tree_head_log_identity_must_match(self):
        head_a = build_tree_head("log-a", self.entries[:2], "2026-11-22T00:00:00Z")
        head_b = build_tree_head("log-b", self.entries[:3], "2026-11-22T00:01:00Z")
        self.assertFalse(verify_consistency_proof_document(head_a, head_b, {}))

    def test_cli_tree_head_proof_and_offline_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entries = []
            for index in range(5):
                entries.append(build_log_entry(
                    "newsroom.example/log-cli", index, "record-reference",
                    format(index + 1, "x") * 64,
                    "application/vnd.ojek.record-digest+json",
                    "2026-11-22T00:00:00Z",
                ))
            old_entries = root / "old-entries.json"
            all_entries = root / "all-entries.json"
            old_entries.write_text(json.dumps(entries[:2]), encoding="utf-8")
            all_entries.write_text(json.dumps(entries), encoding="utf-8")
            old_head = root / "old-head.json"
            new_head = root / "new-head.json"
            proof_file = root / "proof.json"

            def invoke(arguments):
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    result = main(arguments)
                return result, output.getvalue()

            result, output = invoke([
                "log-v2", "head", str(old_entries), "--log-id", "newsroom.example/log-cli",
                "--issued-at", "2026-11-22T00:00:00Z", "--output", str(old_head),
            ])
            self.assertEqual(result, 0, output)
            result, output = invoke([
                "log-v2", "head", str(all_entries), "--log-id", "newsroom.example/log-cli",
                "--issued-at", "2026-11-22T00:01:00Z", "--output", str(new_head),
            ])
            self.assertEqual(result, 0, output)
            result, output = invoke(["log-v2", "verify-head", str(new_head)])
            self.assertEqual(result, 0, output)
            result, output = invoke([
                "log-v2", "consistency-proof", str(all_entries), str(old_head),
                str(new_head), "--output", str(proof_file),
            ])
            self.assertEqual(result, 0, output)
            result, output = invoke([
                "log-v2", "verify-consistency", str(old_head), str(new_head), str(proof_file),
            ])
            self.assertEqual(result, 0, output)
            self.assertIn('"valid": true', output)

    def test_strict_json_rejects_duplicate_members_and_nonstandard_constants(self):
        with self.assertRaises(TransparencyLogError):
            strict_json_loads('{"tree_size":1,"tree_size":2}')
        with self.assertRaises(TransparencyLogError):
            strict_json_loads('{"root_hash":NaN}')
        self.assertEqual(strict_json_loads('{"a":1,"b":[true,null]}'), {"a": 1, "b": [True, None]})

    def test_published_v02_json_schemas(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        schemas = {
            "entry": json.loads((schema_dir / "transparency-log-entry.v0.2.schema.json").read_text(encoding="utf-8")),
            "head": json.loads((schema_dir / "transparency-tree-head.v0.2.schema.json").read_text(encoding="utf-8")),
            "proof": json.loads((schema_dir / "transparency-consistency-proof.v0.2.schema.json").read_text(encoding="utf-8")),
        }
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)
        entry = build_log_entry(
            "newsroom.example/schema", 0, "record-reference", "a" * 64,
            "application/vnd.ojek.record-digest+json", "2026-11-22T00:00:00Z",
        )
        entry_bytes_value = entry_bytes(entry)
        head = build_tree_head("newsroom.example/schema", [entry_bytes_value], "2026-11-22T00:01:00Z")
        empty_head = build_tree_head("newsroom.example/schema", [], "2026-11-22T00:00:00Z")
        proof = build_consistency_proof_document(
            "newsroom.example/schema", empty_head, head,
            generate_consistency_proof_v2([entry_bytes_value], 0),
        )
        for name, value in (("entry", entry), ("head", head), ("proof", proof)):
            validator = Draft202012Validator(schemas[name], format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(value)), [], name)
        invalid = copy.deepcopy(entry)
        invalid["unapproved"] = True
        validator = Draft202012Validator(schemas["entry"], format_checker=FormatChecker())
        self.assertTrue(list(validator.iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
