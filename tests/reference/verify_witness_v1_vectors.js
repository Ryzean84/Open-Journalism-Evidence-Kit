#!/usr/bin/env node
"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const fixture = JSON.parse(fs.readFileSync(
  path.join(__dirname, "..", "fixtures", "witness-v0.1.json"), "utf8"
));
const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest();
const hex = (value, length) => {
  if (typeof value !== "string" || value.length !== length || !new RegExp(`^[0-9a-f]{${length}}$`).test(value)) {
    throw new TypeError("invalid hexadecimal encoding");
  }
  return Buffer.from(value, "hex");
};
function canonicalJson(value) {
  if (value === null) return "null";
  if (typeof value === "string") {
    for (let i = 0; i < value.length; i += 1) {
      const code = value.charCodeAt(i);
      if (code >= 0xd800 && code <= 0xdbff) {
        const next = value.charCodeAt(i + 1);
        if (!(next >= 0xdc00 && next <= 0xdfff)) throw new TypeError("unpaired high surrogate");
        i += 1;
      } else if (code >= 0xdc00 && code <= 0xdfff) {
        throw new TypeError("unpaired low surrogate");
      }
    }
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) throw new TypeError("protocol numbers must be safe integers");
    return String(value);
  }
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  if (typeof value === "object") {
    const keys = Object.keys(value).sort();
    return "{" + keys.map((key) => JSON.stringify(key) + ":" + canonicalJson(value[key])).join(",") + "}";
  }
  throw new TypeError("unsupported canonical JSON value");
}
function rawEd25519PublicKey(hexKey) {
  const raw = hex(hexKey, 64);
  const spkiPrefix = Buffer.from("302a300506032b6570032100", "hex");
  return crypto.createPublicKey({
    key: Buffer.concat([spkiPrefix, raw]),
    format: "der",
    type: "spki",
  });
}
function verifyEd25519(publicKeyHex, message, signatureHex) {
  return crypto.verify(null, message, rawEd25519PublicKey(publicKeyHex), hex(signatureHex, 128));
}
function verifyTreeHead(head) {
  const keys = ["protocol", "log_id", "tree_size", "root_hash", "issued_at", "hash_algorithm", "tree_head_digest"];
  if (!head || Object.keys(head).sort().join("|") !== keys.sort().join("|")) return false;
  if (head.protocol !== "ojek-transparency-log-v0.2" || head.hash_algorithm !== "sha-256") return false;
  const preimage = {
    protocol: head.protocol, log_id: head.log_id, tree_size: head.tree_size,
    root_hash: head.root_hash, issued_at: head.issued_at, hash_algorithm: head.hash_algorithm,
  };
  return sha256(Buffer.from(canonicalJson(preimage), "utf8")).toString("hex") === head.tree_head_digest;
}
function verifyConsistency(oldSize, newSize, oldRoot, newRoot, proof) {
  try {
    const first = hex(oldRoot, 64);
    const second = hex(newRoot, 64);
    const nodes = proof.map((node) => hex(node, 64));
    const empty = sha256(Buffer.alloc(0));
    if (oldSize === 0) return first.equals(empty) && nodes.length === 0 && (newSize > 0 || second.equals(empty));
    if (oldSize === newSize) return first.equals(second) && nodes.length === 0;
    if (newSize < oldSize || nodes.length === 0) return false;
    let fn = oldSize - 1;
    let sn = newSize - 1;
    while ((fn & 1) === 1) { fn = Math.floor(fn / 2); sn = Math.floor(sn / 2); }
    let cursor = 0;
    let fr, sr;
    if (fn === 0) { fr = first; sr = first; }
    else { fr = nodes[0]; sr = nodes[0]; cursor = 1; }
    while (cursor < nodes.length) {
      if (sn === 0) return false;
      const node = nodes[cursor];
      if ((fn & 1) === 1 || fn === sn) {
        fr = sha256(Buffer.concat([Buffer.from([1]), node, fr]));
        sr = sha256(Buffer.concat([Buffer.from([1]), node, sr]));
        while (fn !== 0 && (fn & 1) === 0) { fn = Math.floor(fn / 2); sn = Math.floor(sn / 2); }
      } else {
        sr = sha256(Buffer.concat([Buffer.from([1]), sr, node]));
      }
      fn = Math.floor(fn / 2); sn = Math.floor(sn / 2); cursor += 1;
    }
    return fr.equals(first) && sr.equals(second) && sn === 0;
  } catch (_) { return false; }
}
function verifyKeyDocument(doc) {
  try {
    if (doc.protocol !== "ojek-witness-key-v0.1" || doc.signature_algorithm !== "ed25519") return false;
    const pub = hex(doc.public_key, 64);
    const keyId = sha256(Buffer.concat([Buffer.from("OJEK-WITNESS-KEY-v0.1\0"), pub])).toString("hex");
    return keyId === doc.key_id;
  } catch (_) { return false; }
}
function statementPayload(statement) {
  const { signature, ...payload } = statement;
  return payload;
}
function statementDigest(statement) {
  return sha256(Buffer.concat([
    Buffer.from("OJEK-WITNESS-STATEMENT-DIGEST-v0.1\0"),
    Buffer.from(canonicalJson(statement), "utf8"),
  ])).toString("hex");
}
function proofDigest(proof) {
  return sha256(Buffer.concat([
    Buffer.from("OJEK-CONSISTENCY-PROOF-DIGEST-v0.2\0"),
    Buffer.from(canonicalJson(proof), "utf8"),
  ])).toString("hex");
}
function verifyStatement(statement, keyDoc, treeHead) {
  if (!verifyKeyDocument(keyDoc) || !verifyTreeHead(treeHead)) return false;
  if (statement.protocol !== "ojek-witness-statement-v0.1" ||
      statement.witness_id !== keyDoc.witness_id || statement.key_id !== keyDoc.key_id ||
      statement.log_id !== treeHead.log_id || statement.tree_size !== treeHead.tree_size ||
      statement.root_hash !== treeHead.root_hash || statement.tree_head_digest !== treeHead.tree_head_digest) return false;
  const message = Buffer.concat([
    Buffer.from("OJEK-WITNESS-STATEMENT-v0.1\0"),
    Buffer.from(canonicalJson(statementPayload(statement)), "utf8"),
  ]);
  return verifyEd25519(keyDoc.public_key, message, statement.signature);
}

assert.equal(fixture.format, "ojek-witness-v0.1-test-vectors");
assert.equal(verifyKeyDocument(fixture.old_key_document), true);
assert.equal(verifyKeyDocument(fixture.new_key_document), true);
assert.equal(verifyTreeHead(fixture.old_tree_head), true);
assert.equal(verifyTreeHead(fixture.new_tree_head), true);
assert.equal(statementDigest(fixture.first_statement), fixture.first_statement_digest);
assert.equal(proofDigest(fixture.consistency_proof), fixture.consistency_proof_digest);
assert.equal(verifyStatement(fixture.first_statement, fixture.old_key_document, fixture.old_tree_head), true);
assert.equal(verifyStatement(fixture.second_statement, fixture.new_key_document, fixture.new_tree_head), true);
assert.equal(verifyConsistency(
  fixture.consistency_proof.old_tree_size,
  fixture.consistency_proof.new_tree_size,
  fixture.consistency_proof.old_root,
  fixture.consistency_proof.new_root,
  fixture.consistency_proof.proof,
), true);

const transition = fixture.key_transition;
const transitionPayload = {
  protocol: transition.protocol, witness_id: transition.witness_id,
  previous_key_id: transition.previous_key_id, new_key_id: transition.new_key_id,
  created_at: transition.created_at, signature_algorithm: transition.signature_algorithm,
};
const transitionMessage = Buffer.concat([
  Buffer.from("OJEK-WITNESS-KEY-TRANSITION-v0.1\0"),
  Buffer.from(canonicalJson(transitionPayload), "utf8"),
]);
assert.equal(verifyEd25519(fixture.old_key_document.public_key, transitionMessage, transition.previous_key_signature), true);
assert.equal(verifyEd25519(fixture.new_key_document.public_key, transitionMessage, transition.new_key_signature), true);
assert.equal(sha256(Buffer.concat([
  Buffer.from("OJEK-WITNESS-KEY-TRANSITION-v0.1\0"),
  Buffer.from(canonicalJson(transition), "utf8"),
])).toString("hex"), fixture.key_transition_digest);

const badStatement = structuredClone(fixture.second_statement);
badStatement.signature = "0".repeat(128);
assert.equal(verifyStatement(badStatement, fixture.new_key_document, fixture.new_tree_head), false);
console.log("OJEK witness v0.1 JavaScript reference vectors: PASS");
