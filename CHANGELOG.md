# Changelog

All notable project changes are documented here. This file records repository development; it does not imply that a version has been published as a stable release.

## Unreleased

### Added
- Experimental OJEK v0.2 append-only transparency-log primitives using the RFC 9162 Merkle tree shape and SHA-256.
- Consistency-proof generation and verification, unsigned tree heads, strict JSON parsing, offline CLI commands, and export of verified local ledger events as v0.2 references.
- Versioned JSON Schemas for v0.2 log entries, tree heads, and consistency-proof documents.
- Frozen v0.2 root, consistency-proof, and canonical-entry interoperability vectors.
- Independent Node.js reference implementation and expanded CI coverage.
- Protocol versioning policy, schema catalog, and operator runbook.
- CodeQL workflow, Dependabot configuration, and release-readiness checklist.

### Compatibility
- OJEK v0.1 snapshot checkpoint rules and verification remain unchanged.
- v0.2 artifacts use a distinct protocol identifier and must not be interpreted as v0.1 checkpoints.

### Limitations
- v0.2 tree heads are unsigned and operator-timestamped.
- Trusted timestamps, signed tree heads, independent witnesses, federation, and completeness guarantees are not implemented.
