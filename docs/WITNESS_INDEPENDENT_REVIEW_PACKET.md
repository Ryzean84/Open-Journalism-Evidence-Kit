# OJEK Independent Witness Review and Pilot Packet

**Status:** review preparation material. This is not an independent review, audit, certification, or production-readiness claim.

This packet is intended to let an external cryptographic/protocol reviewer and two prospective witness operators assess the current offline reference implementation without needing to reconstruct the project history.

## 1. Review objective

Review whether the experimental OJEK v0.2 transparency log and v0.1 Ed25519 witness artifacts are internally consistent, unambiguous, safely rejected when malformed, and suitable for a controlled two-operator field exercise.

The target is a transport-neutral, local-first protocol. The implementation does not require a central witness service, blockchain, token, global authority, hosted directory, peer discovery, or automated gossip.

## 2. Current implementation boundary

Implemented and tested:

- Ordered v0.2 transparency log entries, tree heads, inclusion/consistency proof support, and explicit protocol-version separation from v0.1 snapshots.
- Offline Ed25519 witness public-key documents and signed observation statements.
- Dual-signed key transitions with forward key-creation chronology.
- Caller-supplied revoked-key policy.
- Offline conflict bundles, duplicate-statement replay rejection, and same-size/different-root conflict detection.
- Strict JSON parsing, duplicate-member rejection, CLI input byte/depth limits, bounded proof nodes, and bounded conflict-bundle observations.
- Python tests across Python 3.10–3.13 and a Node.js cryptographic reference with positive and negative vectors.

Not implemented or guaranteed:

- Real-world witness identity or organizational independence.
- Trusted timestamps or accurate wall-clock time.
- Log completeness, source authenticity, factual truth, or lawful collection.
- A universal signed revocation service, quorum policy, or trust directory.
- Peer discovery, automated transport/gossip, or a hosted witness service.
- Secure hardware-key integration or a general secret-store adapter.
- Resistance to collusion by all witnesses or detection across fully isolated networks.

The witness CLI applies file byte/depth limits before parsing. Callers that bypass the CLI and invoke library functions directly remain responsible for bounding their input sources.

## 3. Primary review materials

Review these files at one recorded commit:

| Area | File |
|---|---|
| Architecture and threat model | `docs/INDEPENDENT_WITNESS_PROTOCOL.md` |
| Frozen witness wire format and signature rules | `docs/WITNESS_PROTOCOL_V0.1.md` |
| v0.2 append-only log format | `docs/OJEK_TRANSPARENCY_LOG_V0.2.md` |
| Python witness implementation | `src/ojek_ledger/witness_v1.py` |
| Python transparency implementation | `src/ojek_ledger/transparency_v2.py` |
| CLI parsing and exit behavior | `src/ojek_ledger/cli.py` |
| Adversarial/security test matrix | `docs/WITNESS_SECURITY_TEST_PLAN.md` |
| Python witness tests | `tests/test_witness_v1.py` |
| Python transparency tests | `tests/test_transparency_v2.py` |
| Node.js witness reference | `tests/reference/verify_witness_v1_vectors.js` |
| Two-operator procedure | `docs/TWO_OPERATOR_WITNESS_PILOT.md` |

Reviewers should record the exact Git commit SHA they reviewed. Do not rely on a branch name alone.

## 4. Reproduction and test commands

From a clean checkout:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -e .

python -m unittest discover -s tests -p 'test_transparency_v2.py' -v
python -m unittest discover -s tests -p 'test_witness_v1.py' -v

node tests/reference/verify_witness_v1_vectors.js
node tests/reference/verify_transparency_v2_vectors.js
```

The repository CI workflow also runs the full validation matrix on Python 3.10, 3.11, 3.12, and 3.13, plus CodeQL for Python and GitHub Actions.

## 5. Reviewer checklist

### A. Cryptographic construction

- [ ] Confirm the Ed25519 statement preimage is exact, canonical, and domain-separated.
- [ ] Confirm key fingerprint derivation binds the intended public-key bytes and witness identity rules.
- [ ] Confirm key-transition signatures cover the same exact transition payload under both old and new keys.
- [ ] Confirm invalid, truncated, malformed, or wrong-domain signatures fail closed.
- [ ] Confirm no private-key bytes enter public artifacts, CLI output, or logs.

### B. Transparency log and proof semantics

- [ ] Confirm v0.1 snapshot roots cannot be mistaken for v0.2 append-only roots.
- [ ] Confirm RFC 9162-style tree construction and consistency proof behavior against independent vectors.
- [ ] Confirm old/new sizes and roots are bound and safe-integer limits are consistent across Python and JavaScript.
- [ ] Confirm the 64-node proof ceiling safely covers the declared supported tree-size range.
- [ ] Confirm malformed, missing, extra, reordered, and non-hex proof nodes fail closed.

### C. Witness state and key lifecycle

- [ ] Confirm first observations cannot imply historical continuity.
- [ ] Confirm a witness cannot label missing or invalid continuity evidence as verified.
- [ ] Confirm rollback, same-size root conflict, and key rollback are distinguished correctly.
- [ ] Confirm transition-time boundaries and key creation chronology are enforced.
- [ ] Confirm caller-supplied revocation policy is applied consistently to every observation in a bundle.
- [ ] Confirm the format does not imply that a key fingerprint proves real-world identity or operator independence.

### D. Conflict evidence and resource limits

- [ ] Confirm invalid observations cannot be used to produce a valid conflict finding.
- [ ] Confirm exact duplicate signed statements are rejected as replayed evidence.
- [ ] Confirm same-log/same-size/different-root observations are classified as supported conflict evidence.
- [ ] Confirm bundle observation and proof-node caps are enforced before expensive processing.
- [ ] Confirm witness CLI byte and JSON-depth limits are applied before parsing.
- [ ] Confirm library callers are clearly told that CLI file limits do not automatically bound direct API inputs.

### E. Privacy and operations

- [ ] Confirm witness artifacts contain only public keys, signed statements, tree heads, proofs, and necessary metadata.
- [ ] Review metadata leakage, retention, availability, abuse resistance, and incident-response assumptions.
- [ ] Review the key custody, rotation, revocation, loss, and recovery procedures.
- [ ] Confirm manual exchange can be performed without transferring private keys or confidential source material.

## 6. Findings format

For each finding, record:

- Finding ID and title.
- Severity: critical, high, medium, low, or informational.
- Exact commit SHA and affected file/line or protocol section.
- Preconditions and threat assumptions.
- Reproduction steps or proof-of-concept.
- Expected behavior and observed behavior.
- Recommended remediation.
- Whether the finding blocks the two-operator pilot or only a later release gate.

Do not silently change protocol semantics during review. Propose changes with compatibility and versioning implications.

## 7. Two-operator pilot entry criteria

Do not start the field exercise until the following are true:

- [ ] An external reviewer has completed the cryptographic/protocol review or explicitly documented a limited-scope review.
- [ ] Two operators are independently controlled, with no shared private keys, signing accounts, administrators, or single-person unilateral control.
- [ ] Each operator has generated and retained its own key locally.
- [ ] Public-key fingerprints are bound to operator identities through an out-of-band process.
- [ ] Both operators have independently obtained the same exact tree head and recorded its digest.
- [ ] Both operators have run the offline verification workflow.
- [ ] A synthetic same-size/different-root split-view exercise has been run and preserved.
- [ ] Key custody, revocation, recovery, and known shared dependencies are recorded.

Follow `docs/TWO_OPERATOR_WITNESS_PILOT.md` for the actual procedure. Use synthetic data for the fork exercise; do not inject a fork into a live production log.

## 8. Pilot evidence record

Publish only a redacted record containing:

- OJEK commit SHA and runtime versions.
- Reviewer scope, date, and findings status.
- Operator identifiers or agreed public names and key fingerprints.
- Independence declaration and known shared dependencies.
- Tree-head digest, log ID, tree size, and observation dates.
- Artifact exchange method and receipt evidence.
- Offline agreement verification result.
- Synthetic split-view verification result.
- Key-custody/recovery review status.
- Deviations, failures, and unresolved risks.

Never publish private keys, confidential source identities, private contact details, or sensitive infrastructure details.

## 9. Release gate

The offline reference implementation may continue to be developed and tested, but the project must not claim a deployed independent witness network, federation, trusted timestamping, or production security assurance until the relevant external review and operational pilot gates are completed.

A successful pilot demonstrates only that the participating operators and verifier performed the documented exercise. It does not prove that the log is complete, the operators are honest, or the underlying evidence is true.
