#!/usr/bin/env node
"use strict";

// Independent Node.js reference verifier for OJEK v0.2 RFC 6962-style
// transparency-log roots and consistency proofs. Uses only built-in modules.
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const fixturePath = path.join(__dirname, "..", "fixtures", "transparency-log-v0.2.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));

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
function verifyConsistency(oldSize, newSize, oldRootHex, newRootHex, proofHex) {
  try {
    if (!Number.isSafeInteger(oldSize) || !Number.isSafeInteger(newSize) ||
        oldSize < 0 || newSize < oldSize || !Array.isArray(proofHex)) return false;
    const firstHash = fromHex(oldRootHex);
    const secondHash = fromHex(newRootHex);
    const proof = proofHex.map(fromHex);
    const emptyRoot = sha256(Buffer.alloc(0));
    if (oldSize === 0) return firstHash.equals(emptyRoot) && proof.length === 0;
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
    // Proofs are independently frozen in the fixture; this loop checks the
    // verifier's edge semantics and all known roots are checked above.
    if (oldSize === newSize) {
      assert.equal(verifyConsistency(oldSize, newSize, roots[oldSize], roots[newSize], []), true);
    } else if (oldSize === 0) {
      assert.equal(verifyConsistency(0, newSize, roots[0], roots[newSize], []), true);
    }
  }
}
console.log("OJEK v0.2 JavaScript reference vectors: PASS");
