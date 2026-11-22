"""OJEK v0.2 append-only transparency log primitives.

This module is deliberately separate from checkpoints.py: v0.1 snapshot
checkpoints retain their original tree algorithm and wire format.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Sequence

PROTOCOL = "ojek-transparency-log-v0.2"
ENTRY_PROTOCOL = PROTOCOL
TREE_HEAD_PROTOCOL = PROTOCOL
PROOF_PROTOCOL = "ojek-consistency-proof-v0.2"
TREE_ALGORITHM = "rfc9162-merkle-tree-sha256"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LOG_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}$")
_MEDIA_TYPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*/[A-Za-z0-9][A-Za-z0-9.+-]*$")
_ENTRY_TYPES = {"record-reference", "checkpoint-reference", "policy-change"}
_ENTRY_FIELDS = {
    "protocol", "log_id", "leaf_index", "entry_type", "payload_digest",
    "payload_media_type", "created_at",
}
_TREE_HEAD_FIELDS = {
    "protocol", "log_id", "tree_size", "root_hash", "issued_at",
    "hash_algorithm", "tree_head_digest",
}


class TransparencyLogError(ValueError):
    """Invalid v0.2 log entry, tree head, or proof."""


def canonical_bytes(value: Any) -> bytes:
    """Encode JSON using OJEK's explicitly versioned ojek-json-v1 rules."""
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise TransparencyLogError(f"value cannot be canonically encoded: {exc}") from exc



def strict_json_loads(source: str) -> Any:
    """Parse JSON while rejecting duplicate object members and non-JSON constants."""
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TransparencyLogError(f"duplicate JSON object member: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise TransparencyLogError(f"non-standard JSON constant is not permitted: {value}")

    try:
        return json.loads(source, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise TransparencyLogError(f"invalid JSON: {exc}") from exc


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _hex_digest(value: Any, field: str) -> bytes:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise TransparencyLogError(f"{field} must be 64 lowercase hexadecimal characters")
    return bytes.fromhex(value)


def _log_id(value: Any) -> str:
    if not isinstance(value, str) or not _LOG_ID_RE.fullmatch(value):
        raise TransparencyLogError("log_id must be a stable ASCII identifier (1-255 characters)")
    return value


def _utc_timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value):
        raise TransparencyLogError(f"{field} must be an RFC 3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TransparencyLogError(f"{field} must be a valid RFC 3339 UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise TransparencyLogError(f"{field} must use UTC")
    return value


def build_log_entry(
    log_id: str,
    leaf_index: int,
    entry_type: str,
    payload_digest: str,
    payload_media_type: str,
    created_at: str,
) -> dict[str, Any]:
    """Build and validate one ordered, metadata-minimal log entry."""
    entry = {
        "protocol": ENTRY_PROTOCOL,
        "log_id": log_id,
        "leaf_index": leaf_index,
        "entry_type": entry_type,
        "payload_digest": payload_digest,
        "payload_media_type": payload_media_type,
        "created_at": created_at,
    }
    validate_log_entry(entry)
    return entry


def validate_log_entry(entry: Any, expected_log_id: str | None = None, expected_index: int | None = None) -> dict[str, Any]:
    if not isinstance(entry, dict) or set(entry) != _ENTRY_FIELDS:
        raise TransparencyLogError("entry must contain exactly the defined v0.2 fields")
    if entry["protocol"] != ENTRY_PROTOCOL:
        raise TransparencyLogError("unsupported entry protocol")
    log_id = _log_id(entry["log_id"])
    if expected_log_id is not None and log_id != expected_log_id:
        raise TransparencyLogError("entry log_id does not match expected log")
    index = entry["leaf_index"]
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise TransparencyLogError("leaf_index must be a non-negative integer")
    if expected_index is not None and index != expected_index:
        raise TransparencyLogError("leaf_index is not contiguous with the expected sequence")
    if entry["entry_type"] not in _ENTRY_TYPES:
        raise TransparencyLogError("unsupported entry_type")
    _hex_digest(entry["payload_digest"], "payload_digest")
    media_type = entry["payload_media_type"]
    if not isinstance(media_type, str) or len(media_type) > 255 or not _MEDIA_TYPE_RE.fullmatch(media_type):
        raise TransparencyLogError("payload_media_type must be a valid type/subtype media type")
    _utc_timestamp(entry["created_at"], "created_at")
    return entry


def entry_bytes(entry: dict[str, Any]) -> bytes:
    validate_log_entry(entry)
    return canonical_bytes(entry)


def leaf_hash_v2(entry: bytes) -> bytes:
    if not isinstance(entry, bytes):
        raise TransparencyLogError("leaf input must be bytes")
    return _hash(b"\x00" + entry)


def _largest_power_of_two_less_than(n: int) -> int:
    if n < 2:
        raise TransparencyLogError("tree split requires at least two leaves")
    return 1 << ((n - 1).bit_length() - 1)


def _mth(leaves: Sequence[bytes]) -> bytes:
    n = len(leaves)
    if n == 0:
        return _hash(b"")
    if n == 1:
        return leaf_hash_v2(leaves[0])
    k = _largest_power_of_two_less_than(n)
    return _hash(b"\x01" + _mth(leaves[:k]) + _mth(leaves[k:]))


def merkle_root_v2(entries: Sequence[bytes]) -> str:
    """Return the RFC 9162-style SHA-256 root for ordered entry byte strings."""
    if isinstance(entries, (str, bytes, bytearray)):
        raise TransparencyLogError("entries must be a sequence of byte strings")
    if not all(isinstance(entry, bytes) for entry in entries):
        raise TransparencyLogError("every log entry must be supplied as bytes")
    return _mth(entries).hex()


def _subproof(old_size: int, leaves: Sequence[bytes], complete_subtree: bool) -> list[bytes]:
    n = len(leaves)
    if old_size == n:
        return [] if complete_subtree else [_mth(leaves)]
    k = _largest_power_of_two_less_than(n)
    if old_size <= k:
        return _subproof(old_size, leaves[:k], complete_subtree) + [_mth(leaves[k:])]
    return _subproof(old_size - k, leaves[k:], False) + [_mth(leaves[:k])]


def generate_consistency_proof_v2(entries: Sequence[bytes], old_size: int) -> list[str]:
    """Generate an RFC 9162 consistency proof from old_size to len(entries)."""
    if isinstance(old_size, bool) or not isinstance(old_size, int):
        raise TransparencyLogError("old_size must be an integer")
    if isinstance(entries, (str, bytes, bytearray)) or not all(isinstance(item, bytes) for item in entries):
        raise TransparencyLogError("entries must be a sequence of byte strings")
    if old_size < 0 or old_size > len(entries):
        raise TransparencyLogError("old_size must be between zero and the new tree size")
    if old_size == 0 or old_size == len(entries):
        return []
    return [node.hex() for node in _subproof(old_size, entries, True)]


def verify_consistency_proof_v2(
    old_size: int,
    new_size: int,
    old_root: str,
    new_root: str,
    proof: Sequence[str],
) -> bool:
    """Verify that the old tree is an exact prefix of the new tree."""
    try:
        if (isinstance(old_size, bool) or not isinstance(old_size, int)
                or isinstance(new_size, bool) or not isinstance(new_size, int)
                or old_size < 0 or new_size < old_size):
            return False
        first_hash = _hex_digest(old_root, "old_root")
        second_hash = _hex_digest(new_root, "new_root")
        if not isinstance(proof, list):
            return False
        proof_nodes = [_hex_digest(item, "proof node") for item in proof]
        empty_root = _hash(b"")
        if old_size == 0:
            return (first_hash == empty_root and not proof_nodes
                    and (new_size > 0 or second_hash == empty_root))
        if old_size == new_size:
            return first_hash == second_hash and not proof_nodes
        if new_size == 0 or not proof_nodes:
            return False

        fn = old_size - 1
        sn = new_size - 1
        while fn & 1:
            fn >>= 1
            sn >>= 1

        cursor = 0
        if fn == 0:
            fr = sr = first_hash
        else:
            fr = sr = proof_nodes[0]
            cursor = 1

        while cursor < len(proof_nodes):
            if sn == 0:
                return False
            node = proof_nodes[cursor]
            if (fn & 1) == 1 or fn == sn:
                fr = _hash(b"\x01" + node + fr)
                sr = _hash(b"\x01" + node + sr)
                while fn != 0 and (fn & 1) == 0:
                    fn >>= 1
                    sn >>= 1
            else:
                sr = _hash(b"\x01" + sr + node)
            fn >>= 1
            sn >>= 1
            cursor += 1

        return fr == first_hash and sr == second_hash and sn == 0
    except (TypeError, ValueError, OverflowError, TransparencyLogError):
        return False


def build_tree_head(log_id: str, entries: Sequence[bytes], issued_at: str) -> dict[str, Any]:
    """Create an unsigned tree head with a frozen digest preimage.

    tree_head_digest = SHA-256(canonical UTF-8 JSON of the six fields preceding
    tree_head_digest; no digest/signature field is included in that preimage).
    """
    _log_id(log_id)
    _utc_timestamp(issued_at, "issued_at")
    root = merkle_root_v2(entries)
    head = {
        "protocol": TREE_HEAD_PROTOCOL,
        "log_id": log_id,
        "tree_size": len(entries),
        "root_hash": root,
        "issued_at": issued_at,
        "hash_algorithm": "sha-256",
    }
    head["tree_head_digest"] = _hash(canonical_bytes(head)).hex()
    return head


def verify_tree_head(head: Any) -> bool:
    try:
        if not isinstance(head, dict) or set(head) != _TREE_HEAD_FIELDS:
            return False
        if head["protocol"] != TREE_HEAD_PROTOCOL or head["hash_algorithm"] != "sha-256":
            return False
        _log_id(head["log_id"])
        size = head["tree_size"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            return False
        root_hash = _hex_digest(head["root_hash"], "root_hash")
        if size == 0 and root_hash != _hash(b""):
            return False
        _utc_timestamp(head["issued_at"], "issued_at")
        supplied = _hex_digest(head["tree_head_digest"], "tree_head_digest")
        payload = {key: head[key] for key in (
            "protocol", "log_id", "tree_size", "root_hash", "issued_at", "hash_algorithm"
        )}
        return supplied == _hash(canonical_bytes(payload))
    except (KeyError, TypeError, ValueError, TransparencyLogError):
        return False


def build_consistency_proof_document(
    log_id: str,
    old_head: dict[str, Any],
    new_head: dict[str, Any],
    proof: Sequence[str],
) -> dict[str, Any]:
    if not verify_tree_head(old_head) or not verify_tree_head(new_head):
        raise TransparencyLogError("both tree heads must be valid")
    if old_head["log_id"] != log_id or new_head["log_id"] != log_id:
        raise TransparencyLogError("tree heads do not belong to the requested log")
    if old_head["tree_size"] > new_head["tree_size"]:
        raise TransparencyLogError("new tree head cannot be smaller than old tree head")
    if not verify_consistency_proof_v2(
        old_head["tree_size"], new_head["tree_size"],
        old_head["root_hash"], new_head["root_hash"], list(proof),
    ):
        raise TransparencyLogError("consistency proof does not validate against the supplied tree heads")
    return {
        "protocol": PROOF_PROTOCOL,
        "log_id": log_id,
        "old_tree_size": old_head["tree_size"],
        "new_tree_size": new_head["tree_size"],
        "old_root": old_head["root_hash"],
        "new_root": new_head["root_hash"],
        "proof": list(proof),
    }


def verify_consistency_proof_document(old_head: Any, new_head: Any, document: Any) -> bool:
    if not verify_tree_head(old_head) or not verify_tree_head(new_head):
        return False
    if not isinstance(document, dict) or set(document) != {
        "protocol", "log_id", "old_tree_size", "new_tree_size",
        "old_root", "new_root", "proof",
    }:
        return False
    if document.get("protocol") != PROOF_PROTOCOL:
        return False
    if document.get("log_id") != old_head["log_id"] or document.get("log_id") != new_head["log_id"]:
        return False
    old_size = document.get("old_tree_size")
    new_size = document.get("new_tree_size")
    if (isinstance(old_size, bool) or not isinstance(old_size, int)
            or isinstance(new_size, bool) or not isinstance(new_size, int)
            or old_size != old_head["tree_size"] or new_size != new_head["tree_size"]):
        return False
    if document.get("old_root") != old_head["root_hash"] or document.get("new_root") != new_head["root_hash"]:
        return False
    return verify_consistency_proof_v2(
        old_head["tree_size"], new_head["tree_size"],
        old_head["root_hash"], new_head["root_hash"], document.get("proof"),
    )
