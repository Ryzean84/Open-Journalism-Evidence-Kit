#!/usr/bin/env python3
"""Validate OJEK source-observation fixtures against the v0.1 JSON Schema."""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "source-observation.v0.1.schema.json"
VALID_DIR = ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = ROOT / "tests" / "fixtures" / "invalid"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []

    valid_files = sorted(VALID_DIR.glob("*.json"))
    invalid_files = sorted(INVALID_DIR.glob("*.json"))

    if not valid_files:
        failures.append("No valid fixtures found.")
    if not invalid_files:
        failures.append("No invalid fixtures found.")

    for path in valid_files:
        errors = sorted(validator.iter_errors(load_json(path)), key=lambda error: list(error.path))
        if errors:
            failures.append(f"{path.relative_to(ROOT)} should be valid:")
            failures.extend(f"  - {'/'.join(map(str, error.path))}: {error.message}" for error in errors)
        else:
            print(f"PASS valid: {path.relative_to(ROOT)}")

    for path in invalid_files:
        errors = sorted(validator.iter_errors(load_json(path)), key=lambda error: list(error.path))
        if not errors:
            failures.append(f"{path.relative_to(ROOT)} should be invalid but passed.")
        else:
            print(f"PASS rejected invalid fixture: {path.relative_to(ROOT)}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print("All source-observation schema fixtures passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
