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

- [Global Decentralized Journalism Ecosystem](GLOBAL_JOURNALISM_ECOSYSTEM.md) — ecosystem map, repository boundaries, participation tracks, and build sequence.

- [Architecture](ARCHITECTURE.md)
- [Decentralized Public-Information Preservation](DECENTRALIZED_PRESERVATION.md)
- [Global Rights and Law Atlas proposal](GLOBAL_RIGHTS_AND_LAW_ATLAS.md)
- [Language and Accessibility Strategy](LANGUAGE_AND_ACCESSIBILITY.md)
- [Rights, Copyright, and Ethical Preservation](RIGHTS_COPYRIGHT_AND_ETHICS.md)
- [Roadmap](ROADMAP.md)

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

This repository is at the **foundational design stage**. These documents describe proposed architecture and policy; they do not claim that federation, daily checkpoints, translation infrastructure, or the legal atlas are implemented. See [Roadmap](ROADMAP.md) for implementation gates.

## Relationship to Huffman Systems / Open Intelligence Fabric

This project is intended to interoperate with the [Open Intelligence Fabric](https://github.com/Ryzean84/Open-Intelligence-Fabric) standards and governance work and the [OIF Research Observatory](https://github.com/Ryzean84/OIF-Research-Observatory). It should remain useful as an independent tool even without those systems.

## Participation

We welcome contributions from journalists, archivists, librarians, translators, researchers, software developers, legal scholars, and communities worldwide. Participation should be open, documented, respectful, and safe for contributors and sources.

Before implementation or deployment, read the rights, ethics, and security guidance. This project is not legal advice and cannot guarantee personal safety.
