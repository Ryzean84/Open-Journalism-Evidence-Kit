# OJEK Witness Protocol v0.1 — Offline Verification Profile

**Status:** experimental reference implementation. This profile is unsigned only where explicitly stated; witness statements themselves are Ed25519-signed. It is not a production trust service.

## 1. Purpose and boundaries

A witness records an independently observed OJEK v0.2 tree head and signs a statement about that observation. A verifier can validate the public key, signature, tree-head binding, prior statement reference, and consistency proof without contacting the witness or log operator.

A valid witness statement proves only that the holder of a particular Ed25519 private key signed the specified observation. It does not prove that the key belongs to the claimed organization, that witnesses are operationally independent, that the log is complete, that a timestamp is trusted, or that source material is true.

No central directory, blockchain, token, network crawler, or hosted service is required.

## 2. Canonical encoding and cryptographic domains

All protocol objects use OJEK `ojek-json-v1` canonical UTF-8 JSON. Duplicate JSON members, non-standard constants, unknown fields, and unknown protocol identifiers MUST be rejected.

Domain-separated preimages:

- Key identifier: `SHA-256("OJEK-WITNESS-KEY-v0.1\0" || raw_public_key)`.
- Statement signature: `Ed25519.Sign(private_key, "OJEK-WITNESS-STATEMENT-v0.1\0" || canonical_json(statement_without_signature))`.
- Statement digest: `SHA-256("OJEK-WITNESS-STATEMENT-DIGEST-v0.1\0" || canonical_json(full_signed_statement))`.
- Key-transition signatures: `Ed25519.Sign(key, "OJEK-WITNESS-KEY-TRANSITION-v0.1\0" || canonical_json(transition_without_signatures))`.
- Key-transition digest: `SHA-256("OJEK-WITNESS-KEY-TRANSITION-v0.1\0" || canonical_json(full_transition))`.
- Consistency-proof digest: `SHA-256("OJEK-CONSISTENCY-PROOF-DIGEST-v0.2\0" || canonical_json(proof_document))`.

The null byte shown in each domain string is one byte, not the two printable characters backslash and zero. Hex digests are lowercase. Public keys are 32 raw bytes; signatures are 64 raw bytes. Witness tree sizes and prior sizes use interoperable JSON safe integers no greater than 9,007,199,254,740,991.

## 3. Public-key document

The exact key document fields are defined by [witness-key.v0.1.schema.json](../schemas/witness-key.v0.1.schema.json):

- `protocol`: `ojek-witness-key-v0.1`
- `witness_id`: stable operator-chosen identifier
- `key_id`: key fingerprint defined above
- `signature_algorithm`: `ed25519`
- `public_key`: 64 lowercase hex characters (32 raw bytes)
- `created_at`: UTC RFC 3339 assertion ending in `Z`

The key document is not self-authenticating. A verifier must obtain the binding between `witness_id` and `key_id` through an out-of-band channel or its own trust policy. A fingerprint identifies a key, not a person or organization.

## 4. Witness statement

The exact fields are defined by [witness-statement.v0.1.schema.json](../schemas/witness-statement.v0.1.schema.json). Conflict bundles use [witness-conflict-bundle.v0.1.schema.json](../schemas/witness-conflict-bundle.v0.1.schema.json). The signed statement binds:

- witness and key identifiers;
- `log_id`, `tree_size`, `root_hash`, and `tree_head_digest` from one valid v0.2 tree head;
- `observed_at`, an asserted UTC observation time;
- `previous_statement_digest`, the digest of the previous full signed statement for this witness/log, or null on first observation;
- `consistency_status`: `first_observation`, `verified`, `failed`, or `unavailable`;
- `consistency_from_tree_size`, the previous tree size or null on first observation;
- `consistency_proof_digest`, the digest of the supplied v0.2 proof document or null;
- `key_transition_digest`, the digest of a dual-signed key transition or null;
- `policy_id`, the witness's published observation-policy identifier;
- Ed25519 signature algorithm and signature.

A statement is `first_observation` only when all previous-chain fields are null. It MUST NOT imply historical continuity.

A statement is `verified` only when the verifier has the previous signed statement, its key document and tree head, and the exact consistency-proof document, and the proof validates from that previous head to the current head.

A statement is `failed` when a supplied proof does not validate, or when a rollback or same-size/different-root condition is directly observed. A failed statement is a valid signed report of a continuity failure, not a successful continuity attestation.

A statement is `unavailable` when the witness cannot obtain or validate the needed proof and no rollback or same-size root conflict has been established. Unavailable is not equivalent to verified.

## 5. Key rotation

A key transition document is defined by [witness-key-transition.v0.1.schema.json](../schemas/witness-key-transition.v0.1.schema.json). It identifies the same `witness_id`, previous `key_id`, new `key_id`, and asserted transition time. It carries two Ed25519 signatures over the same domain-separated canonical preimage: one from the previous key and one from the new key.

When a statement follows a statement signed by a different key, the verifier MUST require the transition document, validate both signatures, and compare its digest to `key_transition_digest` in the current statement. A transition does not independently establish real-world identity; the witness identity binding remains an out-of-band trust decision.

## 6. Revocation, compromise, and recovery

The offline verifier accepts a caller-supplied set of revoked key fingerprints. It rejects statements signed by a key in that set and rejects continuity chains that rely on a revoked previous key.

Revocation state is intentionally policy-supplied in v0.1; the protocol does not invent a global certificate authority. Operators should publish revocations through more than one independent channel. A verifier should retain the revocation source, retrieval time, and policy used. Because compromise may be discovered after historical statements were issued, policies must distinguish historical verification before a claimed compromise time from statements after it; a simple revoked-key set is a conservative full-key rejection mode.

After compromise, stop using the key, preserve all signed artifacts, publish the revocation, and establish a new key through an out-of-band identity check and a dual-signed transition where the old key is still trustworthy. If the old key is compromised or unavailable, recovery requires an independently authenticated administrative decision; cryptography alone cannot prove continuity of the human or organizational identity.

Private keys MUST NOT be included in repositories, public bundles, logs, or support requests. The library key generator returns private bytes in memory only. Callers are responsible for protected storage, access control, backup, and destruction.

## 7. Conflict bundles

A conflict bundle contains at least two observations. Each observation contains a signed statement, public-key document, and tree head, with optional previous statement/key/head, consistency proof, and key transition artifacts.

The offline checker validates each observation, then detects:

- **Same-size root conflict:** two valid signed observations for the same log and tree size contain different roots.
- **Witness-reported continuity failure:** a valid signed witness statement reports a failed consistency check or directly observed rollback/fork.

A conflict bundle establishes that the supplied signed observations conflict under this protocol. It does not identify which operator is malicious, establish motive, or prove source truth. Preserve all supplied artifacts unchanged.

## 8. CLI and library

Python API: `generate_witness_keypair`, `build_witness_key_document`, `sign_witness_statement`, `verify_witness_statement`, `build_key_transition`, and `verify_conflict_bundle`.

Offline CLI:

```bash
ojek witness verify statement.json witness-key.json tree-head.json
ojek witness verify statement.json witness-key.json tree-head.json \
  --previous-statement previous-statement.json \
  --previous-key previous-key.json \
  --previous-tree-head previous-tree-head.json \
  --consistency-proof consistency-proof.json \
  --key-transition key-transition.json

ojek witness verify-bundle conflict-bundle.json
```

The verifier makes no network requests. Exit code 0 means the signed observation is valid and no reported continuity failure was found; exit code 1 signals invalid verification or a continuity failure/conflict; exit code 2 signals an invalid conflict bundle or input error.

## 9. Limitations and release gates

- No hosted witness service, gossip transport, directory, trusted timestamp, or automatic peer discovery is implemented.
- Witness independence is operational and must be assessed by users.
- Revocation policy is supplied out of band.
- The v0.1 verifier checks supplied prior context; it does not fetch missing history.
- A successful signature proves key possession, not the truth or completeness of logged evidence.

Before production use, obtain independent cryptographic review, test key recovery and revocation procedures, and pilot with independently operated witnesses. This profile is experimental.
