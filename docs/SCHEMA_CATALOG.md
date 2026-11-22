# Protocol Schema Catalog

The JSON Schemas in this directory define machine-readable structural contracts. They complement—not replace—the semantic and cryptographic checks in the reference implementation. See the [protocol versioning policy](PROTOCOL_VERSIONING.md) and [operator runbook](OPERATOR_RUNBOOK.md) for compatibility and operational requirements.

| Schema | Protocol object | Primary verifier |
|---|---|---|
| [source-observation.v0.1](../schemas/source-observation.v0.1.schema.json) | Local source observation metadata | Local ledger validation |
| [transparency-log-entry.v0.2](../schemas/transparency-log-entry.v0.2.schema.json) | Ordered v0.2 log entry | `validate_log_entry` |
| [transparency-tree-head.v0.2](../schemas/transparency-tree-head.v0.2.schema.json) | Unsigned v0.2 tree head | `verify_tree_head` |
| [transparency-consistency-proof.v0.2](../schemas/transparency-consistency-proof.v0.2.schema.json) | Proof between two tree heads | `verify_consistency_proof_document` |

## Validation boundary

JSON Schema checks object shape, field types, enumerations, and basic string formats. It cannot prove that:

- a tree root was correctly computed from the full ordered entry sequence;
- a proof establishes append-only consistency;
- a tree head was issued by a particular operator;
- the operator's clock is accurate;
- a log is complete or a source is true.

Always run the cryptographic verifier after schema validation. Verifiers reject unknown fields and unsupported protocol identifiers.
