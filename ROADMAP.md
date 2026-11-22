# Roadmap

This roadmap describes proposed work, not implemented capabilities.

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
- [ ] Merkle batch construction and proof verification.
- [ ] Signed checkpoint format and key rotation guidance.
- [ ] Independent witness protocol.
- [ ] Checkpoint transparency page or static feed.
- [ ] Reproducible test vectors.

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
