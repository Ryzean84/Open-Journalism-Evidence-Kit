# OJEK Merkle Checkpoints v0.1

**Status: experimental, unsigned reference implementation.** This milestone adds deterministic Merkle commitments and inclusion proofs. It does not add digital signatures, trusted timestamps, independent witnesses, federation, or a production trust model.

## Checkpoint contents

A checkpoint contains a sorted manifest of record identifiers and existing SHA-256 record digests, a Merkle root, leaf count, protocol/canonicalization identifiers, an operator-asserted timestamp, and a digest over the checkpoint document.

## Deterministic v0.1 rules

- Canonical JSON: UTF-8, sorted object keys, compact separators, non-ASCII preserved, NaN and Infinity disallowed. This is the project-specific `ojek-json-v1` encoding, not a claim of RFC 8785/JCS compatibility; cross-language implementations must reproduce these exact rules and published vectors.
- Leaf order: ascending Unicode code-point order of `record_id`; no Unicode normalization is performed.
- Digest input: exactly 64 lowercase hexadecimal characters representing 32 bytes.
- Leaf hash: SHA-256(`0x6f6a656b3a6c6561663a763100` || canonical UTF-8 JSON object containing both `record_id` and `record_digest`).
- Parent hash: SHA-256(`0x6f6a656b3a6e6f64653a763100` || 32 raw left-hash bytes || 32 raw right-hash bytes).
- Odd levels duplicate the final hash as its own right sibling.
- Empty tree root: SHA-256 of the bytes `0x6f6a656b3a656d7074793a763100`.
- Checkpoint digest: SHA-256 of canonical checkpoint JSON before `checkpoint_digest` is added.

The hexadecimal domain prefixes above are the exact UTF-8 bytes of the ASCII labels followed by a single zero byte. Domain separation distinguishes leaves, internal nodes, and empty trees. Protocol changes require a new version and test vectors. In v0.1, the verifier requires the exact `clock_statement` value `operator_asserted_unwitnessed` and rejects unknown top-level fields; extensions require a versioned protocol update rather than silently changing verifier semantics.

The frozen fixture at `tests/fixtures/merkle-checkpoint-v0.1.json` is the interoperability contract. It includes a Unicode identifier, canonical UTF-8 JSON bytes, leaf hashes, roots, and portable inclusion proofs. The Python test suite and the dependency-free JavaScript verifier at `tests/reference/verify_merkle_vectors.js` both consume the same fixture. Run the JavaScript verifier with Node.js 22 or later:

```bash
node tests/reference/verify_merkle_vectors.js
```

The JavaScript verifier is an independent implementation of the v0.1 leaf, parent, empty-tree, and inclusion-proof rules. It deliberately rejects lone UTF-16 surrogates rather than silently encoding invalid Unicode.

## Use

```bash
ojek --workspace ./my-ledger checkpoint create --output exports/checkpoint.json
ojek --workspace ./my-ledger checkpoint verify ./my-ledger/exports/checkpoint.json
ojek --workspace ./my-ledger checkpoint proof ./my-ledger/exports/checkpoint.json --record-id "urn:uuid:REPLACE-WITH-ID"
ojek --workspace ./my-ledger checkpoint verify-proof proof.json ./my-ledger/exports/checkpoint.json
```

A proof is verified against a checkpoint's root and checkpoint digest. A user must still obtain and trust the checkpoint through an independent channel; an unsigned checkpoint can be replaced by its creator.

## Security and trust limitations

- v0.1 checkpoints are **unsigned**. Anyone can create a replacement and recompute its digest. The digest detects accidental changes, not malicious replacement by someone controlling the file.
- The timestamp is an operator assertion, not a trusted timestamp.
- Inclusion proves that a record identifier and digest are committed by the stated root, not that the record is true, authentic, complete, lawfully collected, or published at the asserted time.
- A checkpoint covers only its declared leaves; it does not prove all records were included.
- Public manifests can reveal research activity. Never checkpoint confidential source identities, private communications, credentials, or sensitive investigative metadata.
- This version creates, stores, and manages no private keys.

## Next release gates

Before signing or federation: publish cross-language test vectors; define Ed25519 key binding, rotation, expiry, revocation and recovery; add independently operated witness statements; define clock and witness policies; test adversarial proofs and canonicalization across implementations; and complete external security review.
