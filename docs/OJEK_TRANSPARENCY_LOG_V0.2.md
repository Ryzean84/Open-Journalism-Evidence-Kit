# OJEK Append-Only Transparency Log v0.2 — Design Proposal

**Status: design proposal; not implemented or approved as a release.** This proposal does not change or reinterpret v0.1 checkpoints.

## 1. Why a new profile

OJEK v0.1 is a snapshot tree with project-specific hash prefixes and duplicate-last handling for odd-width levels. Its rules and vectors are frozen. They are not the RFC 6962 history-tree construction. A consistency-proof verifier for v0.2 MUST NOT accept a v0.1 root.

A snapshot manifest sorted anew at each checkpoint is not an append-only history: a later record could sort before an earlier record. v0.2 therefore defines a distinct ordered log sequence. Existing v0.1 checkpoints can be referenced by entries in that sequence.

## 2. Tree algorithm

The proposed v0.2 profile adopts the Merkle tree shape and consistency-proof construction in RFC 6962, Sections 2.1 and 2.1.2, with SHA-256. This is a compatibility choice; OJEK is not thereby a Certificate Transparency log.

Reference: [RFC 6962, Certificate Transparency](https://www.rfc-editor.org/rfc/rfc6962.html).

For ordered byte strings D[0..n-1]:

- Empty tree: MTH({}) = SHA-256(empty byte string).
- Leaf: MTH({d}) = SHA-256(0x00 || d).
- For n > 1, let k be the largest power of two strictly smaller than n. MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n])).
- Hashes are exactly 32 bytes, serialized as 64 lowercase hexadecimal characters.
- No duplicate-last padding is used. Tree shape is determined by the largest-power-of-two split.

The 0x00 and 0x01 prefixes provide leaf/node domain separation. Implementations MUST NOT substitute v0.1's prefixes or duplicate-last rule.

## 3. Ordered log entries

Each log has a stable unique log_id. Each accepted entry receives the next zero-based leaf_index; indices are contiguous and never reused. The log MUST preserve the accepted byte sequence and MUST NOT reorder, rewrite, or silently delete accepted entries.

Proposed v0.2 entry fields:

- protocol: exact string ojek-transparency-log-v0.2
- log_id: non-empty stable log identifier
- leaf_index: non-negative integer assigned by the log
- entry_type: registered lowercase token; initial values are record-reference, checkpoint-reference, and policy-change
- payload_digest: 64-character lowercase SHA-256 digest
- payload_media_type: non-empty media type
- created_at: RFC 3339 UTC timestamp asserted by the operator, not trusted time

The canonical UTF-8 bytes of this object under the existing project-specific ojek-json-v1 rules are the leaf input. A record-reference should normally commit to an existing OJEK record digest; a checkpoint-reference may commit to a v0.1 checkpoint digest. Payloads need not be copied into the public log. This keeps the log lightweight and avoids publishing source identities or private material.

Unknown fields and protocol identifiers MUST be rejected. Future extensions require a new version or an explicitly negotiated extension mechanism.

## 4. Tree head

A v0.2 tree head contains:

- protocol: ojek-transparency-log-v0.2
- log_id
- tree_size: number of accepted leaves; zero is permitted
- root_hash: 32-byte SHA-256 root as lowercase hex
- issued_at: RFC 3339 UTC operator assertion
- hash_algorithm: exact token sha-256

The initial design profile is unsigned. Anyone able to replace a tree head can produce another valid unsigned tree head. A future signed profile must define an explicit version, signature algorithm, key identity, and exact signature preimage; signatures must not be bolted onto this format ambiguously.

The tree-head digest preimage and final field names MUST be frozen with test vectors before implementation.

## 5. Consistency proof semantics

For old tree size m and new tree size n:

- Inputs MUST satisfy 0 <= m <= n.
- m == n is consistent only when old and new roots are identical; the proof is empty.
- m == 0 is valid only when the old root is exactly the defined empty-tree root.
- 0 < m < n uses the RFC 6962 PROOF/SUBPROOF construction.
- Proof nodes are ordered 32-byte hashes, serialized as lowercase hex.
- Verification MUST consume the entire proof and reject missing, extra, malformed, or non-32-byte nodes.
- Verification binds both sizes and both roots and fails if any are changed.

A valid proof demonstrates that the old tree is the first m leaves of the new tree under this algorithm. It does not establish completeness, truth, authenticity, lawful collection, accurate time, or that all observers saw the same head.

## 6. Implementation target

Proposed library API:

- merkle_root_v2(entries) -> root_hash
- generate_consistency_proof_v2(entries, old_size) -> proof
- verify_consistency_proof_v2(old_size, new_size, old_root, new_root, proof) -> bool

CLI command names and JSON argument shapes must be finalized consistently during implementation. No placeholder command should be shipped.

## 7. Required tests and interoperability

Freeze vectors covering:

- Empty-to-empty, empty-to-nonempty, and size-one-to-larger proofs.
- Equal sizes with equal roots and equal sizes with unequal roots.
- Sizes immediately below, at, and above powers of two.
- Odd sizes and multiple append batches.
- Old sizes 1, 2, 3, 4, 5, 7, 8, 9, 15, 16, and 17 against larger sizes.
- Changed old root, new root, old size, and new size.
- Truncated, extended, reordered, malformed, and non-hex proof nodes.
- Forked histories with equal sizes but different roots.
- Cross-language Python and JavaScript verification using the same fixture.

Tests MUST compare against independently generated RFC 6962-compatible vectors or a second implementation, not merely round-trip the same code. Property-based tests SHOULD generate append sequences and verify every earlier prefix against every later prefix.

## 8. Migration and compatibility

- v0.1 verification remains unchanged and supported.
- A v0.1 snapshot may be referenced by a v0.2 checkpoint-reference entry, but its root MUST NOT be treated as a v0.2 log root.
- Migration means appending explicit references to old checkpoint digests in a new v0.2 log; it does not preserve the old root.
- Consumers MUST dispatch by explicit protocol identifier and fail closed on unknown identifiers.

## 9. Threat model and release gate

Consistency proofs make it possible to detect a later root that cannot extend a previously observed prefix. They do not prevent an operator from maintaining two internally consistent forks and showing each to different clients. That requires independent witnesses and gossip.

The operator can omit eligible entries, delay publication, or publish misleading references. Public entries can expose investigative patterns. Store minimal digests and non-sensitive metadata only.

This proposal is not an implementation or security certification. Before implementation is accepted, maintainers must review the exact wire format, publish frozen vectors, validate against an independent implementation, and complete the tests above. Signing, key management, timestamp authorities, witnesses, and federation remain separate release gates.
