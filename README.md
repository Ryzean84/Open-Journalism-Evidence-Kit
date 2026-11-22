# Open Journalism Evidence Kit

**A decentralized, multilingual, local-first toolkit for preserving the public record and supporting independent journalism worldwide.**

The project is designed for journalists, researchers, libraries, universities, civil-society groups, and independent contributors. It aims to make public-interest research more accessible, verifiable, reproducible, and resilient—without requiring a central platform or a cryptocurrency.

## What we are building

- **Evidence provenance:** record where public information came from, when it was observed, how it was collected, and what has changed.
- **Decentralized preservation:** independent nodes can retain and verify permitted records and daily integrity checkpoints.
- **Global language access:** preserve originals and provide clearly labeled, reviewable translations.
- **Rights and law research:** build a source-linked atlas of constitutional documents, founding texts, laws, protections, and international instruments.
- **Journalism workflows:** compare sources, track corrections, create evidence packages, and document uncertainty.

## Foundational design documents

- [Global Decentralized Journalism Ecosystem](GLOBAL_JOURNALISM_ECOSYSTEM.md) — ecosystem map, repository boundaries, upstream projects, participation tracks, and build sequence.
- [Contributing](CONTRIBUTING.md) — participation paths for journalists, communities, archivists, translators, researchers, developers, and reviewers.
- [Governance](GOVERNANCE.md) — decision-making, maintainer roles, conflicts of interest, and release policy.
- [Code of Conduct](CODE_OF_CONDUCT.md) — community expectations and reporting process.
- [Security Policy](SECURITY.md) — private vulnerability reporting and deployment cautions.

- [Architecture](ARCHITECTURE.md)
- [Protocol Versioning and Compatibility](docs/PROTOCOL_VERSIONING.md)
- [Operator Runbook](docs/OPERATOR_RUNBOOK.md)
- [Protocol Schema Catalog](docs/SCHEMA_CATALOG.md)
- [Release Readiness Checklist](docs/RELEASE_CHECKLIST.md)
- [Changelog](CHANGELOG.md)
- [Decentralized Public-Information Preservation](DECENTRALIZED_PRESERVATION.md)
- [Global Rights and Law Atlas proposal](GLOBAL_RIGHTS_AND_LAW_ATLAS.md)
- [Language and Accessibility Strategy](LANGUAGE_AND_ACCESSIBILITY.md)
- [Rights, Copyright, and Ethical Preservation](RIGHTS_COPYRIGHT_AND_ETHICS.md)
- [Roadmap](ROADMAP.md)

## Try the local evidence ledger

The first runnable component is available as an early v0.1 command-line tool. It creates a local metadata ledger, validates source observations, records a hash-chained event history, exports portable JSON packages, and verifies local integrity.

See the [Local Ledger guide](docs/LOCAL_LEDGER.md) for installation, quick-start commands, storage layout, and limitations. The separate [v0.2 transparency log guide](docs/OJEK_TRANSPARENCY_LOG_V0.2.md) documents ordered log entries, tree heads, consistency proofs, and CLI usage. The experimental [Merkle Checkpoints v0.1 guide](docs/MERKLE_CHECKPOINTS.md) documents checkpoint creation, verification, inclusion proofs, and their trust limitations. This tool does not scrape pages, copy article content, provide secure source intake, or establish the truth of a source.

## The preservation model

We are studying useful ideas from distributed systems and cryptography—append-only event logs, content hashes, hash chains, Merkle trees, signed checkpoints, independent witnesses, and optional content-addressed storage.

We are not assuming that a blockchain is necessary. We are not building a token or financial system. The objective is a lightweight, independently verifiable public record.

A daily integrity checkpoint can help establish that a record was included by a particular checkpoint. It does **not** prove that a news report is true, that a source is authentic, or that a node has captured everything.

## Global by design

No single country, language, legal system, publisher, or political viewpoint defines this project. The United States founding documents and constitutional protections are important parts of the collection, alongside other nations' constitutional and legal traditions and international and regional human-rights instruments.

Original texts remain distinguishable from translations, summaries, commentary, and AI-generated analysis. Jurisdiction, effective dates, amendment history, source authority, and translation status must be visible.

## Rights and source protection

We do not automatically copy or republish full news articles. The default is to preserve source references, factual metadata, retrieval records, rights information, and integrity digests. Full-content storage requires a documented rights basis. Sensitive source identities and private investigative material do not belong in public immutable logs.

## Current maturity

The local metadata ledger is implemented as an early v0.1 tool. The unsigned Merkle checkpoint and inclusion-proof prototype (v0.1) is experimental. A separate v0.2 append-only transparency-log implementation now provides RFC 9162-style Merkle roots, consistency-proof generation and verification, unsigned tree heads, and offline CLI verification. v0.1 snapshot rules remain unchanged. Both formats are unsigned and unwitnessed; they do not establish trusted time, completeness, source authenticity, or truth. Independent witnesses, signed tree heads, trusted timestamps, federation, translation infrastructure, and the legal atlas remain future work. See the [Merkle Checkpoints guide](docs/MERKLE_CHECKPOINTS.md) and [Roadmap](ROADMAP.md) for implementation gates.

## Relationship to Huffman Systems / Open Intelligence Fabric

This project is intended to interoperate with the [Open Intelligence Fabric](https://github.com/Ryzean84/Open-Intelligence-Fabric) standards and governance work and the [OIF Research Observatory](https://github.com/Ryzean84/OIF-Research-Observatory). It should remain useful as an independent tool even without those systems.

## Participation

We welcome contributions from journalists, archivists, librarians, translators, researchers, software developers, legal scholars, and communities worldwide. Participation should be open, documented, respectful, and safe for contributors and sources.

Before implementation or deployment, read the rights, ethics, and security guidance. This project is not legal advice and cannot guarantee personal safety.


## Global journalist field manual and reusable materials

The repository now includes a draft field manual and practical templates intended for adaptation by local newsrooms and independent journalists worldwide:

- [Global Journalist Field Manual](GLOBAL_JOURNALIST_FIELD_MANUAL.md)
- [Investigation brief](templates/investigation-brief.md)
- [Source register CSV](templates/source-register.csv)
- [Claim-evidence matrix CSV](templates/claim-evidence-matrix.csv)
- [Verification log](templates/verification-log.md)
- [Journalist and source risk assessment](templates/risk-assessment.md)
- [Pre-publication review checklist](templates/prepublication-review.md)
- [AI-assisted research policy](AI_ASSISTED_RESEARCH_POLICY.md)

### Decentralized ecosystem blueprints

- [Federated Journalism Network](blueprints/FEDERATED_JOURNALISM_NETWORK.md)
- [Open-Source Research Method](blueprints/OPEN_SOURCE_RESEARCH_METHOD.md)
- [Public Records Request Playbook](blueprints/PUBLIC_RECORDS_REQUEST_PLAYBOOK.md)
- [Independent Integrity Checkpoints](blueprints/INDEPENDENT_CHECKPOINTS.md)
- [Distributed Public-Information Catalog](blueprints/PUBLIC_INFORMATION_CATALOG.md)
- [Regional Adaptation Kit](blueprints/REGIONAL_ADAPTATION_KIT.md)
- [Synthetic Public Contract Training Exercise](training/SYNTHETIC_PUBLIC_CONTRACT_EXERCISE.md)

These materials are proposals and working aids, not implemented federation, secure source intake, legal advice, or safety guarantees. Each jurisdiction must adapt the workflows to local law, language, risks, and editorial practice. Contributions from journalists and community organizations are needed to test and improve them.
