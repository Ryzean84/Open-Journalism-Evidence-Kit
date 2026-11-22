#!/usr/bin/env node
"use strict";

// Independent, dependency-free OJEK Merkle v0.1 vector verifier.
// Run: node tests/reference/verify_merkle_vectors.js
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const fixturePath = path.join(__dirname, "..", "fixtures", "merkle-checkpoint-v0.1.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const LEAF_DOMAIN = Buffer.from("ojek:leaf:v1\0", "utf8");
const NODE_DOMAIN = Buffer.from("ojek:node:v1\0", "utf8");
const EMPTY_DOMAIN = Buffer.from("ojek:empty:v1\0", "utf8");
const SHA256_RE = /^[0-9a-f]{64}$/;

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function assertUnicodeScalarString(value) {
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(i + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) {
        throw new Error("lone high surrogate is not valid Unicode scalar text");
      }
      i += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) {
      throw new Error("lone low surrogate is not valid Unicode scalar text");
    }
  }
}

function canonicalLeafJson(recordId, recordDigest) {
  if (typeof recordId !== "string" || recordId.length === 0) {
    throw new Error("record_id must be a non-empty string");
  }
  assertUnicodeScalarString(recordId);
  if (typeof recordDigest !== "string" || !SHA256_RE.test(recordDigest)) {
    throw new Error("record_digest must be 64 lowercase hexadecimal characters");
  }
  // The two ASCII property names sort as record_digest, record_id.
  return "{\"record_digest\":" + JSON.stringify(recordDigest) +
    ",\"record_id\":" + JSON.stringify(recordId) + "}";
}

function leafHash(recordId, recordDigest) {
  return sha256(Buffer.concat([
    LEAF_DOMAIN,
    Buffer.from(canonicalLeafJson(recordId, recordDigest), "utf8"),
  ]));
}

function parentHash(left, right) {
  if (!SHA256_RE.test(left) || !SHA256_RE.test(right)) {
    throw new Error("child hashes must be lowercase SHA-256 digests");
  }
  return sha256(Buffer.concat([
    NODE_DOMAIN,
    Buffer.from(left, "hex"),
    Buffer.from(right, "hex"),
  ]));
}

function merkleRoot(leaves) {
  if (leaves.length === 0) return sha256(EMPTY_DOMAIN);
  let level = leaves.slice();
  while (level.length > 1) {
    const next = [];
    for (let i = 0; i < level.length; i += 2) {
      next.push(parentHash(level[i], level[i + 1] || level[i]));
    }
    level = next;
  }
  return level[0];
}

function verifyInclusionProof(proof) {
  if (!proof || typeof proof !== "object" ||
      proof.format !== "ojek-merkle-inclusion-proof" ||
      proof.protocol_version !== "0.1.0" ||
      !Number.isInteger(proof.leaf_index) ||
      !Number.isInteger(proof.leaf_count) ||
      proof.leaf_count < 1 ||
      proof.leaf_index < 0 ||
      proof.leaf_index >= proof.leaf_count ||
      !SHA256_RE.test(proof.merkle_root) ||
      !SHA256_RE.test(proof.checkpoint_digest) ||
      !Array.isArray(proof.path)) return false;

  let index = proof.leaf_index;
  let width = proof.leaf_count;
  let current;
  try {
    current = leafHash(proof.record_id, proof.record_digest);
    let expectedLevels = 0;
    for (let n = width; n > 1; n = Math.ceil(n / 2)) expectedLevels += 1;
    if (proof.path.length !== expectedLevels) return false;

    for (const step of proof.path) {
      if (!step || !SHA256_RE.test(step.hash)) return false;
      const expectedSide = index % 2 ? "left" : "right";
      if (step.side !== expectedSide) return false;
      if (index % 2) {
        current = parentHash(step.hash, current);
      } else {
        if (index + 1 >= width && step.hash !== current) return false;
        current = parentHash(current, step.hash);
      }
      index = Math.floor(index / 2);
      width = Math.ceil(width / 2);
    }
  } catch (_error) {
    return false;
  }
  return width === 1 && current === proof.merkle_root;
}

if (fixture.format !== "ojek-merkle-test-vectors" || fixture.protocol_version !== "0.1.0") {
  throw new Error("unsupported vector fixture");
}

let checks = 0;
for (const testCase of fixture.cases) {
  const leaves = testCase.records.map((record) =>
    leafHash(record.record_id, record.record_digest)
  );
  if (JSON.stringify(leaves) !== JSON.stringify(testCase.leaf_hashes)) {
    throw new Error(testCase.name + ": leaf hash mismatch");
  }
  if (merkleRoot(leaves) !== testCase.expected_root) {
    throw new Error(testCase.name + ": Merkle root mismatch");
  }
  if (testCase.canonical_json !== undefined) {
    const actual = canonicalLeafJson(
      testCase.records[0].record_id,
      testCase.records[0].record_digest
    );
    if (actual !== testCase.canonical_json) {
      throw new Error(testCase.name + ": canonical JSON mismatch");
    }
  }
  for (const proof of testCase.inclusion_proofs || []) {
    if (!verifyInclusionProof({
      format: "ojek-merkle-inclusion-proof",
      protocol_version: "0.1.0",
      ...proof,
    })) {
      throw new Error(testCase.name + ": inclusion proof failed for " + proof.record_id);
    }
    checks += 1;
  }
  checks += 2;
}

process.stdout.write("Verified " + fixture.cases.length +
  " vector cases and " + checks + " cross-language checks.\n");
