"""Command-line interface for the OJEK local ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checkpoints import CheckpointError, build_checkpoint, create_inclusion_proof, verify_checkpoint, verify_inclusion_proof
from .transparency_v2 import (
    TransparencyLogError, build_consistency_proof_document, build_tree_head,
    entry_bytes, generate_consistency_proof_v2, strict_json_loads, validate_log_entry,
    verify_consistency_proof_document,
)
from .core import LedgerError, add_record, atomic_write, correct_record, export_package, init_workspace, load_json, load_records, record_notice, require_workspace, validate_workspace, verify_package, verify_workspace


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="ojek",
        description="Local-first metadata ledger for public-interest source observations.",
        epilog="This early-stage tool is not secure source-intake software and does not determine truth.",
    )
    root.add_argument("--workspace", default="./ojek-workspace", help="Ledger directory (default: ./ojek-workspace)")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create a local ledger workspace")
    add = commands.add_parser("add", help="Record metadata about a public source")
    add.add_argument("--url", required=True, help="Canonical public source URL")
    add.add_argument("--title")
    add.add_argument("--publisher")
    add.add_argument("--byline")
    add.add_argument("--published-at", dest="published_at", help="Publication timestamp in ISO 8601 format")
    add.add_argument("--updated-at", dest="updated_at", help="Source update timestamp in ISO 8601 format")
    add.add_argument("--language", help="BCP 47 language tag, such as en or pt-BR")
    add.add_argument("--media-type", dest="media_type", default="text/html")
    add.add_argument("--method", choices=["manual", "rss", "atom", "publisher_api", "official_feed", "public_dataset", "sitemap", "other"], default="manual")
    add.add_argument("--http-status", dest="http_status", type=int)
    add.add_argument("--notes")
    add.add_argument("--rights-status", dest="rights_status", choices=["unknown", "link_only", "open_license", "public_domain_reviewed", "permission_granted", "restricted", "not_assessed"], default="not_assessed")
    add.add_argument("--license-name", dest="license_name")
    add.add_argument("--license-url", dest="license_url")
    add.add_argument("--permission-reference", dest="permission_reference")
    commands.add_parser("list", help="List locally recorded source observations")
    commands.add_parser("validate", help="Validate records against the published JSON Schema")
    commands.add_parser("verify", help="Verify record digests and the event hash chain")
    package_verify = commands.add_parser("verify-package", help="Verify a portable evidence package")
    package_verify.add_argument("package", help="Path to an exported evidence package")
    amend = commands.add_parser("amend", help="Append a correction, dispute, withdrawal, or restriction notice")
    amend.add_argument("--record-id", required=True)
    amend.add_argument("--type", required=True, choices=["correction", "disputed", "withdrawn", "restricted"])
    amend.add_argument("--reason", required=True)
    amend.add_argument("--url", help="Corrected canonical URL (correction only)")
    amend.add_argument("--title", help="Corrected source title (correction only)")
    amend.add_argument("--publisher", help="Corrected publisher (correction only)")
    checkpoint = commands.add_parser("checkpoint", help="Create or verify an unsigned Merkle checkpoint")
    checkpoint_commands = checkpoint.add_subparsers(dest="checkpoint_command", required=True)
    checkpoint_create = checkpoint_commands.add_parser("create", help="Create a checkpoint from local record digests")
    checkpoint_create.add_argument("--output", default="exports/checkpoint.json")
    checkpoint_verify = checkpoint_commands.add_parser("verify", help="Verify a checkpoint JSON file")
    checkpoint_verify.add_argument("checkpoint", help="Path to checkpoint JSON")
    checkpoint_proof = checkpoint_commands.add_parser("proof", help="Create an inclusion proof")
    checkpoint_proof.add_argument("checkpoint", help="Path to checkpoint JSON")
    checkpoint_proof.add_argument("--record-id", required=True)
    checkpoint_verify_proof = checkpoint_commands.add_parser("verify-proof", help="Verify a portable inclusion proof against a checkpoint")
    checkpoint_verify_proof.add_argument("proof", help="Path to the inclusion proof JSON")
    checkpoint_verify_proof.add_argument("checkpoint", help="Path to the checkpoint JSON")
    log_v2 = commands.add_parser("log-v2", help="Create and verify v0.2 append-only transparency log artifacts")
    log_commands = log_v2.add_subparsers(dest="log_v2_command", required=True)
    log_head = log_commands.add_parser("head", help="Build an unsigned v0.2 tree head from an ordered JSON entry array")
    log_head.add_argument("entries", help="JSON file containing an array of v0.2 log entries")
    log_head.add_argument("--log-id", required=True)
    log_head.add_argument("--issued-at", required=True, help="RFC 3339 UTC timestamp ending in Z")
    log_head.add_argument("--output", required=True)
    log_proof = log_commands.add_parser("consistency-proof", help="Generate a proof between two v0.2 tree heads")
    log_proof.add_argument("entries", help="JSON file containing the complete ordered entry array")
    log_proof.add_argument("old_head", help="Earlier tree-head JSON file")
    log_proof.add_argument("new_head", help="Later tree-head JSON file")
    log_proof.add_argument("--output", required=True)
    log_verify = log_commands.add_parser("verify-consistency", help="Verify a proof against two tree heads")
    log_verify.add_argument("old_head")
    log_verify.add_argument("new_head")
    log_verify.add_argument("proof")
    export = commands.add_parser("export", help="Export a deterministic JSON evidence package")
    export.add_argument("--output", default="exports/evidence-package.json")
    export.add_argument("--record-id", action="append", default=[], help="Limit export to this record ID; may be repeated")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    workspace = Path(args.workspace).expanduser()
    try:
        if args.command == "init":
            node = init_workspace(workspace)
            print(f"Initialized ledger: {workspace.resolve()}")
            print(f"Node ID: {node['node_id']}")
            return 0
        if args.command == "add":
            record = add_record(workspace, vars(args))
            print(f"Recorded: {record['record_id']}")
            print(f"Source: {record['source']['canonical_url']}")
            print(f"SHA-256: {record['integrity']['digest']}")
            print("Note: the digest checks record integrity, not the truth of the source.")
            return 0
        if args.command == "list":
            paths, _ = require_workspace(workspace)
            records = load_records(paths)
            if not records:
                print("No records yet.")
                return 0
            for record in records:
                source = record.get("source", {})
                print(f"{record.get('record_id')}\t{record.get('observed_at')}\t{source.get('title') or '(untitled)'}\t{source.get('canonical_url')}")
            return 0
        if args.command == "validate":
            count, problems = validate_workspace(workspace)
            if problems:
                print("\n".join(problems), file=sys.stderr)
                return 1
            print(f"Valid: {count} record(s) conform to the source-observation schema.")
            return 0
        if args.command == "verify":
            result = verify_workspace(workspace)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["valid"] else 1
        if args.command == "checkpoint":
            if args.checkpoint_command == "create":
                paths, _ = require_workspace(workspace)
                from .core import canonical_bytes
                ledger_result = verify_workspace(workspace)
                if not ledger_result["valid"]:
                    raise CheckpointError("local ledger verification failed: " + "; ".join(ledger_result["problems"]))
                checkpoint_doc = build_checkpoint(load_records(paths))
                destination = Path(args.output).expanduser()
                if not destination.is_absolute():
                    destination = paths["root"] / destination
                atomic_write(destination, canonical_bytes(checkpoint_doc) + b"\n")
                print(f"Created unsigned checkpoint: {destination.resolve()}")
                print(f"Merkle root: {checkpoint_doc['merkle_root']}")
                print("Warning: unsigned and unwitnessed; not proof of truth or completeness.")
                return 0
            if args.checkpoint_command == "verify":
                checkpoint_doc = load_json(Path(args.checkpoint).expanduser())
                result = verify_checkpoint(checkpoint_doc)
                print(json.dumps(result, indent=2))
                return 0 if result["valid"] else 1
            if args.checkpoint_command == "proof":
                checkpoint_doc = json.loads(Path(args.checkpoint).expanduser().read_text(encoding="utf-8"))
                proof = create_inclusion_proof(checkpoint_doc, args.record_id)
                print(json.dumps(proof, indent=2))
                return 0
            if args.checkpoint_command == "verify-proof":
                proof = strict_json_loads(Path(args.proof).expanduser().read_text(encoding="utf-8"))
                checkpoint_doc = load_json(Path(args.checkpoint).expanduser())
                checkpoint_result = verify_checkpoint(checkpoint_doc)
                if not checkpoint_result["valid"]:
                    raise CheckpointError("checkpoint verification failed: " + "; ".join(checkpoint_result["problems"]))
                valid = verify_inclusion_proof(
                    proof,
                    expected_root=checkpoint_doc["merkle_root"],
                    expected_checkpoint_digest=checkpoint_doc["checkpoint_digest"],
                )
                print(json.dumps({"valid": valid, "record_id": proof.get("record_id") if isinstance(proof, dict) else None}, indent=2))
                return 0 if valid else 1
        if args.command == "log-v2":
            if args.log_v2_command == "head":
                entries_value = strict_json_loads(Path(args.entries).expanduser().read_text(encoding="utf-8"))
                if not isinstance(entries_value, list):
                    raise TransparencyLogError("entries file must contain a JSON array")
                normalized = [
                    entry_bytes(validate_log_entry(item, expected_log_id=args.log_id, expected_index=index))
                    for index, item in enumerate(entries_value)
                ]
                head = build_tree_head(args.log_id, normalized, args.issued_at)
                destination = Path(args.output).expanduser()
                atomic_write(destination, json.dumps(head, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
                print(f"Created unsigned v0.2 tree head: {destination.resolve()}")
                print(f"Tree size: {head['tree_size']}")
                print(f"Root hash: {head['root_hash']}")
                print("Warning: unsigned and unwitnessed; this does not establish trusted time or truth.")
                return 0
            if args.log_v2_command == "consistency-proof":
                entries_value = strict_json_loads(Path(args.entries).expanduser().read_text(encoding="utf-8"))
                old_head = strict_json_loads(Path(args.old_head).expanduser().read_text(encoding="utf-8"))
                new_head = strict_json_loads(Path(args.new_head).expanduser().read_text(encoding="utf-8"))
                if not isinstance(entries_value, list):
                    raise TransparencyLogError("entries file must contain a JSON array")
                log_id = old_head.get("log_id") if isinstance(old_head, dict) else None
                normalized = [
                    entry_bytes(validate_log_entry(item, expected_log_id=log_id, expected_index=index))
                    for index, item in enumerate(entries_value)
                ]
                if not isinstance(old_head, dict) or not isinstance(new_head, dict):
                    raise TransparencyLogError("old and new tree heads must be JSON objects")
                proof = generate_consistency_proof_v2(normalized, old_head.get("tree_size"))
                document = build_consistency_proof_document(log_id, old_head, new_head, proof)
                destination = Path(args.output).expanduser()
                atomic_write(destination, json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
                print(f"Created consistency proof: {destination.resolve()}")
                return 0
            if args.log_v2_command == "verify-consistency":
                old_head = load_json(Path(args.old_head).expanduser())
                new_head = load_json(Path(args.new_head).expanduser())
                proof = load_json(Path(args.proof).expanduser())
                valid = verify_consistency_proof_document(old_head, new_head, proof)
                print(json.dumps({"valid": valid, "protocol": "ojek-consistency-proof-v0.2"}, indent=2))
                return 0 if valid else 1
        if args.command == "export":
            output = export_package(workspace, args.output, args.record_id or None)
            print(f"Exported evidence package: {output.resolve()}")
            return 0
        if args.command == "verify-package":
            result = verify_package(args.package)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["valid"] else 1
        if args.command == "amend":
            if args.type == "correction":
                updates = {key: value for key, value in {
                    "canonical_url": args.url, "title": args.title, "publisher": args.publisher
                }.items() if value is not None}
                record = correct_record(workspace, args.record_id, args.reason, updates)
                print(f"Correction recorded: {record['record_id']}")
                print(f"Supersedes: {record['supersedes']}")
            else:
                event = record_notice(workspace, args.record_id, "record." + args.type, args.reason)
                print(f"Notice recorded: {event['event_id']} ({event['event_type']})")
            return 0
    except (LedgerError, CheckpointError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
