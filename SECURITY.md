# Security Policy

## Scope

This policy covers vulnerabilities in OJEK code, schemas, build workflows, documentation examples, and project-operated infrastructure. Independent node operators remain responsible for their own deployments and threat models.

## Reporting a vulnerability

Please do not publish an exploitable vulnerability, sensitive source information, credentials, private data, or a working exploit in a public issue or pull request.

Use GitHub's private vulnerability reporting or security advisory feature for this repository if available. If that feature is unavailable, contact the repository maintainers privately through GitHub and request a secure disclosure channel. Share only the minimum details needed to reproduce and assess the issue.

A useful report includes:
- Affected repository path, version, or commit.
- Impact and conditions required.
- Reproduction steps or a proof of concept that does not expose real people or data.
- Suggested mitigation, if known.

## Response principles

Maintainers should:
- Acknowledge reports as soon as reasonably possible.
- Restrict access to report details.
- Assess impact and affected versions.
- Coordinate a fix and release where appropriate.
- Credit reporters only with their consent.
- Publish a sanitized advisory after remediation when disclosure is safe.

Do not test against systems you do not own or have explicit permission to assess. Do not access, modify, or retain private source material during security testing.

## Deployment warning

OJEK is early-stage. Its documentation and current code do not guarantee journalist, source, or operator safety. Do not deploy it for high-risk source intake or sensitive investigations without a threat-model review and independent security assessment.

For confidential source intake, evaluate mature tools such as SecureDrop rather than treating OJEK as a replacement.
