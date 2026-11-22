import copy
import json
import unittest
from pathlib import Path

from ojek_ledger.transparency_v2 import (
    PROOF_PROTOCOL,
    TransparencyLogError,
    build_consistency_proof_document,
    build_log_entry,
    build_tree_head,
    entry_bytes,
    generate_consistency_proof_v2,
    merkle_root_v2,
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
        invalid["created_at"] = "2026-11-22T00:00:00-07:00"
        with self.assertRaises(TransparencyLogError):
            validate_log_entry(invalid)

    def test_tree_head_digest_and_consistency_document_binding(self):
        old_entries = self.entries[:4]
        new_entries = self.entries[:9]
        old_head = build_tree_head("newsroom.example/log-1", old_entries, "2026-11-22T00:00:00Z")
        new_head = build_tree_head("newsroom.example/log-1", new_entries, "2026-11-22T00:01:00Z")
        self.assertTrue(verify_tree_head(old_head))
        self.assertTrue(verify_tree_head(new_head))
        proof = generate_consistency_proof_v2(new_entries, 4)
        document = build_consistency_proof_document("newsroom.example/log-1", old_head, new_head, proof)
        self.assertEqual(document["protocol"], PROOF_PROTOCOL)
        self.assertTrue(verify_consistency_proof_document(old_head, new_head, document))
        altered = copy.deepcopy(document)
        altered["new_tree_size"] += 1
        self.assertFalse(verify_consistency_proof_document(old_head, new_head, altered))
        altered_head = copy.deepcopy(new_head)
        altered_head["root_hash"] = "0" * 64
        self.assertFalse(verify_tree_head(altered_head))
        self.assertFalse(verify_consistency_proof_document(old_head, altered_head, document))

    def test_tree_head_log_identity_must_match(self):
        head_a = build_tree_head("log-a", self.entries[:2], "2026-11-22T00:00:00Z")
        head_b = build_tree_head("log-b", self.entries[:3], "2026-11-22T00:01:00Z")
        self.assertFalse(verify_consistency_proof_document(head_a, head_b, {}))


if __name__ == "__main__":
    unittest.main()
