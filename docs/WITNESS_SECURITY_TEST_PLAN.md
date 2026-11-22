# Witness Verifier Security Test Plan

**Status:** engineering test plan; not a security certification or independent audit.

This plan defines adversarial test coverage for the experimental offline Ed25519 witness verifier. Its purpose is to make failure behavior explicit before any network exchange or federation work is designed.

## 1. Security properties under test

The verifier should:

1. Bind every signed statement to one exact public-key document and one exact v0.2 tree head.
2. Reject malformed, altered, unknown-field, or unsupported protocol artifacts.
3. Distinguish an invalid signature/artifact from a validly signed report of failed continuity.
4. Verify linked observations, consistency proofs, and dual-signed key transitions without silently upgrading missing evidence.
5. Detect supported same-log, same-size, different-root conflicts across independently valid observations.
6. Apply caller-supplied key revocation policy consistently.
7. Fail closed at both library and CLI boundaries without exposing private key material.

These properties do not establish real-world identity, independent administration, trusted time, log completeness, source authenticity, or factual truth.

## 2. Adversarial test matrix

| Area | Input or attack | Expected behavior |
|---|---|---|
| Statement integrity | Alter signature, root, tree-head digest, witness ID, key ID, log ID, or signed policy field | Reject statement |
| Key binding | Public-key bytes do not match key ID | Reject key document |
| Identity binding | Statement witness ID or key ID differs from key document | Reject statement |
| Tree-head binding | Statement log ID, size, root, or digest differs from supplied head | Reject statement |
| Unknown fields | Add unrecognized top-level fields to protocol artifacts | Reject according to strict schema/runtime validation |
| Type confusion | Boolean supplied where integer is expected | Reject |
| Numeric bounds | Negative or greater-than-safe-integer tree size | Reject |
| Nested values | Replace protocol scalar fields with arrays/objects or malformed nested observation members | Return an invalid result without an uncaught exception |
| Digest encoding | Uppercase, short, non-hex, or malformed digest | Reject |
| Cross-language negative vectors | Tampered witness/key/log bindings, altered tree heads, wrong signature domain, malformed proof nodes, invalid numeric bounds | Independent JavaScript reference rejects the same negative cases as Python |
| Signature encoding | Wrong length, uppercase, or non-hex signature | Reject |
| First observation | Include previous-chain fields or prior artifacts | Reject |
| Continuity | Omit required prior statement, key, or tree head | Reject |
| Prior chain | Previous statement belongs to another witness or log | Reject |
| Proof binding | Proof digest differs from signed statement digest | Reject |
| Proof validity | Invalid proof labeled `verified` | Reject |
| Proof status | Valid proof labeled `failed` | Reject as inconsistent report |
| Missing proof | Missing proof represented as `unavailable` without rollback/fork | Accept statement but report continuity unverified |
| Rollback | Smaller tree size without valid continuity | Report failed continuity; do not treat as verified |
| Split view | Same log and size with different valid roots | Detect conflict |
| Key rotation | Missing or invalid old/new dual signature | Reject transition |
| Rotation timing | Transition outside linked observation interval | Reject |
| Key rollback | Attempt a transition from a newer key document back to an older key document | Reject because transition time must fall within the old-to-new key creation interval |
| Rotation boundaries | Transition time before old-key creation or after new-key creation | Reject; timestamps within the permitted interval validate |
| Conflicting revocation policy | Conflict bundle includes an observation signed by a caller-revoked key | Mark the bundle invalid and do not report a conflict using invalid evidence |
| Revocation | Statement signed by key in caller's revoked-key set | Reject |
| Bundle structure | Missing required observation fields or extra fields | Reject bundle observation |
| Mixed bundle | One valid and one invalid observation | Bundle invalid; do not present it as a clean conflict proof |
| Duplicate evidence | Repeat the same signed witness statement in a bundle | Reject the replayed duplicate; do not count it as an additional observation |
| Resource exhaustion | More than 128 observations in a conflict bundle | Reject before per-observation verification or pairwise comparison; maximum pair comparisons are 8,128 |
| Resource exhaustion | Witness CLI artifact exceeds its per-type byte cap or JSON nesting exceeds 64 containers | Reject before JSON parsing; CLI returns exit code 2 |
| Resource exhaustion | Conflict bundle exceeds 4 MiB or 128 observations | Reject before per-observation verification or pairwise comparison |
| CLI boundary | Missing file, malformed JSON, invalid artifact, inaccessible path | Stable nonzero exit and useful error; no traceback leakage of secrets |
| CLI error contract | Invalid signature, key, tree head, missing continuity context, proof, transition, or revoked key | Return semantic-invalid exit code 1 with structured result; malformed/unreadable input returns exit code 2 |
| Secret handling | Inspect public key documents, conflict bundles, and witness CLI output for raw/hex/base64 private-key bytes | No private key material is serialized or emitted; the CLI accepts public verification artifacts only |
| Secret handling | Search CLI output, logs, bundles, and test artifacts for private key bytes | No private key material emitted or serialized |

## 3. Witness CLI input limits

The offline witness CLI applies operational input limits before parsing. These are local resource-protection limits, not changes to the signed artifact formats, protocol identifiers, or published JSON Schemas. Library callers that bypass the CLI remain responsible for bounding their own input sources.

| Artifact | Maximum serialized file size |
|---|---:|
| Current or previous witness statement | 64 KiB |
| Consistency proof | 64 KiB |
| Key document (current or previous) | 16 KiB |
| Tree head (current or previous) | 16 KiB |
| Key transition | 16 KiB |
| Conflict bundle | 4 MiB |

All witness CLI JSON artifacts are limited to 64 nested arrays/objects. The reader consumes at most the configured limit plus one byte, rejects over-limit input before decoding, requires UTF-8, checks nesting while respecting quoted strings and escapes, then invokes the duplicate-member-rejecting strict JSON parser. These limits are initial CLI defaults and should be revisited against real-world artifact samples before any production deployment; they do not imply a production security certification.

## 4. Required test layers

### A. Unit tests
Exercise every validation branch in `witness_v1.py`, including malformed types, field mismatches, invalid signatures, proof-state transitions, key rotation, and revocation.

### B. Schema tests
Validate all frozen valid artifacts against their JSON Schemas. Mutate each artifact with unknown fields, missing required fields, invalid types, and boundary values. Confirm runtime validation and schema validation agree where the protocol requires them to.

### C. Cross-language vectors
Keep Python and Node.js implementations aligned on canonicalization, digest preimages, signature verification, key transitions, and conflict classification. The JavaScript witness reference exercises negative witness/key/log bindings, altered tree heads, wrong signature domain, malformed signatures/proofs, and invalid numeric/proof-size bounds. Continue adding negative cases where the reference implementation covers the same protocol behavior; do not imply full witness-protocol parity where it does not.

### D. CLI integration tests
Exercise `ojek witness verify` and `ojek witness verify-bundle` with valid, invalid, missing, malformed, and adversarial files. Verify exit codes and output behavior. Semantic-invalid artifacts return exit code 1 with structured invalid results; malformed or unreadable input returns exit code 2 with a bounded error message.

### E. Secret-handling tests
Confirm the CLI accepts public verification artifacts only and that raw, hexadecimal, and base64 encodings of test private keys never appear in public key documents, conflict bundles, or CLI output.

### F. Resource-limit tests
Set explicit limits only after measuring realistic artifacts and documenting the compatibility implications. Candidate limits include maximum bundle observations, serialized artifact bytes, JSON nesting depth, and proof-node counts. Do not introduce arbitrary limits into a published protocol version without a versioning decision.

## 5. Result classification

Tests and documentation must preserve these distinct outcomes:

- **Invalid evidence:** signature, schema, key binding, tree-head binding, or required proof validation failed.
- **Valid observation, continuity verified:** signature and exact consistency proof validate against the supplied prior observation.
- **Valid observation, continuity unavailable:** the witness did not supply a proof; this is not proof of continuity.
- **Valid observation, continuity failed:** the witness signed a failed continuity result, such as a rollback or invalid proof.
- **Valid conflict evidence:** individual observations verify, while their authenticated tree heads demonstrate a supported conflict.

Do not reduce these states to a single generic "verified" flag.

## 6. Release gates

Before describing the witness verifier as production-ready:

- [ ] Every applicable matrix row has an automated test or a documented reason it cannot be automated.
- [ ] Resource limits are measured, specified, and enforced.
- [ ] Cross-language positive and negative vectors agree.
- [ ] CLI error behavior is stable and tested.
- [ ] A reviewer independent of the implementation author reviews cryptographic and protocol behavior.
- [ ] Known residual risks and unsupported guarantees are published.
- [ ] The two-operator pilot in [TWO_OPERATOR_WITNESS_PILOT.md](TWO_OPERATOR_WITNESS_PILOT.md) is completed and evidence is recorded.

Passing this plan's automated tests is necessary but not sufficient for a security assurance claim.

## 7. Scope exclusions

This plan does not authorize or specify:
- Peer discovery, gossip, or automated network transport.
- A global witness quorum or universal trust policy.
- Trusted timestamping.
- A universal signed revocation service.
- Secure hardware-key integration.
- Source-intake or journalist-safety certification.

Those require separate designs, explicit threat models, and independent review.
