# OJEK Two-Operator Witness Pilot

**Status:** pilot procedure; not a certification or production-readiness claim.

This procedure demonstrates how two separately administered operators can sign observations of the same OJEK v0.2 transparency tree head, exchange only public artifacts, and independently verify the resulting evidence bundle. It also defines a controlled split-view exercise.

The current reference implementation is offline. It does not provide witness discovery, network transport, a directory, automatic polling, or a quorum service.

## 1. Pilot objective

Demonstrate all of the following:

1. Operator A and Operator B independently obtain the same tree head.
2. Each operator verifies the tree head and, where applicable, its consistency proof from its own previously retained head.
3. Each operator signs its own observation using a separately controlled Ed25519 key.
4. Operators exchange public artifacts without exchanging private keys.
5. A third verifier validates both statements offline.
6. A controlled same-size/different-root test produces an explicit split-view conflict.

A successful exercise demonstrates protocol interoperability and the stated operational controls for this pilot. It does not prove that either operator is honest, that the log is complete, or that the source records are true.

## 2. Independence requirements

Two keys are not automatically two independent witnesses. Before the exercise, record the following for each operator:

- Responsible person or organization and a public contact route.
- Administrative control of the device and signing environment.
- Key custody and recovery process.
- Hosting and network provider, if applicable.
- Funding, ownership, and governance relationships relevant to independence.
- Observation policy identifier and software version.
- Date and method used to bind the operator identity to the public-key fingerprint.

For a meaningful pilot, A and B must not share private keys, signing accounts, administrators, or a single person with unilateral control of both signing environments. Prefer separate organizations, devices, credentials, and infrastructure. Document unavoidable dependencies rather than assuming independence.

Identity binding is out-of-band. A key fingerprint alone identifies a key, not an organization.

## 3. Preparation

Both operators independently install the same reviewed OJEK source revision and record its full commit hash and Python version.

Each operator obtains the exact same tree-head bytes through the agreed observation channel. Preserve the original bytes. Validate the tree head with the OJEK v0.2 verifier. For an existing log, retrieve the prior tree head and consistency proof independently; do not rely solely on artifacts supplied by the log operator.

Agree on:
- Exact `log_id`.
- Tree-head digest and tree size expected for the exercise.
- Observation-policy identifier.
- UTC observation-time recording convention.
- Artifact exchange method and receipt logging.
- Who will perform independent verification.

Do not include confidential source identities or private investigative details in witness artifacts.

## 4. Key creation and custody

The Python API currently exposes `generate_witness_keypair(witness_id, created_at)`. It returns private-key bytes and a public-key document.

Example, run separately by each operator in their own controlled environment:

```python
from ojek_ledger.witness_v1 import generate_witness_keypair

private_key_bytes, public_key_document = generate_witness_keypair(
    "witness:operator-a",
    "2026-11-22T18:00:00Z",
)
```

Operator B uses its own stable identifier, for example `witness:operator-b`, and creates its own key pair independently.

**Private-key handling:** the snippet is illustrative; do not save raw private-key bytes in a repository, shared folder, issue, notebook, or unencrypted artifact. Keep the key in memory for the signing operation or use an independently reviewed encrypted secret store / hardware-backed key custody integration. The current Python API accepts Ed25519 private-key bytes or an Ed25519 private-key object; a general-purpose secure key-store adapter is not yet provided. Backups, recovery, rotation, and revocation are operator responsibilities.

Exchange only the public-key document and confirm its fingerprint over an independent channel.

## 5. Sign an observation

Each operator signs the exact tree head it independently obtained. The following is the first-observation form:

```python
from ojek_ledger.witness_v1 import sign_witness_statement

statement = sign_witness_statement(
    public_key_document,
    private_key_bytes,
    tree_head,
    "2026-11-22T18:05:00Z",
    "two-operator-pilot-v1",
)
```

For subsequent observations, supply the operator's own prior signed statement, prior key document, prior tree head, and the v0.2 consistency proof. If a key changed, also supply the dual-signed key-transition artifact. A witness must not claim `verified` continuity unless the supplied proof validates. A missing proof is not a successful continuity check.

Retain the signed statement, public-key document, exact tree-head artifact, and any prior statement/proof/transition artifacts required to validate the chain.

## 6. Exchange and offline verification

Each operator sends the verifier:
- Signed witness statement.
- Public-key document.
- Exact tree head.
- Prior statement, prior key, prior tree head, consistency proof, and key transition where applicable.

Never send private-key material.

The verifier should obtain the expected public-key fingerprints through an out-of-band identity-binding process, then assemble a conflict bundle and verify it with the existing API:

```python
from ojek_ledger.witness_v1 import (
    build_conflict_bundle,
    verify_conflict_bundle,
)

bundle = build_conflict_bundle([
    {
        "statement": operator_a_statement,
        "key_document": operator_a_key_document,
        "tree_head": operator_a_tree_head,
    },
    {
        "statement": operator_b_statement,
        "key_document": operator_b_key_document,
        "tree_head": operator_b_tree_head,
    },
])

result = verify_conflict_bundle(bundle)
assert result["valid"], result["errors"]
assert not result["conflict_detected"], result["conflicts"]
```

For a normal agreement run, both observations should refer to the same log, tree size, and root. Preserve the bundle, verifier version, commit hash, verification output, and transfer receipt. A successful bundle check does not independently establish the operators' real-world identities; that remains the verifier's trust-policy responsibility.

The CLI can verify an exported bundle without network access:

```bash
ojek witness verify-bundle pilot-bundle.json
```

Exit code 0 means the bundle is valid and no supported conflict was detected. Exit code 1 means a conflict was detected (or a statement reported failed continuity). Exit code 2 means the bundle or its inputs were invalid.

## 7. Controlled split-view exercise

Use synthetic test data only. Do not inject a fork into a live production log.

1. Create two valid tree heads with the same `log_id` and `tree_size`, but different roots.
2. Have two separate test witness keys sign first-observation statements, one for each head.
3. Assemble both observations into one conflict bundle.
4. Run the offline verifier.
5. Confirm that `valid` is true for the signatures and artifact structures, while `conflict_detected` is also true with a `same-size-root-conflict` result.
6. Preserve the bundle and verifier output as a test record.

This is an important distinction: a conflict bundle can be cryptographically valid while proving that the observations disagree. Do not collapse "valid signatures" and "consistent history" into one boolean.

The reference tests include a synthetic independent-witness split-view case. The pilot team should additionally repeat the exercise using two separately administered environments and record the evidence.

## 8. Acceptance record

The pilot is complete only when the maintainers can publish a redacted record containing:

- OJEK commit hash and runtime versions.
- Operator identities or agreed public identifiers and their key fingerprints.
- Independence declaration and known shared dependencies.
- Tree-head digest, log ID, tree size, and observation dates.
- Artifact exchange method and receipt evidence.
- Offline verifier output for the agreement case.
- Offline verifier output for the controlled split-view case.
- Key-custody, recovery, and incident-response review.
- Deviations, failures, and unresolved risks.

Do not publish private keys, confidential source information, private contact details, or sensitive infrastructure data.

## 9. Known limitations and next gates

- There is no peer discovery, gossip protocol, automated exchange, or hosted witness directory.
- There is no automatic trusted timestamping; `observed_at` is a witness assertion.
- The verifier does not prove operator independence or real-world identity.
- Revocation is currently based on verifier-supplied policy; v0.1 does not define a universal signed revocation service.
- A pair of witnesses is not a universal quorum rule. Clients and communities must define their own risk-based policies.
- The reference API does not yet provide secure hardware-key integration or general secret-store adapters.
- Independent cryptographic review and a real two-operator field exercise remain release gates.

See [Witness Protocol v0.1](WITNESS_PROTOCOL_V0.1.md), [Independent Witness Architecture](INDEPENDENT_WITNESS_PROTOCOL.md), and the [Operator Runbook](OPERATOR_RUNBOOK.md).
