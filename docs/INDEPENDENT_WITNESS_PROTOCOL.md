# OJEK Independent Witness Protocol — Architecture Proposal

**Status: architecture and threat-model document.** The initial offline Ed25519 reference implementation is specified in [WITNESS_PROTOCOL_V0.1.md](WITNESS_PROTOCOL_V0.1.md). It depends on the v0.2 append-only transparency log and does not apply to v0.1 snapshot roots.

## 1. Principles

1. No mandatory central witness, blockchain, token, or global authority.
2. Witnesses are independently operated and publish their policies and public keys.
3. A witness statement records an observation and protocol check; it is not an endorsement of truth, legality, completeness, or quality.
4. Prior attestations are never silently rewritten.
5. Evidence must be verifiable offline using published rules and public keys.
6. Participation is opt-in and feasible for a small newsroom or archive.

## 2. Threat model

In scope: split view/equivocation (different heads shown to different clients), rollback, selective observation, witness key compromise, witness collusion/capture, availability attacks, and metadata privacy leakage.

Not guaranteed: truth or authenticity of source material, completeness of submissions, accurate wall-clock time absent a timestamp authority, availability, detection when all gossip paths are isolated, or protection when all witnesses collude.

## 3. Actors and independence

- Log operator: accepts ordered entries and publishes v0.2 tree heads and consistency proofs.
- Witness: independently retrieves a tree head, validates its structure and continuity against its prior observation, stores the result, and signs a statement.
- Client/verifier: validates tree heads, statements, keys, proofs, and local witness policy.
- Gossip peer: exchanges signed observations and conflict evidence.

Independence is operational, not a cryptographic fact. A public witness directory should disclose, where known and voluntarily provided, operator, organization, jurisdiction, hosting/provider, funding or control relationships, key fingerprints, contact, and incident policy. Counting keys is not equivalent to counting independent operators. Quorum policy belongs to clients, not a universal protocol constant.

## 4. Minimal witness statement (proposed)

Canonical JSON fields:

- protocol: exact string ojek-witness-statement-v0.1
- witness_id: stable witness identifier
- key_id: fingerprint identifying the signing public key
- log_id: observed log identifier
- tree_size: observed v0.2 tree size
- root_hash: observed v0.2 root hash
- tree_head_digest: digest of the exact observed tree head
- observed_at: RFC 3339 UTC witness wall-clock assertion, not trusted time
- previous_statement_digest: prior statement digest for this witness/log, or null
- consistency_status: verified, first_observation, failed, or unavailable
- consistency_from_tree_size: prior size used for verification, or null
- consistency_proof_digest: digest of proof artifact, or null
- policy_id: published witness policy identifier/version
- signature_algorithm: exact token ed25519
- signature: signature over the canonical statement preimage, excluding this field

Canonicalization, signature preimage, public-key encoding, and key fingerprint rules MUST be frozen with cross-language vectors before implementation. Unknown fields and algorithms MUST be rejected unless a future version explicitly defines them.

A witness may emit verified only after validating a v0.2 consistency proof from its stored prior head to the observed head. On first observation it emits first_observation; it cannot claim historical continuity it did not check. If proof retrieval or verification fails, it emits failed or unavailable, never verified.

## 5. Observation workflow

1. Retrieve a tree head from the log or receive one from a client.
2. Validate protocol identifier, log identity, tree-size bounds, root encoding, and tree-head digest.
3. If a prior observation exists, request and verify a consistency proof from the previous size to the new size.
4. A smaller tree size is a rollback signal. Same size with a different root is a conflict. A larger size without a valid proof is a continuity failure.
5. Store the exact head, proof artifact or digest, observation time, policy version, and result in a local append-only observation store.
6. Sign and publish the statement while retaining prior statements for export.
7. Periodically exchange statement digests with peers.

Witnesses SHOULD independently retrieve tree heads where practical rather than rely only on operator-supplied data. Push-only observations must be labeled as such.

## 6. Conflict evidence and split-view detection

An exportable conflict bundle contains the conflicting signed statements or tree heads, log identifier, sizes, roots, tree-head digests, available consistency proofs and results, public keys/key-status evidence, and collection/tool metadata.

A verifier can detect a same-size conflict when two validly signed observations for the same log identify different roots at the same tree size. It can detect continuity failure when a larger head cannot be proven to extend a previously observed smaller head.

A conflict bundle proves that supplied signed observations conflict under the protocol rules. It does not by itself identify the malicious party or explain the cause. Preserve both artifacts; never overwrite one with the other.

Gossip may use HTTPS, email attachments, repository releases, or offline media. Transport is untrusted; signatures and protocol verification provide integrity and signer authentication. Gossip improves detection probability but cannot guarantee detection across isolated networks.

## 7. Key lifecycle requirements

A separate key lifecycle specification is required before implementation:

- Generation: locally generated Ed25519 keys using a documented cryptographic library and secure randomness. Private keys remain under witness operator control.
- Identity binding: publish a key fingerprint and out-of-band identity-binding statement. A witness name alone is not a key identity.
- Rotation: old and new keys cross-sign a transition where possible; publish it through multiple channels and preserve old public keys.
- Revocation: publish a signed revocation with reason category and effective-time assertion. Historical statements remain intact; verifiers apply a documented policy to statements around the compromise window.
- Compromise: stop issuance under the compromised key, preserve evidence, publish revocation through independent channels, and require explicit recovery review.
- Recovery: perform out-of-band identity checks and bind a new key. Never silently replace a public key under the same fingerprint.
- Loss: a lost private key cannot be reconstructed. A new key may be established through recovery; identity continuity is a policy judgment.

This proposal does not define a universal root CA or treat trust-on-first-use as a sufficient identity system.

## 8. Privacy and operational controls

Witnesses should observe public tree heads and minimal metadata only. Do not submit confidential source identities, unpublished reporting, private communications, credentials, or sensitive investigative metadata to public witness services.

Publish retention, access, abuse-reporting, and incident-response policies. Apply request limits, bounded proof sizes, timeouts, caching, and explicit log allowlists. Do not automatically crawl arbitrary URLs supplied in log entries. Support offline verification and export. Disclose outages and observation gaps; absence of an attestation is not evidence of misconduct.

## 9. Client policy

Clients choose their own policy: minimum distinct operators, organizational/infrastructure diversity, observation recency, acceptable key status, required consistency verification, treatment of first observations, and handling of missing or conflicting witnesses.

A verifier reports raw observations separately from its policy decision. A quorum is not proof that underlying evidence is true.

## 10. Reference implementation\n\nThe experimental [Witness Protocol v0.1 specification](WITNESS_PROTOCOL_V0.1.md) freezes the Ed25519 signature preimages, key fingerprints, statement digest, dual-signed key transitions, revocation-policy input, and conflict-bundle semantics. The Python API and offline CLI verify supplied artifacts without network access. No hosted witness service, gossip transport, or peer discovery is implemented.\n\n## 11. Implementation gates

1. Freeze the v0.2 tree-head and consistency-proof format.
2. Freeze witness statement schema, canonicalization, signature preimage, and key fingerprint.
3. Publish Python and JavaScript vectors for valid, invalid, rotated, revoked, and conflicting statements.
4. Build an offline verifier before any hosted service.
5. Demonstrate split-view detection with two intentionally forked test logs.
6. Review privacy, key recovery, abuse resistance, and operational independence with external maintainers.
7. Pilot with at least two independently operated witnesses before describing federation as available.

This protocol is an accountability mechanism for log behavior, not a truth oracle, timestamp authority, or guarantee of source safety.
