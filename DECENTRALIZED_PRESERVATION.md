# Decentralized Public-Information Preservation

## Concept
Preserve a verifiable record of public information becoming available, changing, being corrected, or disappearing—without claiming ownership of the original reporting and without requiring a blockchain.

The system should remember the public record, not become a second publisher that republishes everything it encounters.

## A practical alternative to a blockchain
Start with well-understood components:
- Append-only event log: each observation creates a new event.
- Content hashing: compute a digest for content or permitted evidence packages.
- Hash chaining: link each event to the previous event in a local sequence.
- Merkle trees: summarize large batches so individual records can be verified efficiently.
- Digital signatures: nodes sign checkpoints and replication statements using managed keys.
- Independent witnesses: multiple operators retain and attest to checkpoints.
- Content-addressed storage: optional storage of objects by digest, subject to rights, privacy, and retention policy.

These components provide useful integrity and audit properties without mining, tokens, or global transaction consensus.

## Daily preservation cycle
1. A node discovers an eligible public source through a documented connector or manual submission.
2. It records the canonical URL, source identity, title, language, publication time if supplied, retrieval time, and collection method.
3. It records rights and access conditions. Unknown rights are treated conservatively.
4. It computes a digest over the exact bytes or normalized evidence object and records which representation was hashed.
5. It appends an observation event; it never silently edits a prior event.
6. At a defined interval, it creates a Merkle batch root and signs a checkpoint.
7. Independent nodes may retrieve and verify the checkpoint and selectively mirror eligible objects.
8. Later changes, corrections, takedowns, and broken links are new events linked to the earlier observation.

## What is preserved
Default preservation package:
- Source URL and publisher metadata
- Title, byline, dates and language where available
- Retrieval timestamp and method
- Rights/permission status and terms reference
- Cryptographic digest and representation description
- HTTP status and selected non-sensitive response metadata
- Permitted short quotation or abstract where lawful
- Correction, version, and availability observations
- Signed checkpoint and witness references

Full article bodies, photographs, video, audio, paywalled material, personal data, and leaked material are not copied by default. Full-text replication requires a documented rights basis, publisher permission, public-domain status, or another reviewed legal basis.

## Daily roots are not daily truth
A daily checkpoint can show that a particular record was included in a batch by a certain checkpoint. It cannot establish that the article was true, that the source was authentic, that the node collected every relevant item, that a publisher did not alter the source before collection, that all independent witnesses are honest, or that a translation is accurate.

The user interface must explain this distinction whenever it presents an integrity proof.

## Federation and resilience
Nodes should be independently operated by newsrooms, universities, libraries, civil-society organizations, and volunteers. They can subscribe to signed manifests, mirror selected metadata and permitted objects, verify event and checkpoint signatures, compare local history with peers, operate offline and synchronize later, and publish their own retention, moderation, and replication policies.

No node is required to accept every other node's data. Trust relationships are explicit and revocable.

## Privacy, removal, and contested material
Immutability must not become a mechanism for permanently exposing victims, minors, vulnerable sources, private individuals, or unlawfully disclosed material.

The system distinguishes immutable evidence that an event occurred; mutable access controls and availability of a stored object; a correction or restriction event explaining a change; and retention/deletion obligations.

Do not put sensitive source identities, private correspondence, credentials, or raw personal data into public immutable logs. A public digest can itself be sensitive if it enables confirmation or correlation of private material. Review before publication.

Where material must be removed, nodes can stop serving the object and record a minimal, privacy-preserving tombstone or restriction event where appropriate. The system must not promise that all replicas can be recalled.

## Threats to test
- A malicious node submits fabricated metadata.
- A compromised signing key creates false checkpoints.
- A node withholds inconvenient records.
- A publisher changes content before the first observation.
- Two nodes collude to claim independent witnessing.
- Hashes are computed over inconsistent representations.
- Replication exposes personal or copyrighted material.
- An attacker floods feeds or causes resource exhaustion.
- A malicious connector redirects requests or exfiltrates credentials.

Mitigations include independent key management, signed manifests, source provenance, rate limits, strict network allowlists, reproducible canonicalization, transparent node policies, and human review.
