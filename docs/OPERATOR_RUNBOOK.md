# Operator Runbook

**Audience:** journalists, researchers, archivists, and maintainers operating a local OJEK workspace or validating exported artifacts.

OJEK is an early-stage metadata and integrity toolkit. This runbook is not a security certification, legal advice, or a guarantee of source or operator safety.

## 1. Before recording information

- Use OJEK for public-source metadata and non-sensitive evidence references.
- Do not enter confidential source identities, private communications, credentials, unpublished tips, or precise personal-risk details.
- Do not assume a public URL grants permission to copy or republish its contents.
- Keep original source files in an appropriate, access-controlled system; OJEK does not provide secure source intake or encryption.
- Record uncertainty and distinguish direct observation from inference, translation, and editorial judgment.

## 2. Workspace protection

- Store the workspace on a device and account with appropriate access controls.
- Use full-disk encryption and operating-system updates where appropriate; OJEK does not implement either.
- Keep at least one separate backup of important work. For high-value material, maintain more than one backup and periodically test restoration.
- Do not place workspaces, exports, or source notes in public repositories or shared folders by default.
- Avoid syncing sensitive workspaces to third-party services unless their data handling and access controls have been reviewed.

## 3. Routine integrity checks

From the repository root or installed environment:

```bash
ojek --workspace ./my-ledger verify
```

The executable is `ojek` (without spaces):

```bash
ojek --workspace ./my-ledger verify
ojek --workspace ./my-ledger validate
```

Create a v0.1 snapshot checkpoint only after the local ledger verifies:

```bash
ojek --workspace ./my-ledger checkpoint create --output exports/checkpoint.json
ojek --workspace ./my-ledger checkpoint verify ./my-ledger/exports/checkpoint.json
```

v0.1 checkpoints are unsigned snapshots. Their digest detects changes relative to a supplied file; it does not prevent replacement by someone who controls the file.

## 4. v0.2 transparency artifacts

The v0.2 commands operate on an ordered JSON array of validated log entries. The `import-ledger` command first verifies a local v0.1 workspace and emits one digest reference per event in its existing event order. It exports event hashes, the node identifier, sequence indexes, and operator-asserted event times—not source titles, URLs, article content, or confidential source identities. It does not publish a log or provide an external timestamp.

```bash
ojek --workspace ./my-ledger log-v2 import-ledger --output entries.json
ojek log-v2 head entries.json --log-id newsroom.example/main --issued-at 2026-11-22T00:00:00Z --output tree-head.json
ojek log-v2 verify-head tree-head.json
ojek log-v2 consistency-proof entries.json old-head.json new-head.json --output consistency-proof.json
ojek log-v2 verify-consistency old-head.json new-head.json consistency-proof.json
```

Tree heads are unsigned operator assertions. Their digest provides deterministic integrity checking, not signer authentication or trusted time. A consistency proof establishes prefix extension under the v0.2 tree algorithm, not completeness or truth.

## 5. Independent verification and transfer

When receiving an evidence package or transparency artifact:

1. Preserve the received bytes unchanged and record the transfer context separately.
2. Verify the package or artifact using a trusted, independently obtained copy of the verifier.
3. Keep the original artifact, verifier version, verification output, and any errors.
4. Obtain prior tree heads and consistency proofs through an independent channel when available.
5. Do not treat an artifact's own digest as proof that the artifact came from the claimed operator.
6. Do not treat a successful inclusion or consistency proof as proof that the source material is accurate.

## 6. Witness verification

Witness statements and conflict bundles can be checked offline. The verifier uses supplied public-key documents and caller-supplied revocation policy; it makes no network requests.

```bash
ojek witness verify statement.json witness-key.json tree-head.json
ojek witness verify statement.json witness-key.json tree-head.json --previous-statement previous-statement.json --previous-key previous-key.json --previous-tree-head previous-tree-head.json --consistency-proof consistency-proof.json --key-transition key-transition.json
ojek witness verify-bundle conflict-bundle.json
```

Exit code 1 signals an invalid statement or reported continuity failure/conflict. Exit code 2 signals an invalid conflict bundle or input error. A successful signature establishes key possession, not real-world identity or witness independence. See the [witness protocol specification](WITNESS_PROTOCOL_V0.1.md) and [two-operator pilot procedure](TWO_OPERATOR_WITNESS_PILOT.md) for independent key custody, artifact exchange, and split-view exercises.

## 7. Incident response

If a digest, event chain, tree head, or proof fails verification:

- Stop relying on the affected artifact as verified.
- Preserve the original bytes and error output; do not overwrite or repair the only copy.
- Make a separate working copy for investigation.
- Compare against independently held backups and previously observed checkpoints.
- Record who supplied each copy, when it was received, and the verification software used.
- If a suspected vulnerability affects OJEK, use the private reporting route in `SECURITY.md`; do not publish sensitive source material in an issue.

If a person or source may be at risk, prioritize their safety and follow the newsroom's established incident and source-protection procedures. OJEK is not an emergency response system.

## 7. Retention and deletion

Cryptographic logs and public exports can preserve sensitive metadata indefinitely. Do not place personal or confidential details in immutable or publicly replicated records. A restriction notice in the v0.1 ledger is not access control and does not erase prior copies. Establish a separate retention and deletion policy appropriate to the jurisdiction and material before deployment.

## 8. Production readiness

Do not describe an OJEK deployment as production-secure or suitable for high-risk source intake. Before operational deployment, obtain independent security review, define key management and incident response, test backup restoration, review local law and rights, and assess the specific threat model.
