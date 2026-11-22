# Roadmap

This roadmap distinguishes implemented experimental capabilities from planned work. A checked item does not by itself mean production readiness; see the release checklist and protocol specifications.

## Phase 0 — Repository foundation
- [x] Establish project repository.
- [x] Publish architecture and ethical preservation principles.
- [x] Select initial license (Apache-2.0; review compatibility before adding dependencies).
- [x] Add contribution, security disclosure, code of conduct, and governance documents.
- [x] Define repository maturity and release policy.

## Phase 1 — Local evidence ledger
- [x] Versioned JSON Schema for source observations.
- [x] Add valid/invalid fixtures and automated JSON Schema validation in GitHub Actions.
- [x] Local-first CLI and portable filesystem storage (v0.1).
- [x] Append-only-by-application JSONL event log with hash chaining (v0.1).
- [x] Deterministic JSON evidence package export (v0.1).
- [x] Record digest and event-chain verification commands (v0.1).
- [x] Unit tests for creation, validation, export determinism, and tamper detection (v0.1).
- [ ] Signed checkpoints and independent witnesses (future phase; not implied by local hashes).

## Phase 2 — Daily integrity checkpoints
- [x] Deterministic Merkle batch construction and inclusion-proof verification (experimental unsigned v0.1; merged to `main`).
- [ ] Signed checkpoint format and key rotation guidance.
- [x] Experimental offline Ed25519 witness statements, public-key fingerprints, dual-signed key rotation, revocation-policy checks, and split-view conflict bundles (no hosted service or gossip; independent review pending).
- [ ] Checkpoint transparency page or static feed.
- [x] Frozen SHA-256 Python reference test vectors for empty, one-, two-, and three-leaf trees (v0.1).
- [x] Independent JavaScript verifier for canonicalization, leaf hashes, roots, and inclusion-proof vectors (Node.js 22; CI).
- [x] v0.2 Merkle consistency-proof generator and verifier, unsigned tree heads, offline CLI, strict JSON artifact parsing, frozen vectors, and independent JavaScript reference checks (initial implementation; external review and production release gates remain).

## Phase 3 — Federation
- [ ] Node identity and capability manifest.
- [ ] Signed manifests and opt-in replication.
- [ ] Explicit network allowlists, quotas, and rate limits.
- [ ] Offline synchronization and conflict handling.
- [ ] Node operator policy and abuse response.

## Phase 4 — Global language and access
- [ ] BCP 47 metadata and Unicode test suite.
- [ ] Translation provenance and review workflow.
- [ ] RTL and accessibility support.
- [ ] Low-bandwidth and offline interfaces.
- [ ] Community translation guidelines.

## Phase 5 — Journalism workflows
- [ ] Evidence notebook and source comparison.
- [ ] Public records change tracking.
- [ ] Citation and correction management.
- [ ] Exportable investigation packages.
- [ ] Editorial review and source-safety checks.

## Phase 6 — Rights and law atlas
- [ ] Separate repository and governance model.
- [ ] U.S. founding documents from authoritative sources.
- [ ] International human-rights instruments and treaty metadata.
- [ ] Jurisdiction-by-jurisdiction official legal-source registry.
- [ ] Version history, amendment and repeal tracking.
- [ ] Expert-reviewed translation links.

## Release gates
No phase is considered complete because documentation exists. Each release requires implementation evidence, tests against the exact commit, documented limitations, rights review, and security review. Public deployment and replication remain opt-in.


## Phase 7 — Global journalist materials and field validation
- [x] Draft global journalist field manual and core reporting templates (blueprint v0.1).
- [x] Draft AI-assisted research and editorial accountability policy.
- [x] Draft federated journalism network architecture and node roles.
- [x] Draft open-source research methodology and public-records request playbook.
- [x] Draft independent checkpoint and distributed public-information catalog blueprints.
- [x] Add a synthetic public-contract investigation exercise and regional adaptation kit.
- [ ] Obtain review from working journalists, editors, archivists, security practitioners, translators, and regional legal experts.
- [ ] Adapt materials with local partners in multiple legal systems and languages.
- [ ] Publish synthetic training exercises and reproducible example investigations.
- [ ] Convert approved protocol proposals into versioned schemas and test vectors.
- [ ] Run two independently operated pilot nodes before any general federation release.

## Field-validation rule
The new documents are drafts. A checkbox above records that a draft exists, not that the method has been validated in the field. Do not describe federation, secure source intake, signed checkpoints, or a global catalog as implemented until code, independent tests, operational review, and release gates are complete.
