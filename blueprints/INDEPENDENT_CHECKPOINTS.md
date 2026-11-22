# Blueprint: Independent Integrity Checkpoints

**Protocol proposal v0.1 — not implemented.**

## Goal
Allow separate operators to verify that a defined set of public evidence-record digests existed in a checkpointed batch, without claiming that the records are true or complete.

## Proposed checkpoint fields
- Protocol and schema version.
- Checkpoint identifier.
- Creation timestamp in UTC and stated clock source.
- Hash algorithm and canonicalization version.
- Merkle tree algorithm and leaf-ordering rule.
- Merkle root and leaf count.
- Previous checkpoint digest, if linked.
- Signer key identifier and public-key fingerprint.
- Signature over canonical checkpoint bytes.
- Optional independent witness statements.

## Verification requirements
A verifier must:
1. Validate schema and canonical serialization.
2. Recompute every included record digest.
3. Rebuild the Merkle tree using the specified leaf ordering and domain separation.
4. Verify inclusion proofs.
5. Verify signature against a trusted key binding supplied through an independently checked channel.
6. Check key validity, revocation, and rotation history.
7. Report missing data, clock uncertainty, and verification limits.

## Threats and controls
- **Key compromise:** publish revocation and replacement statements; do not rewrite old signatures.
- **Clock manipulation:** distinguish asserted timestamp from independently witnessed time.
- **Selective inclusion:** publish leaf count and inclusion proofs; never claim a checkpoint covers all records in existence.
- **Witness collusion:** require independently operated witnesses with disclosed relationships; signatures do not prove independence.
- **Canonicalization mismatch:** publish test vectors and version every canonicalization rule.
- **Privacy leakage:** checkpoint only safe digests and avoid revealing sensitive record identifiers or activity patterns.

## Release gates
Before implementation, publish cross-language test vectors, a key lifecycle policy, witness independence criteria, a verifier reference implementation, and adversarial tests for reordered leaves, altered digests, invalid proofs, expired keys, and compromised-key revocation.

## Non-goals
No blockchain requirement, token, proof of truth, proof of completeness, or public disclosure of confidential sources.
