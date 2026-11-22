# Release Readiness Checklist

A merged pull request is not automatically a release. Complete this checklist for every tagged release.

## Scope and compatibility

- [ ] Release scope and supported protocol identifiers are stated.
- [ ] Existing v0.1 fixtures and verifiers remain unchanged.
- [ ] New schemas and wire formats are versioned and documented.
- [ ] Migration and deprecation guidance is available.
- [ ] Changelog distinguishes implemented features from proposals.

## Engineering validation

- [ ] CI passes on every supported Python version.
- [ ] JavaScript reference vectors pass on the supported Node.js version.
- [ ] Package builds and installs from a clean environment.
- [ ] Installed package includes every published schema and runtime asset.
- [ ] CLI smoke tests cover success, invalid input, and non-zero exit status.
- [ ] Frozen positive and negative vectors are included.
- [ ] Dependency and static security checks have no unresolved release-blocking findings.

## Security, privacy, and rights

- [ ] Threat model and known limitations are current.
- [ ] No secrets, confidential source data, or sensitive personal data are included.
- [ ] Rights and license provenance are reviewed for added material.
- [ ] Cryptographic claims are limited to what the implementation proves.
- [ ] Key-management and witness claims are not made unless implemented and independently reviewed.
- [ ] Backup, restore, incident, and disclosure procedures are documented.

## Review and publication

- [ ] At least one maintainer review is recorded.
- [ ] Cryptographic protocol changes receive independent specialist review.
- [ ] Release notes include commit, compatibility, limitations, and known issues.
- [ ] Tag points to the reviewed commit.
- [ ] Build artifacts are reproducible or their provenance is documented.
- [ ] Post-release verification is recorded.
