# Protocol Versioning and Compatibility Policy

## Purpose

OJEK stores portable evidence metadata and cryptographic commitments. Protocol formats must remain independently verifiable long after implementation details and maintainers change. This policy defines how wire formats evolve.

## Version identifiers

Every cryptographic artifact carries an explicit protocol identifier. Verifiers dispatch only on recognized identifiers and fail closed on unknown values. A filename, README badge, Git branch, or package version is not a substitute for an artifact-level protocol identifier.

- v0.1 snapshot checkpoints use `protocol_version: 0.1.0`, `ojek-json-v1`, and `ojek-merkle-sha256-v1`.
- v0.2 transparency log entries and tree heads use `ojek-transparency-log-v0.2`.
- v0.2 consistency proof documents use `ojek-consistency-proof-v0.2`.
- Witness statements use a separate protocol identifier and version; they do not reuse a log or tree-head identifier.

## Compatibility rules

1. Never silently change canonicalization, hash prefixes, tree shape, leaf ordering, timestamp semantics, signature preimages, or required fields within a published protocol version.
2. Preserve historical verifiers and frozen vectors. Bug fixes must not redefine the meaning of an already accepted artifact.
3. Reject unknown fields unless the protocol explicitly defines an extension mechanism and its negotiation rules.
4. A new tree algorithm, digest algorithm, canonicalization rule, or signature profile requires a new protocol identifier.
5. Do not treat v0.1 snapshot roots as v0.2 transparency-log roots. Migration uses explicit digest-reference entries in a new log.
6. A successful parser or hash check does not imply source authenticity, completeness, trusted time, or truth.

## Canonical JSON profile

The current OJEK JSON profile is `ojek-json-v1`: UTF-8; object keys sorted by the implementation's Unicode ordering; compact separators; non-ASCII characters emitted directly; non-finite numeric constants rejected. Protocol objects restrict values to types and fields defined by their schemas. Implementations must reject duplicate JSON object members before validation. Cross-language vectors are normative.

This is a project-specific profile and is not a claim of RFC 8785/JCS compatibility.

## Cryptographic algorithm policy

- v0.1 uses its documented project-specific domain-separated SHA-256 construction with duplicate-last handling.
- v0.2 uses the RFC 9162 history-tree shape with SHA-256 and the 0x00 leaf / 0x01 node prefixes.
- Hashes are represented as 64 lowercase hexadecimal characters.
- Do not introduce algorithm agility without an explicit versioned algorithm identifier and independent vectors.

## Change process

A protocol change requires:

- an issue describing motivation, threat model, compatibility impact, and migration;
- a written specification before implementation;
- schemas and frozen positive/negative vectors;
- at least two independently maintained implementations for cryptographic interoperability;
- boundary, malformed-input, adversarial, and regression tests;
- review of privacy, source safety, rights, and operational impact;
- release notes that state what is and is not guaranteed.

A draft specification is not an implemented capability. A merged implementation is not automatically a production release. A production designation requires independent review and documented release gates.

## Deprecation

Deprecation must include a published notice, a support window where practical, migration instructions, and a retained verifier or documented archival verification path. Do not delete old fixtures or change old protocol semantics to simplify new development.
