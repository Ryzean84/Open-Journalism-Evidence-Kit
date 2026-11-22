#!/usr/bin/env node
"use strict";

// Independent Node.js reference verifier for OJEK v0.2 RFC 9162-style
// transparency-log roots and consistency proofs. Uses only built-in modules.
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const fixturePath = path.join(__dirname, "..", "fixtures", "transparency-log-v0.2.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));

function canonicalJson(value) {
  if (value === null) return "null";
  if (typeof value === "string") {
    for (let i = 0; i < value.length; i += 1) {
      const code = value.charCodeAt(i);
      if (code >= 0xd800 && code <= 0xdbff) {
        const next = value.charCodeAt(i + 1);
        if (!(next >= 0xdc00 && next <= 0xdfff)) throw new TypeError("unpaired UTF-16 high surrogate");
        i += 1;
      } else if (code >= 0xdc00 && code <= 0xdfff) {
        throw new TypeError("unpaired UTF-16 low surrogate");
      }
    }
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite JSON number");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  if (typeof value === "object") {
    const keys = Object.keys(value).sort();
    return "{" + keys.map((key) => JSON.stringify(key) + ":" + canonicalJson(value[key])).join(",") + "}";
  }
  throw new TypeError("unsupported canonical JSON value");
}
function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest();
}
function fromHex(value) {
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) {
    throw new TypeError("digest must be 64 lowercase hexadecimal characters");
  }
  return Buffer.from(value, "hex");
}
function leafHash(entryBytes) {
  return sha256(Buffer.concat([Buffer.from([0x00]), Buffer.from(entryBytes)]));
}
function largestPowerOfTwoLessThan(n) {
  if (!Number.isSafeInteger(n) || n < 2) throw new RangeError("invalid tree split");
  let k = 1;
  while (k * 2 < n) k *= 2;
  return k;
}
function merkleRoot(entries) {
  if (!Array.isArray(entries)) throw new TypeError("entries must be an array");
  if (entries.length === 0) return sha256(Buffer.alloc(0));
  if (entries.length === 1) return leafHash(Buffer.from(entries[0], "utf8"));
  const k = largestPowerOfTwoLessThan(entries.length);
  return sha256(Buffer.concat([
    Buffer.from([0x01]),
    merkleRoot(entries.slice(0, k)),
    merkleRoot(entries.slice(k)),
  ]));
}
function subproof(oldSize, leaves, completeSubtree) {
  const n = leaves.length;
  if (oldSize === n) return completeSubtree ? [] : [merkleRoot(leaves)];
  const k = largestPowerOfTwoLessThan(n);
  if (oldSize <= k) return subproof(oldSize, leaves.slice(0, k), completeSubtree).concat([merkleRoot(leaves.slice(k))]);
  return subproof(oldSize - k, leaves.slice(k), false).concat([merkleRoot(leaves.slice(0, k))]);
}
function generateConsistency(entries, oldSize) {
  if (!Number.isSafeInteger(oldSize) || oldSize < 0 || oldSize > entries.length) {
    throw new RangeError("old tree size out of range");
  }
  if (oldSize === 0 || oldSize === entries.length) return [];
  const leaves = entries.map((entry) => Buffer.from(entry, "utf8"));
  return subproof(oldSize, leaves, true).map((node) => node.toString("hex"));
}
function verifyConsistency(oldSize, newSize, oldRootHex, newRootHex, proofHex) {
  try {
    if (!Number.isSafeInteger(oldSize) || !Number.isSafeInteger(newSize) ||
        oldSize < 0 || newSize < oldSize || !Array.isArray(proofHex)) return false;
    const firstHash = fromHex(oldRootHex);
    const secondHash = fromHex(newRootHex);
    const proof = proofHex.map(fromHex);
    const emptyRoot = sha256(Buffer.alloc(0));
    if (oldSize === 0) return firstHash.equals(emptyRoot) && proof.length === 0 &&
      (newSize > 0 || secondHash.equals(emptyRoot));
    if (oldSize === newSize) return firstHash.equals(secondHash) && proof.length === 0;
    if (proof.length === 0) return false;

    let fn = oldSize - 1;
    let sn = newSize - 1;
    while ((fn & 1) === 1) {
      fn = Math.floor(fn / 2);
      sn = Math.floor(sn / 2);
    }
    let cursor = 0;
    let fr;
    let sr;
    if (fn === 0) {
      fr = firstHash;
      sr = firstHash;
    } else {
      fr = proof[0];
      sr = proof[0];
      cursor = 1;
    }
    while (cursor < proof.length) {
      if (sn === 0) return false;
      const node = proof[cursor];
      if ((fn & 1) === 1 || fn === sn) {
        fr = sha256(Buffer.concat([Buffer.from([0x01]), node, fr]));
        sr = sha256(Buffer.concat([Buffer.from([0x01]), node, sr]));
        while (fn !== 0 && (fn & 1) === 0) {
          fn = Math.floor(fn / 2);
          sn = Math.floor(sn / 2);
        }
      } else {
        sr = sha256(Buffer.concat([Buffer.from([0x01]), sr, node]));
      }
      fn = Math.floor(fn / 2);
      sn = Math.floor(sn / 2);
      cursor += 1;
    }
    return fr.equals(firstHash) && sr.equals(secondHash) && sn === 0;
  } catch (_) {
    return false;
  }
}

assert.equal(fixture.format, "ojek-transparency-log-v0.2-test-vectors");
assert.throws(() => canonicalJson("\\ud800"), /surrogate/);
assert.equal(verifyConsistency(0, 0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "0".repeat(64), []), false);
const canonicalEntryBytes = Buffer.from(canonicalJson(fixture.canonical_entry), "utf8");
assert.equal(canonicalEntryBytes.toString("utf8"), fixture.canonical_entry_bytes);
assert.equal(leafHash(canonicalEntryBytes).toString("hex"), fixture.canonical_entry_leaf_hash);
const headVector = fixture.tree_head_vector;
const headPreimage = canonicalJson({
  protocol: headVector.protocol,
  log_id: headVector.log_id,
  tree_size: headVector.tree_size,
  root_hash: headVector.root_hash,
  issued_at: headVector.issued_at,
  hash_algorithm: headVector.hash_algorithm,
});
assert.equal(headPreimage, headVector.canonical_preimage);
assert.equal(sha256(Buffer.from(headPreimage, "utf8")).toString("hex"), headVector.tree_head_digest);
for (const vector of fixture.roots) {
  assert.equal(merkleRoot(fixture.entries.slice(0, vector.tree_size)).toString("hex"), vector.root_hash,
    `root mismatch at size ${vector.tree_size}`);
}
for (const testCase of fixture.consistency_cases) {
  assert.equal(verifyConsistency(
    testCase.old_size, testCase.new_size, testCase.old_root, testCase.new_root, testCase.proof
  ), true, `consistency proof failed: ${testCase.old_size} -> ${testCase.new_size}`);
  assert.equal(verifyConsistency(
    testCase.old_size, testCase.new_size, "0".repeat(64), testCase.new_root, testCase.proof
  ), false, "modified old root must fail");
  assert.equal(verifyConsistency(
    testCase.old_size, testCase.new_size, testCase.old_root, "0".repeat(64), testCase.proof
  ), false, "modified new root must fail");
}

// Adversarial checks: malformed, truncated and extended proof encodings.
for (const testCase of fixture.consistency_cases) {
  const p = testCase.proof;
  assert.equal(verifyConsistency(testCase.old_size, testCase.new_size,
    testCase.old_root, testCase.new_root, p.concat(["0".repeat(64)])), false);
  assert.equal(verifyConsistency(testCase.old_size, testCase.new_size,
    testCase.old_root, testCase.new_root, p.concat(["z".repeat(64)])), false);
  if (p.length > 1) {
    assert.equal(verifyConsistency(testCase.old_size, testCase.new_size,
      testCase.old_root, testCase.new_root, p.slice(0, -1)), false);
    assert.equal(verifyConsistency(testCase.old_size, testCase.new_size,
      testCase.old_root, testCase.new_root, [...p].reverse()), false);
  }
}

// Verify every prefix pair against independently computed roots.
const generated = Array.from({ length: 40 }, (_, i) => `node-generated-entry-${i}`);
const roots = Array.from({ length: generated.length + 1 }, (_, n) =>
  merkleRoot(generated.slice(0, n)).toString("hex"));
for (let oldSize = 0; oldSize <= generated.length; oldSize += 1) {
  for (let newSize = oldSize; newSize <= generated.length; newSize += 1) {
    const proof = generateConsistency(generated.slice(0, newSize), oldSize);
    assert.equal(verifyConsistency(oldSize, newSize, roots[oldSize], roots[newSize], proof), true,
      `generated proof failed: ${oldSize} -> ${newSize}`);
  }
}
console.log("OJEK v0.2 JavaScript reference vectors: PASS");
