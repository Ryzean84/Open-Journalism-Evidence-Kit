"""Local-first metadata ledger with schema validation and hash-chained events.

This is an early-stage research tool. It is not secure source-intake software,
a legal-compliance engine, or proof that a recorded claim is true.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_VERSION = "0.1.0"
_REPOSITORY_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "source-observation.v0.1.schema.json"
_INSTALLED_SCHEMA = Path(sys.prefix) / "share" / "ojek-local-ledger" / "schemas" / "source-observation.v0.1.schema.json"
SCHEMA_PATH = _REPOSITORY_SCHEMA if _REPOSITORY_SCHEMA.exists() else _INSTALLED_SCHEMA


class LedgerError(Exception):
    """Expected ledger operation failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    """Stable UTF-8 JSON representation used for local integrity digests."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise LedgerError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LedgerError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def schema_validator() -> Draft202012Validator:
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_record(record: dict[str, Any]) -> list[str]:
    validator = schema_validator()
    errors = sorted(validator.iter_errors(record), key=lambda err: list(err.path))
    return [f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors]


def record_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload.pop("integrity", None)
    return payload


def seal_record(record: dict[str, Any]) -> dict[str, Any]:
    """Add a digest over the canonical record excluding its integrity block."""
    sealed = dict(record)
    payload = canonical_bytes(record_payload(sealed))
    sealed["integrity"] = {
        "representation": "metadata_record",
        "algorithm": "sha-256",
        "digest": sha256_hex(payload),
        "byte_length": len(payload),
    }
    return sealed


def verify_record_digest(record: dict[str, Any]) -> bool:
    integrity = record.get("integrity")
    if not isinstance(integrity, dict):
        return False
    payload = canonical_bytes(record_payload(record))
    return (
        integrity.get("algorithm") == "sha-256"
        and integrity.get("representation") == "metadata_record"
        and integrity.get("digest") == sha256_hex(payload)
        and integrity.get("byte_length") == len(payload)
    )


def workspace_paths(workspace: str | Path) -> dict[str, Path]:
    root = Path(workspace).expanduser().resolve()
    return {
        "root": root,
        "node": root / "node.json",
        "records": root / "records",
        "events": root / "events.jsonl",
        "exports": root / "exports",
    }


def init_workspace(workspace: str | Path) -> dict[str, Any]:
    paths = workspace_paths(workspace)
    paths["records"].mkdir(parents=True, exist_ok=True)
    paths["exports"].mkdir(parents=True, exist_ok=True)
    if paths["node"].exists():
        return load_json(paths["node"])
    node = {
        "format": "ojek-local-ledger",
        "format_version": SCHEMA_VERSION,
        "node_id": "node:" + str(uuid.uuid4()),
        "created_at": utc_now(),
        "storage": "local-filesystem",
    }
    atomic_write(paths["node"], canonical_bytes(node) + b"\n")
    if not paths["events"].exists():
        atomic_write(paths["events"], b"")
    return node


def require_workspace(workspace: str | Path) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = workspace_paths(workspace)
    if not paths["node"].exists():
        raise LedgerError(f"No ledger found at {paths['root']}. Run 'ojek init' first.")
    return paths, load_json(paths["node"])


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"Invalid event JSON on line {line_number}: {exc}") from exc
            if not isinstance(event, dict):
                raise LedgerError(f"Event on line {line_number} is not a JSON object.")
            events.append(event)
    return events


def event_hash(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("event_hash", None)
    return sha256_hex(canonical_bytes(payload))


def append_event(paths: dict[str, Path], event_type: str, record: dict[str, Any], details: dict[str, Any] | None = None) -> dict[str, Any]:
    events = read_events(paths["events"])
    previous = events[-1]["event_hash"] if events else None
    event = {
        "event_id": "event:" + str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": utc_now(),
        "record_id": record["record_id"],
        "record_digest": record["integrity"]["digest"],
        "previous_event_hash": previous,
    }
    if details:
        event["details"] = details
    event["event_hash"] = event_hash(event)
    with paths["events"].open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def add_record(workspace: str | Path, fields: dict[str, Any]) -> dict[str, Any]:
    paths, node = require_workspace(workspace)
    record_id = "urn:uuid:" + str(uuid.uuid4())
    source = {
        "canonical_url": fields["url"],
        "publisher": fields.get("publisher"),
        "title": fields.get("title"),
        "byline": fields.get("byline"),
        "published_at": fields.get("published_at"),
        "updated_at": fields.get("updated_at"),
        "language": fields.get("language"),
        "media_type": fields.get("media_type", "text/html"),
    }
    collection = {
        "method": fields.get("method", "manual"),
        "node_id": node["node_id"],
        "tool_name": "ojek-local-ledger",
        "tool_version": SCHEMA_VERSION,
        "http_status": fields.get("http_status"),
        "notes": fields.get("notes"),
    }
    rights = {
        "status": fields.get("rights_status", "not_assessed"),
        "license_name": fields.get("license_name"),
        "license_url": fields.get("license_url"),
        "permission_reference": fields.get("permission_reference"),
        "full_content_storage_allowed": False,
        "reviewed_at": None,
    }
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "source": source,
        "observed_at": fields.get("observed_at") or utc_now(),
        "collection": collection,
        "rights": rights,
        "translation": None,
        "supersedes": None,
        "correction_status": "none_known",
    }
    record = seal_record(record)
    errors = validate_record(record)
    if errors:
        raise LedgerError("Record failed schema validation:\n- " + "\n- ".join(errors))
    record_path = paths["records"] / (record_id.removeprefix("urn:uuid:") + ".json")
    if record_path.exists():
        raise LedgerError("Unexpected record ID collision.")
    atomic_write(record_path, canonical_bytes(record) + b"\n")
    append_event(paths, "record.created", record)
    return record


def load_records(paths: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    if not paths["records"].exists():
        return records
    for path in sorted(paths["records"].glob("*.json")):
        records.append(load_json(path))
    return records


def validate_workspace(workspace: str | Path) -> tuple[int, list[str]]:
    paths, _ = require_workspace(workspace)
    records = load_records(paths)
    problems: list[str] = []
    for record in records:
        errors = validate_record(record)
        if errors:
            problems.extend(f"{record.get('record_id', '<unknown>')}: {error}" for error in errors)
        if not verify_record_digest(record):
            problems.append(f"{record.get('record_id', '<unknown>')}: integrity digest mismatch")
    return len(records), problems


def verify_workspace(workspace: str | Path) -> dict[str, Any]:
    paths, node = require_workspace(workspace)
    records = load_records(paths)
    record_by_id = {record.get("record_id"): record for record in records}
    problems: list[str] = []
    for record in records:
        errors = validate_record(record)
        if errors:
            problems.extend(f"{record.get('record_id', '<unknown>')}: schema: {error}" for error in errors)
        if not verify_record_digest(record):
            problems.append(f"{record.get('record_id', '<unknown>')}: record digest mismatch")
    events = read_events(paths["events"])
    previous = None
    seen_event_ids: set[str] = set()
    for index, event in enumerate(events, start=1):
        if event.get("event_id") in seen_event_ids:
            problems.append(f"event line {index}: duplicate event ID")
        seen_event_ids.add(event.get("event_id"))
        if event.get("previous_event_hash") != previous:
            problems.append(f"event line {index}: previous-event hash does not match chain")
        if event.get("event_hash") != event_hash(event):
            problems.append(f"event line {index}: event hash mismatch")
        record = record_by_id.get(event.get("record_id"))
        if record is None:
            problems.append(f"event line {index}: references missing record")
        elif event.get("record_digest") != record.get("integrity", {}).get("digest"):
            problems.append(f"event line {index}: record digest reference mismatch")
        previous = event.get("event_hash")
    event_record_ids = {event.get("record_id") for event in events}
    for record_id in record_by_id:
        if record_id not in event_record_ids:
            problems.append(f"{record_id}: record has no ledger event")
    return {
        "node_id": node.get("node_id"),
        "record_count": len(records),
        "event_count": len(events),
        "valid": not problems,
        "problems": problems,
    }


def export_package(workspace: str | Path, output: str | Path, record_ids: list[str] | None = None) -> Path:
    paths, node = require_workspace(workspace)
    records = load_records(paths)
    if record_ids:
        wanted = set(record_ids)
        records = [record for record in records if record.get("record_id") in wanted]
        missing = wanted - {record.get("record_id") for record in records}
        if missing:
            raise LedgerError("Unknown record ID(s): " + ", ".join(sorted(missing)))
    # Include the complete event chain so a recipient can verify previous-event links,
    # even when only a subset of source records was selected for this package.
    events = read_events(paths["events"])
    package: dict[str, Any] = {
        "format": "ojek-evidence-package",
        "format_version": SCHEMA_VERSION,
        "node_id": node["node_id"],
        "records": records,
        "events": events,
    }
    package["package_digest"] = sha256_hex(canonical_bytes(package))
    destination = Path(output).expanduser()
    if not destination.is_absolute():
        destination = paths["root"] / destination
    atomic_write(destination, canonical_bytes(package) + b"\n")
    return destination


def record_notice(
    workspace: str | Path,
    record_id: str,
    notice_type: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Append a dispute, withdrawal, or restriction notice without rewriting a record."""
    allowed = {
        "record.disputed",
        "record.withdrawn",
        "record.restricted",
    }
    if notice_type not in allowed:
        raise LedgerError(f"Unsupported notice type: {notice_type}")
    paths, _ = require_workspace(workspace)
    records = {record.get("record_id"): record for record in load_records(paths)}
    record = records.get(record_id)
    if record is None:
        raise LedgerError(f"Unknown record ID: {record_id}")
    details = {"reason": reason} if reason else None
    return append_event(paths, notice_type, record, details)


def correct_record(
    workspace: str | Path,
    record_id: str,
    reason: str,
    source_updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new observation linked to the prior record; never edit the prior record."""
    paths, node = require_workspace(workspace)
    records = {record.get("record_id"): record for record in load_records(paths)}
    original = records.get(record_id)
    if original is None:
        raise LedgerError(f"Unknown record ID: {record_id}")
    updated_source = dict(original.get("source", {}))
    allowed_source_fields = {
        "canonical_url", "publisher", "title", "byline",
        "published_at", "updated_at", "language", "media_type",
    }
    for key, value in (source_updates or {}).items():
        if key not in allowed_source_fields:
            raise LedgerError(f"Unsupported source field: {key}")
        updated_source[key] = value
    successor = dict(original)
    successor["record_id"] = "urn:uuid:" + str(uuid.uuid4())
    successor["source"] = updated_source
    successor["observed_at"] = utc_now()
    successor["collection"] = dict(original.get("collection", {}))
    successor["collection"]["node_id"] = node["node_id"]
    successor["collection"]["notes"] = reason
    successor["supersedes"] = record_id
    successor["correction_status"] = "correction_observed"
    successor = seal_record(successor)
    errors = validate_record(successor)
    if errors:
        raise LedgerError("Corrected record failed schema validation:\\n- " + "\\n- ".join(errors))
    record_path = paths["records"] / (successor["record_id"].removeprefix("urn:uuid:") + ".json")
    atomic_write(record_path, canonical_bytes(successor) + b"\\n")
    append_event(paths, "record.superseded", successor, {"supersedes": record_id, "reason": reason})
    return successor


def verify_package(package_path: str | Path) -> dict[str, Any]:
    """Verify a portable evidence package without access to its originating workspace."""
    package = load_json(Path(package_path))
    problems: list[str] = []
    if not isinstance(package, dict) or package.get("format") != "ojek-evidence-package":
        raise LedgerError("Not an OJEK evidence package.")
    expected_digest = package.get("package_digest")
    payload = dict(package)
    payload.pop("package_digest", None)
    if expected_digest != sha256_hex(canonical_bytes(payload)):
        problems.append("package digest mismatch")
    records = package.get("records", [])
    events = package.get("events", [])
    if not isinstance(records, list) or not isinstance(events, list):
        raise LedgerError("Package records and events must be arrays.")
    record_by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            problems.append(f"record {index}: not a JSON object")
            continue
        record_id = record.get("record_id")
        if record_id in record_by_id:
            problems.append(f"record {index}: duplicate record ID")
        record_by_id[record_id] = record
        for error in validate_record(record):
            problems.append(f"{record_id}: schema: {error}")
        if not verify_record_digest(record):
            problems.append(f"{record_id}: record digest mismatch")
    previous = None
    seen_event_ids: set[str] = set()
    matched_records: set[str] = set()
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            problems.append(f"event {index}: not a JSON object")
            continue
        event_id = event.get("event_id")
        if event_id in seen_event_ids:
            problems.append(f"event {index}: duplicate event ID")
        seen_event_ids.add(event_id)
        if event.get("previous_event_hash") != previous:
            problems.append(f"event {index}: previous-event hash does not match chain")
        if event.get("event_hash") != event_hash(event):
            problems.append(f"event {index}: event hash mismatch")
        event_record_id = event.get("record_id")
        included = record_by_id.get(event_record_id)
        if included is not None:
            if event.get("record_digest") != included.get("integrity", {}).get("digest"):
                problems.append(f"event {index}: record digest reference mismatch")
            matched_records.add(event_record_id)
        previous = event.get("event_hash")
    for record_id in record_by_id:
        if record_id not in matched_records:
            problems.append(f"{record_id}: no matching event in package history")
    return {
        "valid": not problems,
        "record_count": len(records),
        "event_count": len(events),
        "problems": problems,
    }
