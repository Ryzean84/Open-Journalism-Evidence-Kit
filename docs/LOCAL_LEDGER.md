# OJEK Local Evidence Ledger v0.1

The local ledger is the first runnable component of the Open Journalism Evidence Kit. It stores metadata about public sources on the operator's own computer.

## Scope and limitations

The first version supports:
- Creating a local workspace and node identifier.
- Recording source metadata and collection context.
- Validating records against the published Source Observation v0.1 JSON Schema.
- Recording creation events in a local JSON Lines event log.
- Hash-chaining events and hashing canonical record metadata.
- Exporting a deterministic JSON evidence package.
- Verifying record digests and the event chain.

It does not:
- Download or scrape source pages.
- Copy article bodies, images, or attachments.
- Provide confidential source intake or secure messaging.
- Encrypt the workspace or protect a compromised computer.
- Prove a source's identity, accuracy, authenticity, or truth.
- Make a local log tamper-proof against an administrator who can rewrite files and recompute hashes.
- Synchronize or replicate between nodes.

Use established secure source-intake systems for confidential tips. Do not place confidential source identities, private communications, credentials, or sensitive investigative material in this ledger.

## Requirements

- Python 3.10 or later.
- Internet access only to install the package dependency; the ledger itself runs locally.
- The jsonschema package, installed automatically with the project.

## Install from a clone

~~~bash
git clone https://github.com/Ryzean84/Open-Journalism-Evidence-Kit.git
cd Open-Journalism-Evidence-Kit
python -m venv .venv
~~~

Activate the virtual environment:

**macOS / Linux**
~~~bash
source .venv/bin/activate
~~~

**Windows PowerShell**
~~~powershell
.venv\Scripts\Activate.ps1
~~~

Install the local package:
~~~bash
python -m pip install -e .
~~~

## Quick start

Create a workspace:
~~~bash
ojek --workspace ./my-ledger init
~~~

Record a public source. Use the original public URL and metadata; do not paste confidential source material:
~~~bash
ojek --workspace ./my-ledger add \
  --url "https://example.org/public-report" \
  --title "Example public report" \
  --publisher "Example Publisher" \
  --language en \
  --method manual \
  --rights-status link_only \
  --notes "Manually observed public page; metadata only."
~~~

List and validate records:
~~~bash
ojek --workspace ./my-ledger list
ojek --workspace ./my-ledger validate
ojek --workspace ./my-ledger verify
~~~

Export a portable evidence package:
~~~bash
ojek --workspace ./my-ledger export --output exports/first-export.json
~~~

The export is deterministic for the same records and event history. Its package digest is a checksum of the canonical package content before the digest field is added.

## Storage layout

~~~text
my-ledger/
  node.json       # local node identifier and format version
  records/        # one JSON source-observation record per file
  events.jsonl    # append-only-by-application event sequence
  exports/        # generated evidence packages
~~~

The event log is hash-chained: each event includes the previous event's hash. Each source-observation digest covers canonical JSON for the complete record excluding its integrity block. Canonical JSON uses UTF-8, sorted object keys, compact separators, and no NaN values.

These checks detect accidental changes and unsophisticated tampering. They are not a digital signature, trusted timestamp, external witness, or protection against an operator who can rewrite all files and recompute the chain. Future versions may add signed checkpoints and independent witnesses.

## Rights and integrity

The default is metadata-only. A rights status of link_only or not_assessed does not authorize copying or republishing full content. The CLI deliberately sets full_content_storage_allowed to false in v0.1.

A SHA-256 digest establishes whether the locally recorded bytes match the bytes later checked. It does not establish whether the source is accurate or whether the source publisher is genuine.

## Tests

From the repository root:
~~~bash
python tests/test_source_observation_schema.py
python -m unittest discover -s tests -p 'test_local_ledger.py' -v
~~~

## Current status

This is an early v0.1 implementation. Review its code and security limitations before using it in real investigations. Back up the workspace. Do not rely on it as the only copy of important records.


## Corrections and status notices

The ledger supports append-only follow-up events:

- A correction creates a new source-observation record with a `supersedes` link. The original record is retained unchanged.
- A dispute appends a `record.disputed` event with the reason supplied by the operator.
- A withdrawal appends a `record.withdrawn` event.
- A restriction appends a `record.restricted` event.

These notices document an operator's report; they do not independently establish that a claim is false, that a publisher has authenticated a correction, or that a legal takedown obligation exists. A restriction notice is not access-control enforcement and does not erase local copies or prior exports. Handle privacy, legal demands, and sensitive material through a separately designed and reviewed process.

Example correction:

~~~bash
ojek --workspace ./my-ledger amend \\
  --record-id "urn:uuid:REPLACE-WITH-RECORD-ID" \\
  --type correction \\
  --reason "Publisher issued a corrected headline" \\
  --title "Corrected public report title"
~~~

Example dispute or withdrawal notice:

~~~bash
ojek --workspace ./my-ledger amend \\
  --record-id "urn:uuid:REPLACE-WITH-RECORD-ID" \\
  --type disputed \\
  --reason "A cited primary source conflicts with this observation"
~~~

## Independent package verification

A recipient can verify an exported package without opening the original workspace:

~~~bash
ojek verify-package ./evidence-package.json
~~~

The verifier checks the package digest, each included record's schema and digest, the event hash chain, and whether each included record has a matching event in the included history. When an export intentionally contains only selected records, events for records omitted from that selection cannot be cross-checked against those omitted records. The event-chain integrity is still checked.

Verification establishes consistency with the package's recorded hashes, not source truth, identity, completeness, or a trusted time of observation.
