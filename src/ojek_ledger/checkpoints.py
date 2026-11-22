"""Deterministic, unsigned OJEK Merkle checkpoints (protocol v0.1)."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

PROTOCOL_VERSION = "0.1.0"
CANONICALIZATION = "ojek-json-v1"
TREE_ALGORITHM = "ojek-merkle-sha256-v1"
LEAF_DOMAIN = b"ojek:leaf:v1\x00"
NODE_DOMAIN = b"ojek:node:v1\x00"
EMPTY_DOMAIN = b"ojek:empty:v1\x00"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CheckpointError(ValueError):
    """Invalid checkpoint input or structure."""


def canonical_bytes(value: Any) -> bytes:
    """Return the v0.1 canonical JSON representation."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise CheckpointError(f"value cannot be canonically encoded: {exc}") from exc


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_bytes(value: Any, field: str = "digest") -> bytes:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise CheckpointError(f"{field} must be 64 lowercase hexadecimal characters")
    return bytes.fromhex(value)


def _record_identity(record_id: Any, record_digest: Any) -> bytes:
    if not isinstance(record_id, str) or not record_id:
        raise CheckpointError("record_id must be a non-empty string")
    _digest_bytes(record_digest, "record_digest")
    return canonical_bytes({"record_id": record_id, "record_digest": record_digest})


def leaf_hash(record_id: str, record_digest: str) -> str:
    """Commit to both the record identifier and its lowercase SHA-256 digest."""
    return sha256(LEAF_DOMAIN + _record_identity(record_id, record_digest))


def _parent(left: str, right: str) -> str:
    return sha256(NODE_DOMAIN + _digest_bytes(left, "left child hash") + _digest_bytes(right, "right child hash"))


def _levels(leaf_hashes: list[str]) -> list[list[str]]:
    if not leaf_hashes:
        return [[sha256(EMPTY_DOMAIN)]]
    for value in leaf_hashes:
        _digest_bytes(value, "leaf hash")
    levels = [list(leaf_hashes)]
    while len(levels[-1]) > 1:
        current = levels[-1]
        next_level = []
        for index in range(0, len(current), 2):
            right = current[index + 1] if index + 1 < len(current) else current[index]
            next_level.append(_parent(current[index], right))
        levels.append(next_level)
    return levels


def merkle_root(leaf_hashes: list[str]) -> str:
    return _levels(leaf_hashes)[-1][0]


def _timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not isinstance(value, str) or not value:
        raise CheckpointError("created_at must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CheckpointError("created_at must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise CheckpointError("created_at must include a timezone")
    return value


def build_checkpoint(
    records: list[dict[str, Any]],
    created_at: str | None = None,
    previous_checkpoint_digest: str | None = None,
) -> dict[str, Any]:
    if not isinstance(records, list):
        raise CheckpointError("records must be an array")
    if previous_checkpoint_digest is not None:
        _digest_bytes(previous_checkpoint_digest, "previous_checkpoint_digest")

    normalized = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise CheckpointError(f"record at index {index} must be an object")
        record_id = record.get("record_id")
        integrity = record.get("integrity")
        if not isinstance(integrity, dict):
            raise CheckpointError(f"record at index {index} has no integrity object")
        record_digest = integrity.get("digest")
        _record_identity(record_id, record_digest)
        if record_id in seen:
            raise CheckpointError(f"duplicate record_id: {record_id}")
        seen.add(record_id)
        normalized.append({"record_id": record_id, "record_digest": record_digest})

    normalized.sort(key=lambda item: item["record_id"])
    leaves = [
        {
            "record_id": item["record_id"],
            "record_digest": item["record_digest"],
            "leaf_hash": leaf_hash(item["record_id"], item["record_digest"]),
        }
        for item in normalized
    ]
    document = {
        "format": "ojek-merkle-checkpoint",
        "protocol_version": PROTOCOL_VERSION,
        "created_at": _timestamp(created_at),
        "clock_statement": "operator_asserted_unwitnessed",
        "hash_algorithm": "sha-256",
        "canonicalization": CANONICALIZATION,
        "tree_algorithm": TREE_ALGORITHM,
        "leaf_order": "record_id_ascending_unicode_codepoint",
        "odd_leaf_rule": "duplicate_last",
        "leaf_count": len(leaves),
        "previous_checkpoint_digest": previous_checkpoint_digest,
        "leaves": leaves,
        "merkle_root": merkle_root([item["leaf_hash"] for item in leaves]),
        "authentication": {"status": "unsigned", "signature": None, "key_id": None},
    }
    document["checkpoint_digest"] = sha256(canonical_bytes(document))
    return document


def verify_checkpoint(document: Any) -> dict[str, Any]:
    problems: list[str] = []
    if not isinstance(document, dict) or document.get("format") != "ojek-merkle-checkpoint":
        raise CheckpointError("not an OJEK Merkle checkpoint")

    payload = dict(document)
    supplied_digest = payload.pop("checkpoint_digest", None)
    try:
        if supplied_digest != sha256(canonical_bytes(payload)):
            problems.append("checkpoint digest mismatch")
    except CheckpointError as exc:
        problems.append(str(exc))

    if document.get("protocol_version") != PROTOCOL_VERSION:
        problems.append("unsupported protocol_version")
    if document.get("hash_algorithm") != "sha-256" or document.get("tree_algorithm") != TREE_ALGORITHM:
        problems.append("unsupported hash or tree algorithm")
    if document.get("canonicalization") != CANONICALIZATION:
        problems.append("unsupported canonicalization")
    if document.get("leaf_order") != "record_id_ascending_unicode_codepoint":
        problems.append("unsupported leaf ordering")
    if document.get("odd_leaf_rule") != "duplicate_last":
        problems.append("unsupported odd-leaf rule")

    leaves = document.get("leaves")
    if not isinstance(leaves, list):
        raise CheckpointError("leaves must be an array")
    identifiers = []
    computed = []
    for index, item in enumerate(leaves):
        if not isinstance(item, dict):
            problems.append(f"leaf {index}: entry must be an object")
            continue
        record_id = item.get("record_id")
        identifiers.append(record_id)
        try:
            expected = leaf_hash(record_id, item.get("record_digest"))
            if item.get("leaf_hash") != expected:
                problems.append(f"leaf {index}: leaf hash mismatch")
            computed.append(expected)
        except CheckpointError as exc:
            problems.append(f"leaf {index}: {exc}")

    if len(identifiers) != len(leaves):
        problems.append("malformed leaf entry")
    if not all(isinstance(value, str) and value for value in identifiers):
        problems.append("every leaf must contain a non-empty string record_id")
    elif identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
        problems.append("leaves are not uniquely sorted by record_id")
    leaf_count = document.get("leaf_count")
    if isinstance(leaf_count, bool) or not isinstance(leaf_count, int) or leaf_count != len(leaves):
        problems.append("leaf_count does not match leaves array")
    if len(computed) == len(leaves):
        try:
            if document.get("merkle_root") != merkle_root(computed):
                problems.append("Merkle root mismatch")
        except CheckpointError as exc:
            problems.append(str(exc))

    auth = document.get("authentication")
    if not isinstance(auth, dict) or auth != {"status": "unsigned", "signature": None, "key_id": None}:
        problems.append("v0.1 verifier only accepts explicitly unsigned checkpoints")
    try:
        _timestamp(document.get("created_at"))
    except CheckpointError as exc:
        problems.append(str(exc))
    previous = document.get("previous_checkpoint_digest")
    if previous is not None:
        try:
            _digest_bytes(previous, "previous_checkpoint_digest")
        except CheckpointError as exc:
            problems.append(str(exc))

    return {
        "valid": not problems,
        "leaf_count": len(leaves),
        "merkle_root": document.get("merkle_root"),
        "authentication": "unsigned",
        "problems": problems,
    }


def create_inclusion_proof(document: dict[str, Any], record_id: str) -> dict[str, Any]:
    if not verify_checkpoint(document)["valid"]:
        raise CheckpointError("cannot create proof from an invalid checkpoint")
    leaves = document["leaves"]
    identifiers = [item["record_id"] for item in leaves]
    if record_id not in identifiers:
        raise CheckpointError(f"record_id not found: {record_id}")

    index = identifiers.index(record_id)
    levels = _levels([item["leaf_hash"] for item in leaves])
    path = []
    cursor = index
    for level in levels[:-1]:
        sibling = cursor - 1 if cursor % 2 else cursor + 1
        if sibling >= len(level):
            sibling = cursor
        path.append({"side": "left" if sibling < cursor else "right", "hash": level[sibling]})
        cursor //= 2

    item = leaves[index]
    return {
        "format": "ojek-merkle-inclusion-proof",
        "protocol_version": PROTOCOL_VERSION,
        "record_id": record_id,
        "record_digest": item["record_digest"],
        "leaf_index": index,
        "leaf_count": len(leaves),
        "merkle_root": document["merkle_root"],
        "checkpoint_digest": document["checkpoint_digest"],
        "path": path,
    }


def verify_inclusion_proof(
    proof: Any,
    expected_root: str | None = None,
    expected_checkpoint_digest: str | None = None,
) -> bool:
    if not isinstance(proof, dict):
        return False
    if proof.get("format") != "ojek-merkle-inclusion-proof" or proof.get("protocol_version") != PROTOCOL_VERSION:
        return False
    try:
        current = leaf_hash(proof.get("record_id"), proof.get("record_digest"))
        index = proof.get("leaf_index")
        count = proof.get("leaf_count")
        if isinstance(index, bool) or not isinstance(index, int):
            return False
        if isinstance(count, bool) or not isinstance(count, int) or count < 1 or index < 0 or index >= count:
            return False
        _digest_bytes(proof.get("merkle_root"), "proof merkle_root")
        _digest_bytes(proof.get("checkpoint_digest"), "proof checkpoint_digest")
        if expected_root is not None and proof["merkle_root"] != expected_root:
            return False
        if expected_checkpoint_digest is not None and proof["checkpoint_digest"] != expected_checkpoint_digest:
            return False

        path = proof.get("path")
        if not isinstance(path, list):
            return False
        expected_levels = 0
        remaining = count
        while remaining > 1:
            expected_levels += 1
            remaining = (remaining + 1) // 2
        if len(path) != expected_levels:
            return False

        width = count
        for item in path:
            if not isinstance(item, dict):
                return False
            sibling = item.get("hash")
            _digest_bytes(sibling, "proof sibling hash")
            expected_side = "left" if index % 2 else "right"
            if item.get("side") != expected_side:
                return False
            if index % 2:
                current = _parent(sibling, current)
            else:
                if index + 1 >= width and sibling != current:
                    return False
                current = _parent(current, sibling)
            index //= 2
            width = (width + 1) // 2
        return width == 1 and current == proof["merkle_root"]
    except (KeyError, TypeError, ValueError, CheckpointError):
        return False
