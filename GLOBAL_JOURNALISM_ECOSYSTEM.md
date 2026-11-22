# Global Decentralized Journalism Ecosystem

**Status:** Strategy and build plan  
**Parent foundation:** Open Journalism Evidence Kit (OJEK)  
**Interoperability:** Open Intelligence Fabric (OIF)  
**Principle:** Build a network of independent public-interest capabilities, not a centralized media platform.

## 1. Mission

Enable independent journalists, local newsrooms, researchers, archivists, libraries, universities, civil-society organizations, and communities to publish, preserve, verify, contextualize, and access public-interest information across borders and languages.

The network must not require a single publisher, server operator, funder, identity provider, or editorial authority. Each participant retains control over its own work, policies, and infrastructure while using open formats to interoperate.

## 2. What this is—and is not

This is:
- Open infrastructure for independent journalism and public-interest research.
- A federated network of independently operated nodes and archives.
- A set of interoperable tools, schemas, and workflows.
- A way to preserve source provenance, corrections, uncertainty, and research methods.
- A participation framework for people with technical and non-technical skills.

This is not:
- A centralized global newsroom or universal editor.
- A machine that declares disputed claims true or false.
- A mass-scraping or unrestricted collection system.
- A public repository for confidential source identities or leaked personal data.
- A token, cryptocurrency, or mandatory blockchain project.
- A replacement for local journalism, professional editors, legal counsel, or source-protection specialists.

## 3. Ecosystem map

| Layer | Responsibility | Current home / direction |
|---|---|---|
| Shared standards | Common terminology, provenance envelopes, capability descriptions, policy boundaries, interoperability | Open Intelligence Fabric |
| Evidence records | Source observations, metadata, rights status, integrity digests, corrections, evidence exports | Open Journalism Evidence Kit |
| Research quality | Reproducible methods, evaluations, limitations, incident learning | OIF Research Observatory |
| Legal and civic context | Laws, rights, jurisdictions, founding documents, official sources | Global Rights and Law Atlas |
| Secure source intake | Confidential tip submission and journalist-source communication | Integrate established projects such as SecureDrop; do not casually reimplement |
| Visual verification | Geolocation, chronology, media provenance, collaborative review | Integrate or interoperate with established projects such as Atlos and Bellingcat tools |
| Public web preservation | Capture permitted public records, observe changes, preserve metadata and integrity evidence | OJEK connectors plus integrations with ArchiveBox/Webrecorder/Auto Archiver where appropriate |
| Censorship and access monitoring | Document network interference, shutdowns, and accessibility barriers | Integrate established measurement projects such as OONI |
| Distribution | Independent publication, feeds, mirrors, subscriptions, multilingual access | Future federation and distribution protocol |
| Participation and discovery | Find independent publishers, archives, projects, local contributors, and open tasks | Future opt-in directory; avoid a centralized ranking authority |

## 4. Proposed repository portfolio

Do not create all of these immediately. First prove the interfaces and boundaries. A repository should be created only when it has a distinct user, independently testable purpose, maintainable scope, and clear relationship to existing upstream projects.

### Existing repositories to strengthen

1. **Open-Journalism-Evidence-Kit** — the core evidence format and local-first tools.
   - Next: finish the v0.1 source-observation schema tests and fixtures.
   - Next: implement a tiny local evidence ledger and deterministic export.
   - Next: add correction, restriction, and removal event examples.
   - Next: add a reproducible verification command and test vectors.

2. **Open-Intelligence-Fabric** — shared contracts, not a central execution engine.
   - Next: publish a versioned provenance envelope and capability manifest.
   - Next: define compatibility rules and machine-readable policy decisions.
   - Next: add conformance fixtures that independent repositories can test.

3. **OIF-Research-Observatory** — research and evaluation.
   - Next: establish a public project/tool assessment template.
   - Next: test decentralization, privacy, accessibility, energy, and resilience claims.
   - Next: publish reproducible evaluations with uncertainty and limitations.

4. **Global-Rights-and-Law-Atlas** — separate civic/legal dataset.
   - Continue the Colorado pilot independently.
   - Link legal-source records to journalism evidence only through stable references.
   - Keep law, reporting, testimony, commentary, and reform proposals distinct.

### Candidate new repositories

#### A. Open Journalism Federation Protocol (proposed)
**Purpose:** Define how independent journalism nodes exchange signed metadata, source observations, corrections, manifests, and permitted archive references.

Initial deliverables:
- Protocol goals and threat model.
- Node identity and signed capability manifest.
- Versioned event envelope.
- Subscription and replication manifest.
- Opt-in replication, quotas, allowlists, and revocation.
- Offline synchronization and conflict semantics.
- Conformance fixtures and reference test vectors.

This should be the first candidate new repository, but only after the OIF and OJEK contracts are stable enough to avoid competing schemas.

#### B. Independent Archive Node (proposed)
**Purpose:** A small, self-hostable implementation that libraries, newsrooms, universities, and community groups can run independently.

Initial deliverables:
- Local-first metadata store.
- Import/export of OJEK records.
- Signature and digest verification.
- Selective replication.
- Operator-configured retention and access policy.
- Low-resource deployment and backup guide.

Do not build this before the federation protocol and evidence record are stable.

#### C. Journalism Commons Directory (proposed)
**Purpose:** An opt-in, federated directory of independent newsrooms, journalists' collectives, community archives, research groups, and public-interest tools.

Initial deliverables:
- Publisher-controlled profiles and contact methods.
- Language, region, coverage, and accessibility metadata.
- Verification status with transparent criteria.
- Exportable directory feeds and independent mirrors.
- Clear separation between identity verification and editorial endorsement.

No global credibility score, popularity leaderboard, or central authority over who counts as a journalist.

#### D. Low-Bandwidth Journalism Access Kit (proposed)
**Purpose:** Make public-interest reporting and evidence accessible where connectivity, devices, bandwidth, or language support are limited.

Initial deliverables:
- Offline-first reading bundles.
- RSS/Atom and open-feed ingestion.
- Human-reviewed translation workflow.
- Screen-reader and low-bandwidth design guidance.
- Community print/export formats.
- Synchronization that does not expose sensitive reading histories.

#### E. Public Evidence Review Workbench (proposed; evaluate integrations first)
**Purpose:** Give small teams a reproducible workspace for comparing public sources, timelines, media observations, and corrections.

Initial deliverables:
- Evidence references and annotations.
- Timeline and claim-to-source links.
- Separate observation, inference, and editorial conclusion.
- Reviewer notes and disagreement records.
- Exportable investigation package.

Before creating this repository, assess whether OJEK plus integrations with Atlos, Bellingcat tools, and existing document platforms already meet the need.

## 5. Participation: the global work table

Participation must not be limited to software developers.

| Contributor | Useful work |
|---|---|
| Local journalists | Identify local reporting needs, public records, and safe workflows |
| Community members | Document local context, public sources, language needs, and corrections |
| Archivists and librarians | Preservation practice, cataloguing, retention, metadata quality |
| Translators | Original-language review, translation, terminology, accessibility |
| Researchers | Methods, source evaluation, reproducibility, comparative analysis |
| Developers | Schemas, tests, connectors, local tools, interoperability |
| Security specialists | Threat modelling, source protection, secure deployment review |
| Legal researchers | Rights, copyright, jurisdiction, privacy, and takedown process |
| Educators | Training materials and media/evidence literacy |
| Designers and accessibility specialists | Low-bandwidth, multilingual, accessible interfaces |
| Node operators | Independent hosting, replication policy, backup, and uptime transparency |
| Funders and institutions | Transparent, non-exclusive support without editorial control |

## 6. Contribution tracks

Every contribution should have a clear path:

1. **Discover:** identify a missing source, tool, language, region, workflow, or accessibility need.
2. **Document:** describe the need, evidence, intended users, and risks.
3. **Propose:** open an issue or discussion before adding a large feature.
4. **Build:** submit a small, reviewable change with tests and documentation.
5. **Review:** invite independent review, including local or language expertise where relevant.
6. **Verify:** demonstrate the behavior against fixtures and document limitations.
7. **Release:** version the result and publish migration notes.
8. **Learn:** record corrections, failures, and user feedback without blame.

Recognition should reward careful review, useful corrections, translation quality, accessibility, maintenance, and community service—not volume, speed, political alignment, or popularity.

## 7. Trust, safety, and editorial boundaries

- Preserve the distinction between source material, metadata, observation, inference, translation, commentary, and editorial conclusion.
- Never treat a cryptographic hash, signature, or timestamp as proof that a claim is true.
- Keep source identities, private communications, credentials, and sensitive investigative material out of public records.
- Make collection scope, method, rights basis, retention, and replication policy explicit.
- Do not bypass access controls, paywalls, or platform restrictions.
- Do not publish precise location data or identifying details that could expose vulnerable people.
- Support correction, restriction, and removal even when integrity history is append-only.
- Keep moderation and abuse-response policies visible and appealable.
- Require human review for consequential editorial or external actions.
- Make funding, sponsorship, conflicts of interest, and governance changes transparent.

## 8. Funding and governance

The ecosystem should be able to survive without one sponsor. Explore:
- Small recurring donations and public-interest grants.
- University and library partnerships.
- Newsroom and community infrastructure cooperatives.
- In-kind hosting, translation, accessibility, and security reviews.
- Transparent project budgets and conflict-of-interest disclosures.

No funder should receive hidden editorial control. No token or speculative asset is required. A contribution record is not a financial instrument.

## 9. Build order: practical sequence

### Stage 1 — Make the existing foundation real
- Complete schema validation and sample fixtures in OJEK.
- Implement a local evidence ledger with export and verification.
- Add correction and restriction event examples.
- Publish OIF shared contracts and compatibility tests.
- Create a contribution guide for non-developers.

### Stage 2 — Prove independent interoperability
- Define the federation protocol in a separate specification repository.
- Build two minimal independent test nodes.
- Demonstrate signed manifests, selective replication, and offline synchronization.
- Test revocation, conflicting records, abusive peers, and resource limits.

### Stage 3 — Open the participation network
- Launch the opt-in Journalism Commons Directory.
- Add multilingual and low-bandwidth workflows.
- Establish independent node operator guidance.
- Pilot with a small number of willing libraries, local newsrooms, universities, and community archives.

### Stage 4 — Expand through partnerships
- Integrate mature source-intake and visual-verification tools.
- Add public-record and legal-source connectors with explicit permissions.
- Expand by language and region through local maintainers.
- Publish independent security, privacy, accessibility, and sustainability reviews.

## 10. First 30 concrete tasks

1. Add JSON Schema tests for OJEK source observations.
2. Add valid and invalid example fixtures.
3. Define a stable event ID and correction reference.
4. Define a privacy-safe restriction event.
5. Define deterministic evidence package export.
6. Implement digest verification.
7. Document local storage and backup.
8. Add a rights-review checklist to collection workflows.
9. Add a source-risk checklist for public submissions.
10. Publish an OIF provenance envelope.
11. Publish an OIF capability manifest.
12. Add compatibility fixtures for both contracts.
13. Write the federation threat model.
14. Compare ActivityPub, RSS/Atom, and other open distribution options.
15. Evaluate SecureDrop integration boundaries.
16. Evaluate Atlos integration boundaries.
17. Evaluate Bellingcat Auto Archiver integration boundaries.
18. Evaluate OONI data integration boundaries.
19. Evaluate ArchiveBox and Webrecorder preservation boundaries.
20. Define a non-centralized publisher profile format.
21. Define directory inclusion and verification criteria.
22. Draft a multilingual contributor guide.
23. Draft a low-bandwidth and offline requirements checklist.
24. Draft a node operator policy template.
25. Draft an independent security review checklist.
26. Draft a community correction and appeal process.
27. Identify three potential pilot partners (no commitments assumed).
28. Create a public issue template for new regional/language needs.
29. Publish a transparent funding and conflict-of-interest policy.
30. Run an end-to-end tabletop exercise before any public deployment.

## 11. Definition of meaningful progress

Progress is not the number of repositories, commits, agents, or records collected. Progress is demonstrated when an independent local group can use the tools, retain control of its work, verify what it receives, correct mistakes, protect sources, and leave the network without losing its own records.

**The measure of decentralization is whether participants can operate independently—not whether a central project claims to be decentralized.**
