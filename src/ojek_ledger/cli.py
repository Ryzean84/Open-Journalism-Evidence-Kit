"""Command-line interface for the OJEK local ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import LedgerError, add_record, export_package, init_workspace, require_workspace, validate_workspace, verify_workspace


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
            from .core import load_records
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
        if args.command == "export":
            output = export_package(workspace, args.output, args.record_id or None)
            print(f"Exported evidence package: {output.resolve()}")
            return 0
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
