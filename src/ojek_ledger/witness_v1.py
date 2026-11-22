"""Offline Ed25519 witness statements and split-view evidence for OJEK."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .transparency_v2 import (
    TransparencyLogError,
    canonical_bytes,
    verify_consistency_proof_document,
    verify_tree_head,
)

KEY_PROTOCOL = "ojek-witness-key-v0.1"
STATEMENT_PROTOCOL = "ojek-witness-statement-v0.1"
TRANSITION_PROTOCOL = "ojek-witness-key-transition-v0.1"
CONFLICT_PROTOCOL = "ojek-witness-conflict-bundle-v0.1"
_KEY_DOMAIN = b"OJEK-WITNESS-KEY-v0.1\x00"
_STATEMENT_DOMAIN = b"OJEK-WITNESS-STATEMENT-v0.1\x00"
_STATEMENT_DIGEST_DOMAIN = b"OJEK-WITNESS-STATEMENT-DIGEST-v0.1\x00"
_TRANSITION_DOMAIN = b"OJEK-WITNESS-KEY-TRANSITION-v0.1\x00"
_PROOF_DIGEST_DOMAIN = b"OJEK-CONSISTENCY-PROOF-DIGEST-v0.2\x00"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX128 = re.compile(r"^[0-9a-f]{128}$")
_MAX_SAFE_INTEGER = (1 << 53) - 1
# Bound pairwise conflict analysis to at most 8,128 comparisons per bundle.
MAX_CONFLICT_BUNDLE_OBSERVATIONS = 128
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_KEY_FIELDS = {"protocol", "witness_id", "key_id", "signature_algorithm", "public_key", "created_at"}
_STATEMENT_FIELDS = {
    "protocol", "witness_id", "key_id", "log_id", "tree_size", "root_hash",
    "tree_head_digest", "observed_at", "previous_statement_digest",
    "consistency_status", "consistency_from_tree_size", "consistency_proof_digest",
    "key_transition_digest", "policy_id", "signature_algorithm", "signature",
}
_TRANSITION_FIELDS = {
    "protocol", "witness_id", "previous_key_id", "new_key_id", "created_at",
    "signature_algorithm", "previous_key_signature", "new_key_signature",
}
_STATUSES = {"first_observation", "verified", "failed", "unavailable"}


class WitnessProtocolError(ValueError):
    """Invalid witness key, statement, transition, or conflict bundle."""


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise WitnessProtocolError(f"{field} must be a stable ASCII identifier")
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        raise WitnessProtocolError(f"{field} must be an RFC 3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WitnessProtocolError(f"{field} is not a valid UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise WitnessProtocolError(f"{field} must use UTC")
    return value


def _digest(value: Any, field: str) -> bytes:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise WitnessProtocolError(f"{field} must be 64 lowercase hexadecimal characters")
    return bytes.fromhex(value)


def _public_key_bytes(value: Any) -> bytes:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise WitnessProtocolError("public_key must be a 32-byte lowercase hexadecimal Ed25519 key")
    return bytes.fromhex(value)


def _key_id(public_key: bytes) -> str:
    return hashlib.sha256(_KEY_DOMAIN + public_key).hexdigest()


def build_witness_key_document(witness_id: str, public_key: bytes, created_at: str) -> dict[str, Any]:
    _identifier(witness_id, "witness_id")
    _timestamp(created_at, "created_at")
    if not isinstance(public_key, bytes) or len(public_key) != 32:
        raise WitnessProtocolError("Ed25519 public key must be exactly 32 bytes")
    return {
        "protocol": KEY_PROTOCOL,
        "witness_id": witness_id,
        "key_id": _key_id(public_key),
        "signature_algorithm": "ed25519",
        "public_key": public_key.hex(),
        "created_at": created_at,
    }


def generate_witness_keypair(witness_id: str, created_at: str) -> tuple[bytes, dict[str, Any]]:
    """Generate an Ed25519 keypair in memory; caller must protect private_key_bytes."""
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_bytes, build_witness_key_document(witness_id, public_bytes, created_at)


def verify_witness_key_document(document: Any) -> bool:
    try:
        if not isinstance(document, dict) or set(document) != _KEY_FIELDS:
            return False
        if document["protocol"] != KEY_PROTOCOL or document["signature_algorithm"] != "ed25519":
            return False
        _identifier(document["witness_id"], "witness_id")
        _timestamp(document["created_at"], "created_at")
        public_key = _public_key_bytes(document["public_key"])
        return document["key_id"] == _key_id(public_key)
    except (KeyError, TypeError, ValueError, WitnessProtocolError):
        return False


def witness_statement_digest(statement: dict[str, Any]) -> str:
    return hashlib.sha256(_STATEMENT_DIGEST_DOMAIN + canonical_bytes(statement)).hexdigest()


def consistency_proof_digest(proof_document: dict[str, Any]) -> str:
    return hashlib.sha256(_PROOF_DIGEST_DOMAIN + canonical_bytes(proof_document)).hexdigest()


def _transition_payload(document: dict[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in (
        "protocol", "witness_id", "previous_key_id", "new_key_id",
        "created_at", "signature_algorithm",
    )}


def build_key_transition(
    previous_key_document: dict[str, Any],
    new_key_document: dict[str, Any],
    previous_private_key: bytes | Ed25519PrivateKey,
    new_private_key: bytes | Ed25519PrivateKey,
    created_at: str,
) -> dict[str, Any]:
    if not verify_witness_key_document(previous_key_document) or not verify_witness_key_document(new_key_document):
        raise WitnessProtocolError("both witness key documents must be valid")
    if previous_key_document["witness_id"] != new_key_document["witness_id"]:
        raise WitnessProtocolError("key transition must preserve witness_id")
    if previous_key_document["key_id"] == new_key_document["key_id"]:
        raise WitnessProtocolError("key transition requires a different new key")
    _timestamp(created_at, "created_at")
    transition_time = datetime.fromisoformat(created_at[:-1] + "+00:00")
    previous_created = datetime.fromisoformat(previous_key_document["created_at"][:-1] + "+00:00")
    new_created = datetime.fromisoformat(new_key_document["created_at"][:-1] + "+00:00")
    if transition_time < previous_created or transition_time < new_created:
        raise WitnessProtocolError("key transition time must fall between the old and new key creation assertions")
    document = {
        "protocol": TRANSITION_PROTOCOL,
        "witness_id": previous_key_document["witness_id"],
        "previous_key_id": previous_key_document["key_id"],
        "new_key_id": new_key_document["key_id"],
        "created_at": created_at,
        "signature_algorithm": "ed25519",
        "previous_key_signature": "",
        "new_key_signature": "",
    }
    preimage = _TRANSITION_DOMAIN + canonical_bytes(_transition_payload(document))
    old_private = _load_private_key(previous_private_key)
    new_private = _load_private_key(new_private_key)
    _require_private_matches(old_private, previous_key_document)
    _require_private_matches(new_private, new_key_document)
    document["previous_key_signature"] = old_private.sign(preimage).hex()
    document["new_key_signature"] = new_private.sign(preimage).hex()
    return document


def verify_key_transition(
    document: Any,
    previous_key_document: Any,
    new_key_document: Any,
) -> bool:
    try:
        if not isinstance(document, dict) or set(document) != _TRANSITION_FIELDS:
            return False
        if not verify_witness_key_document(previous_key_document) or not verify_witness_key_document(new_key_document):
            return False
        if document["protocol"] != TRANSITION_PROTOCOL or document["signature_algorithm"] != "ed25519":
            return False
        witness_id = _identifier(document["witness_id"], "witness_id")
        _timestamp(document["created_at"], "created_at")
        if witness_id != previous_key_document["witness_id"] or witness_id != new_key_document["witness_id"]:
            return False
        if document["previous_key_id"] != previous_key_document["key_id"]:
            return False
        if document["new_key_id"] != new_key_document["key_id"]:
            return False
        if document["previous_key_id"] == document["new_key_id"]:
            return False
        transition_time = datetime.fromisoformat(document["created_at"][:-1] + "+00:00")
        previous_created = datetime.fromisoformat(previous_key_document["created_at"][:-1] + "+00:00")
        new_created = datetime.fromisoformat(new_key_document["created_at"][:-1] + "+00:00")
        if not previous_created <= transition_time <= new_created:
            return False
        payload = _transition_payload(document)
        preimage = _TRANSITION_DOMAIN + canonical_bytes(payload)
        old_public = Ed25519PublicKey.from_public_bytes(_public_key_bytes(previous_key_document["public_key"]))
        new_public = Ed25519PublicKey.from_public_bytes(_public_key_bytes(new_key_document["public_key"]))
        old_signature = document["previous_key_signature"]
        new_signature = document["new_key_signature"]
        if not isinstance(old_signature, str) or not _HEX128.fullmatch(old_signature):
            return False
        if not isinstance(new_signature, str) or not _HEX128.fullmatch(new_signature):
            return False
        old_public.verify(bytes.fromhex(old_signature), preimage)
        new_public.verify(bytes.fromhex(new_signature), preimage)
        return True
    except (KeyError, TypeError, ValueError, InvalidSignature, WitnessProtocolError):
        return False


def _load_private_key(value: bytes | Ed25519PrivateKey) -> Ed25519PrivateKey:
    if isinstance(value, Ed25519PrivateKey):
        return value
    if isinstance(value, bytes) and len(value) == 32:
        return Ed25519PrivateKey.from_private_bytes(value)
    raise WitnessProtocolError("private key must be an Ed25519PrivateKey or 32 raw bytes")


def _require_private_matches(private_key: Ed25519PrivateKey, key_document: dict[str, Any]) -> None:
    actual = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if actual != _public_key_bytes(key_document["public_key"]):
        raise WitnessProtocolError("private key does not match the supplied public key document")


def _statement_payload(statement: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in statement.items() if key != "signature"}


def _verify_signature_and_head(
    statement: Any,
    key_document: Any,
    tree_head: Any,
    revoked_key_ids: set[str] | None = None,
) -> None:
    if not isinstance(statement, dict) or set(statement) != _STATEMENT_FIELDS:
        raise WitnessProtocolError("witness statement has missing or unknown fields")
    if not verify_witness_key_document(key_document):
        raise WitnessProtocolError("witness public-key document is invalid")
    if not verify_tree_head(tree_head):
        raise WitnessProtocolError("observed v0.2 tree head is invalid")
    if statement["protocol"] != STATEMENT_PROTOCOL or statement["signature_algorithm"] != "ed25519":
        raise WitnessProtocolError("unsupported witness statement protocol or signature algorithm")
    witness_id = _identifier(statement["witness_id"], "witness_id")
    log_id = _identifier(statement["log_id"], "log_id")
    _timestamp(statement["observed_at"], "observed_at")
    if witness_id != key_document["witness_id"] or statement["key_id"] != key_document["key_id"]:
        raise WitnessProtocolError("statement identity does not match its public-key document")
    if revoked_key_ids and statement["key_id"] in revoked_key_ids:
        raise WitnessProtocolError("statement uses a key revoked by the verifier's policy")
    size = statement["tree_size"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0 or size > _MAX_SAFE_INTEGER:
        raise WitnessProtocolError("tree_size must be a non-negative integer")
    _digest(statement["root_hash"], "root_hash")
    _digest(statement["tree_head_digest"], "tree_head_digest")
    if (tree_head["log_id"] != log_id or tree_head["tree_size"] != size
            or tree_head["root_hash"] != statement["root_hash"]
            or tree_head["tree_head_digest"] != statement["tree_head_digest"]):
        raise WitnessProtocolError("witness statement is not bound to the supplied tree head")
    policy_id = statement["policy_id"]
    if not isinstance(policy_id, str) or not policy_id.strip() or len(policy_id) > 128:
        raise WitnessProtocolError("policy_id must be a non-empty string of at most 128 characters")
    status = statement["consistency_status"]
    if not isinstance(status, str) or status not in _STATUSES:
        raise WitnessProtocolError("unsupported consistency_status")
    previous_digest = statement["previous_statement_digest"]
    from_size = statement["consistency_from_tree_size"]
    proof_digest = statement["consistency_proof_digest"]
    transition_digest = statement["key_transition_digest"]
    if status == "first_observation":
        if any(value is not None for value in (previous_digest, from_size, proof_digest, transition_digest)):
            raise WitnessProtocolError("first observation contains prior-chain fields")
    else:
        _digest(previous_digest, "previous_statement_digest")
        if isinstance(from_size, bool) or not isinstance(from_size, int) or from_size < 0 or from_size > _MAX_SAFE_INTEGER:
            raise WitnessProtocolError("consistency_from_tree_size must be a non-negative integer")
        if proof_digest is not None:
            _digest(proof_digest, "consistency_proof_digest")
        if transition_digest is not None:
            _digest(transition_digest, "key_transition_digest")
    if datetime.fromisoformat(statement["observed_at"][:-1] + "+00:00") < datetime.fromisoformat(key_document["created_at"][:-1] + "+00:00"):
        raise WitnessProtocolError("statement predates the signing key document")
    signature = statement["signature"]
    if not isinstance(signature, str) or not _HEX128.fullmatch(signature):
        raise WitnessProtocolError("signature must be 128 lowercase hexadecimal characters")
    public_key = Ed25519PublicKey.from_public_bytes(_public_key_bytes(key_document["public_key"]))
    public_key.verify(bytes.fromhex(signature), _STATEMENT_DOMAIN + canonical_bytes(_statement_payload(statement)))


def sign_witness_statement(
    key_document: dict[str, Any],
    private_key: bytes | Ed25519PrivateKey,
    tree_head: dict[str, Any],
    observed_at: str,
    policy_id: str,
    previous_statement: dict[str, Any] | None = None,
    previous_key_document: dict[str, Any] | None = None,
    previous_tree_head: dict[str, Any] | None = None,
    consistency_proof: dict[str, Any] | None = None,
    key_transition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not verify_witness_key_document(key_document):
        raise WitnessProtocolError("current public-key document is invalid")
    if not verify_tree_head(tree_head):
        raise WitnessProtocolError("current tree head is invalid")
    _timestamp(observed_at, "observed_at")
    if datetime.fromisoformat(observed_at[:-1] + "+00:00") < datetime.fromisoformat(key_document["created_at"][:-1] + "+00:00"):
        raise WitnessProtocolError("observation predates the current signing key")
    if not isinstance(policy_id, str) or not policy_id.strip() or len(policy_id) > 128:
        raise WitnessProtocolError("policy_id must be a non-empty string of at most 128 characters")
    private = _load_private_key(private_key)
    _require_private_matches(private, key_document)

    previous_digest = None
    previous_size = None
    proof_digest = None
    transition_digest = None
    if previous_statement is None:
        if any(value is not None for value in (
            previous_key_document, previous_tree_head, consistency_proof, key_transition
        )):
            raise WitnessProtocolError("first observation cannot include prior statement context")
        status = "first_observation"
    else:
        if previous_key_document is None or previous_tree_head is None:
            raise WitnessProtocolError("previous statement requires its key document and tree head")
        _verify_signature_and_head(previous_statement, previous_key_document, previous_tree_head)
        if previous_statement["witness_id"] != key_document["witness_id"]:
            raise WitnessProtocolError("previous statement belongs to a different witness")
        if previous_tree_head["log_id"] != tree_head["log_id"]:
            raise WitnessProtocolError("witness continuity cannot cross log identities")
        previous_digest = witness_statement_digest(previous_statement)
        previous_size = previous_tree_head["tree_size"]
        if previous_key_document["key_id"] != key_document["key_id"]:
            if key_transition is None or not verify_key_transition(
                key_transition, previous_key_document, key_document
            ):
                raise WitnessProtocolError("key rotation requires a valid dual-signed transition")
            transition_time = datetime.fromisoformat(key_transition["created_at"][:-1] + "+00:00")
            previous_observed = datetime.fromisoformat(previous_statement["observed_at"][:-1] + "+00:00")
            current_observed = datetime.fromisoformat(observed_at[:-1] + "+00:00")
            if not previous_observed <= transition_time <= current_observed:
                raise WitnessProtocolError("key transition must occur between the linked observations")
            transition_digest = hashlib.sha256(
                _TRANSITION_DOMAIN + canonical_bytes(key_transition)
            ).hexdigest()
        elif key_transition is not None:
            raise WitnessProtocolError("key transition supplied when the key did not change")

        if consistency_proof is None:
            rollback_or_fork = (
                tree_head["tree_size"] < previous_tree_head["tree_size"]
                or (
                    tree_head["tree_size"] == previous_tree_head["tree_size"]
                    and tree_head["root_hash"] != previous_tree_head["root_hash"]
                )
            )
            status = "failed" if rollback_or_fork else "unavailable"
        else:
            proof_digest = consistency_proof_digest(consistency_proof)
            status = "verified" if verify_consistency_proof_document(
                previous_tree_head, tree_head, consistency_proof
            ) else "failed"

    statement = {
        "protocol": STATEMENT_PROTOCOL,
        "witness_id": key_document["witness_id"],
        "key_id": key_document["key_id"],
        "log_id": tree_head["log_id"],
        "tree_size": tree_head["tree_size"],
        "root_hash": tree_head["root_hash"],
        "tree_head_digest": tree_head["tree_head_digest"],
        "observed_at": observed_at,
        "previous_statement_digest": previous_digest,
        "consistency_status": status,
        "consistency_from_tree_size": previous_size,
        "consistency_proof_digest": proof_digest,
        "key_transition_digest": transition_digest,
        "policy_id": policy_id,
        "signature_algorithm": "ed25519",
        "signature": "",
    }
    statement["signature"] = private.sign(
        _STATEMENT_DOMAIN + canonical_bytes(_statement_payload(statement))
    ).hex()
    return statement


def verify_witness_statement(
    statement: Any,
    key_document: Any,
    tree_head: Any,
    previous_statement: Any = None,
    previous_key_document: Any = None,
    previous_tree_head: Any = None,
    consistency_proof: Any = None,
    key_transition: Any = None,
    revoked_key_ids: set[str] | None = None,
) -> dict[str, Any]:
    try:
        _verify_signature_and_head(statement, key_document, tree_head, revoked_key_ids)
        status = statement["consistency_status"]
        if status not in _STATUSES:
            raise WitnessProtocolError("unsupported consistency_status")
        if status == "first_observation":
            if any(statement[field] is not None for field in (
                "previous_statement_digest", "consistency_from_tree_size",
                "consistency_proof_digest", "key_transition_digest",
            )):
                raise WitnessProtocolError("first observation must not claim prior continuity")
            if any(value is not None for value in (
                previous_statement, previous_key_document, previous_tree_head,
                consistency_proof, key_transition,
            )):
                raise WitnessProtocolError("first observation must not include prior artifacts")
            return {
                "valid": True, "continuity_status": status,
                "continuity_verified": False, "witness_id": statement["witness_id"],
                "log_id": statement["log_id"], "tree_size": statement["tree_size"],
                "root_hash": statement["root_hash"], "errors": [],
            }

        if previous_statement is None or previous_key_document is None or previous_tree_head is None:
            raise WitnessProtocolError("statement requires previous statement, key, and tree head")
        _verify_signature_and_head(
            previous_statement, previous_key_document, previous_tree_head, revoked_key_ids
        )
        if previous_statement["witness_id"] != statement["witness_id"]:
            raise WitnessProtocolError("previous statement belongs to a different witness")
        if previous_tree_head["log_id"] != tree_head["log_id"]:
            raise WitnessProtocolError("previous tree head belongs to a different log")
        if statement["previous_statement_digest"] != witness_statement_digest(previous_statement):
            raise WitnessProtocolError("previous_statement_digest does not match supplied statement")
        prior_size = previous_tree_head["tree_size"]
        from_size = statement["consistency_from_tree_size"]
        if isinstance(from_size, bool) or not isinstance(from_size, int) or from_size < 0 or from_size > _MAX_SAFE_INTEGER or from_size != prior_size:
            raise WitnessProtocolError("consistency_from_tree_size does not match previous tree head")

        if previous_key_document["key_id"] != key_document["key_id"]:
            if not verify_key_transition(key_transition, previous_key_document, key_document):
                raise WitnessProtocolError("missing or invalid dual-signed key transition")
            transition_time = datetime.fromisoformat(key_transition["created_at"][:-1] + "+00:00")
            previous_observed = datetime.fromisoformat(previous_statement["observed_at"][:-1] + "+00:00")
            current_observed = datetime.fromisoformat(statement["observed_at"][:-1] + "+00:00")
            if not previous_observed <= transition_time <= current_observed:
                raise WitnessProtocolError("key transition must occur between the linked observations")
            expected_transition_digest = hashlib.sha256(
                _TRANSITION_DOMAIN + canonical_bytes(key_transition)
            ).hexdigest()
            if statement["key_transition_digest"] != expected_transition_digest:
                raise WitnessProtocolError("key_transition_digest does not match supplied transition")
        elif key_transition is not None or statement["key_transition_digest"] is not None:
            raise WitnessProtocolError("unexpected key transition")

        if status == "unavailable":
            if consistency_proof is not None or statement["consistency_proof_digest"] is not None:
                raise WitnessProtocolError("unavailable status must not claim a proof artifact")
            if (tree_head["tree_size"] < prior_size
                    or (tree_head["tree_size"] == prior_size
                        and tree_head["root_hash"] != previous_tree_head["root_hash"])):
                raise WitnessProtocolError("rollback or same-size root conflict cannot be labeled unavailable")
            continuity_verified = False
        elif consistency_proof is None:
            if statement["consistency_proof_digest"] is not None:
                raise WitnessProtocolError("missing consistency proof does not match its digest field")
            if status != "failed" or not (
                tree_head["tree_size"] < prior_size
                or (tree_head["tree_size"] == prior_size
                    and tree_head["root_hash"] != previous_tree_head["root_hash"])
            ):
                raise WitnessProtocolError("failed status without a proof requires a rollback or same-size root conflict")
            continuity_verified = False
        else:
            if not isinstance(consistency_proof, dict):
                raise WitnessProtocolError("consistency proof must be a JSON object")
            supplied_proof_digest = consistency_proof_digest(consistency_proof)
            if statement["consistency_proof_digest"] != supplied_proof_digest:
                raise WitnessProtocolError("consistency_proof_digest does not match supplied proof")
            proof_valid = verify_consistency_proof_document(
                previous_tree_head, tree_head, consistency_proof
            )
            if status == "verified" and not proof_valid:
                raise WitnessProtocolError("statement claims verified continuity but proof is invalid")
            if status == "failed" and proof_valid:
                raise WitnessProtocolError("statement reports failed continuity but proof verifies")
            continuity_verified = status == "verified"

        return {
            "valid": True, "continuity_status": status,
            "continuity_verified": continuity_verified,
            "witness_id": statement["witness_id"], "log_id": statement["log_id"],
            "tree_size": statement["tree_size"], "root_hash": statement["root_hash"],
            "errors": [],
        }
    except (KeyError, TypeError, ValueError, InvalidSignature, WitnessProtocolError, TransparencyLogError) as exc:
        return {"valid": False, "continuity_status": "invalid", "continuity_verified": False, "errors": [str(exc)]}


def build_conflict_bundle(observations: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(observations, list) or len(observations) < 2:
        raise WitnessProtocolError("conflict bundle requires at least two observations")
    if len(observations) > MAX_CONFLICT_BUNDLE_OBSERVATIONS:
        raise WitnessProtocolError(
            f"conflict bundle exceeds the limit of {MAX_CONFLICT_BUNDLE_OBSERVATIONS} observations"
        )
    return {"protocol": CONFLICT_PROTOCOL, "observations": observations}


def verify_conflict_bundle(
    bundle: Any,
    revoked_key_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(bundle, dict) or set(bundle) != {"protocol", "observations"}:
        return {"valid": False, "conflict_detected": False, "errors": ["invalid conflict bundle shape"], "conflicts": []}
    if bundle.get("protocol") != CONFLICT_PROTOCOL or not isinstance(bundle.get("observations"), list) or len(bundle["observations"]) < 2:
        return {"valid": False, "conflict_detected": False, "errors": ["unsupported conflict bundle"], "conflicts": []}
    if len(bundle["observations"]) > MAX_CONFLICT_BUNDLE_OBSERVATIONS:
        return {
            "valid": False,
            "conflict_detected": False,
            "errors": [
                f"conflict bundle exceeds the limit of {MAX_CONFLICT_BUNDLE_OBSERVATIONS} observations"
            ],
            "conflicts": [],
        }

    results = []
    errors = []
    normalized = []
    allowed = {
        "statement", "key_document", "tree_head", "previous_statement",
        "previous_key_document", "previous_tree_head", "consistency_proof", "key_transition",
    }
    for index, observation in enumerate(bundle["observations"]):
        if not isinstance(observation, dict) or not {"statement", "key_document", "tree_head"}.issubset(observation) or not set(observation).issubset(allowed):
            result = {"valid": False, "errors": ["invalid observation object"]}
            normalized.append(None)
        else:
            result = verify_witness_statement(
                observation["statement"], observation["key_document"], observation["tree_head"],
                observation.get("previous_statement"), observation.get("previous_key_document"),
                observation.get("previous_tree_head"), observation.get("consistency_proof"),
                observation.get("key_transition"), revoked_key_ids,
            )
            normalized.append(observation if result["valid"] else None)
        results.append(result)
        if not result["valid"]:
            errors.append(f"observation {index}: " + "; ".join(result["errors"]))

    conflicts = []
    for left_index in range(len(normalized)):
        left = normalized[left_index]
        if left is None:
            continue
        for right_index in range(left_index + 1, len(normalized)):
            right = normalized[right_index]
            if right is None:
                continue
            a = left["tree_head"]
            b = right["tree_head"]
            if a["log_id"] == b["log_id"] and a["tree_size"] == b["tree_size"] and a["root_hash"] != b["root_hash"]:
                conflicts.append({
                    "type": "same-size-root-conflict",
                    "log_id": a["log_id"], "tree_size": a["tree_size"],
                    "left_observation": left_index, "right_observation": right_index,
                    "left_root": a["root_hash"], "right_root": b["root_hash"],
                })
    for index, result in enumerate(results):
        if result["valid"] and result["continuity_status"] == "failed":
            conflicts.append({
                "type": "witness-reported-continuity-failure",
                "log_id": result["log_id"], "tree_size": result["tree_size"],
                "observation": index,
            })

    return {
        "valid": not errors,
        "conflict_detected": bool(conflicts),
        "observation_results": results,
        "conflicts": conflicts,
        "errors": errors,
    }
