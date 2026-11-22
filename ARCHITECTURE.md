# Open Journalism Evidence Kit — Architecture

**Project status:** Foundational design, version 0.2  
**Scope:** Global, decentralized, multilingual public-interest research and preservation.

## Mission
Build open, portable tools that help journalists, researchers, libraries, and the public preserve references to public information, verify provenance, examine changes, and make research methods reproducible. This is not a publisher, news agency, legal authority, or centralized archive.

## Architectural principles
1. Federation over centralization. Independent nodes can collect, validate, mirror, and serve records without depending on one operator.
2. Original sources remain authoritative for their own publications. We preserve references and evidence of what was observed; we do not impersonate publishers.
3. Integrity without false claims of truth. Cryptographic proofs can show that a recorded object has not changed since a checkpoint. They cannot prove that the source was accurate, unbiased, authentic, or complete.
4. Local-first. Research records and sensitive working notes remain under the user's control unless deliberately shared.
5. Multilingual by design. Original language is retained; translations are separate, attributed, versioned objects.
6. Rights-aware preservation. Store metadata, links, hashes, and limited permitted extracts by default. Store full content only where permission, license, public-domain status, or applicable law allows.
7. Human editorial responsibility. No automated system decides whether a person is guilty, whether a claim is true, or whether an article should be published.
8. Portable and replaceable components. Open formats, documented APIs, exportability, and independent implementations are preferred.

## Logical layers
### Source discovery
Connectors may discover public material through RSS/Atom, publisher APIs, official feeds, public datasets, sitemaps, and manual submission. Every connector must document scope, rate limits, terms, and data handling.

### Evidence record
A record may include canonical URL, publisher, title, byline when available, publication/update timestamps, retrieval timestamp, language, content type, source classification, rights metadata, content digest, and collection method. Missing values remain explicitly unknown.

### Integrity and history
Records are added to an append-only event sequence. Periodic batches can be represented by Merkle roots and signed checkpoints. Corrections are new events that refer to earlier records; they do not silently overwrite history.

### Replication
Independent nodes exchange signed manifests and permitted objects. Each node chooses what to mirror and publishes its own replication policy. Nodes can be disconnected and later reconcile through deterministic event identifiers and sequence metadata.

### Research and presentation
Users can search, compare versions, build timelines, cite records, annotate findings privately, and export evidence packages. Automated summaries must link to source records and disclose model/tool versions.

### Translation
A translation is a derivative record linked to the original. It records language pair, method, model/tool, timestamp, reviewer status, and uncertainty. Machine translation is never silently presented as the original.

## Trust model
- A source publisher is authoritative for the content it published, not for the truth of every claim.
- A node operator is responsible for the node's collection and replication behavior.
- A signature authenticates a signing key's statement; it does not prove the signer is trustworthy.
- A hash proves byte-level integrity relative to a known digest; it does not prove provenance by itself.
- Multiple independent witnesses can increase confidence that a record existed by a checkpoint, but cannot prove the underlying reporting was correct.
- Conflicting records remain visible with their provenance; the system does not manufacture consensus.

## Non-goals
- No token, cryptocurrency, speculative financial instrument, or mandatory blockchain.
- No universal centralized database or single global ranking of truth.
- No unrestricted scraping, access-control bypass, credential collection, or covert surveillance.
- No automatic republication of copyrighted articles.
- No replacement for editors, courts, legal counsel, or professional fact-checking.
- No claim that a tool can guarantee journalist or source safety.

## Initial implementation sequence
1. Define versioned evidence and event schemas.
2. Implement local SQLite or portable file-backed storage and deterministic exports.
3. Add append-only event records and hash-chain verification.
4. Add Merkle batch checkpoints and signed checkpoint format.
5. Build independent node sync with explicit allowlists and rate limits.
6. Add rights metadata and retention/deletion workflows.
7. Add language metadata and translation provenance.
8. Add newsroom workflows, accessibility, and low-bandwidth operation.
