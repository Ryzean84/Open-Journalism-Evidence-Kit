# Blueprint: Federated Journalism Network

**Architecture proposal v0.1 — not implemented.**

## Objective
Enable independent newsrooms, libraries, universities, community archives, and journalists to exchange verifiable public-interest evidence packages without depending on one central platform.

## Design commitments
- **Independent operation:** Each node controls storage, policy, retention, and availability.
- **Opt-in replication:** No record replicates by default. Each transfer declares purpose, rights basis, and recipient consent.
- **Portable formats:** JSON, JSONL, CSV, and documented schemas remain usable without a vendor.
- **Local-first:** Core collection and verification work offline.
- **No global identity registry:** Do not create a universal directory of journalists, sources, or subjects.
- **No trust by membership:** A signature authenticates a key's statement, not the truth of content.
- **Revocable participation:** Nodes can stop sharing and rotate keys. Previously copied material may not be retractable; disclose this clearly.
- **Safety before replication:** Sensitive, restricted, personal, or legally contested material is excluded from public replication unless a reviewed policy explicitly permits controlled transfer.

## Proposed node roles
| Role | Responsibility | Does not imply |
|---|---|---|
| Local researcher | Create and verify local packages | Editorial authority |
| Newsroom | Review, retain, publish selected material | Authority over other nodes |
| Library / archive | Preserve permitted records and metadata | Permission to republish copyrighted content |
| Witness | Independently countersign a checkpoint after review | Proof that a report is true |
| Translator | Produce linked, attributed translations | Replacement of original text |
| Public mirror | Serve approved public artifacts | Complete or canonical archive |

## Proposed exchange sequence
1. Sender creates a package manifest with schema versions, digests, rights labels, and data-minimization summary.
2. Sender signs the manifest with a locally controlled key.
3. Recipient verifies signature, digest, schema, and policy metadata before import.
4. Recipient applies local safety, rights, and retention review.
5. Recipient explicitly accepts, rejects, or quarantines the package.
6. If accepted, recipient records a receipt event and optional local checkpoint.
7. Corrections, disputes, withdrawals, and restrictions propagate as notices, never silent rewrites.
8. Nodes publish only the minimum public status needed to explain what they hold.

## Threat model to complete before implementation
- Compromised or stolen node keys.
- Malicious or negligent node operators.
- Poisoned packages and parser vulnerabilities.
- Replication of unlawful, copyrighted, or dangerous material.
- Metadata leakage revealing reporter interests or source relationships.
- Sybil nodes pretending to be independent witnesses.
- Selective omission, censorship, or inconsistent histories.
- Denial of service and storage exhaustion.
- False confidence caused by signatures or hash chains.

## Minimum protocol objects (proposal)
- **node-manifest:** software version, supported schemas, public contact channel, declared policies, signing-key fingerprints, expiry.
- **package-manifest:** package ID, creation time, schema versions, record digests, rights labels, sensitivity classification, sender key fingerprint.
- **receipt-event:** recipient node ID, package digest, receipt time, verification result, disposition.
- **checkpoint:** Merkle root, leaf count, tree algorithm, creation time, signing key ID, signature.
- **notice:** correction, dispute, withdrawal, restriction, or supersession reference.

## Release gates
Do not implement network listeners or automatic replication until a written threat model is reviewed; canonical serialization and signature test vectors exist; key generation, storage, rotation, revocation, and compromise recovery are documented; package import is sandboxed and resource-limited; rights and safety labels have local policy handling; two independent test nodes pass interoperability tests; and privacy review addresses traffic analysis and metadata leakage.

## Deliberately out of scope
No cryptocurrency, token, universal source identity, public source registry, central search monopoly, covert collection system, or automated credibility score.
