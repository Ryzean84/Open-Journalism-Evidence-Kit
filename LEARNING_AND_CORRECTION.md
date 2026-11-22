# Learning, Corrections, and Failure Records

## Principle

A mistake is not a weakness to conceal. It is a new piece of evidence about the system, its assumptions, or its operating environment. We record failures so the community can understand them, reproduce them where safe, and improve the design.

## What we record

- Incorrect or incomplete source metadata
- Broken or redirected source links
- Parser and connector failures
- Translation errors and disputed terminology
- Integrity-check mismatches
- Replication delays or divergence
- Security and privacy incidents
- Rights or takedown concerns
- Accessibility barriers
- Documentation that overstated actual capability

## Required failure record

Each report should include:
1. Short, neutral title
2. Date discovered and affected component/version
3. Expected behavior
4. Observed behavior
5. Reproduction steps or supporting evidence, where safe
6. Impact and affected users/data
7. Root-cause analysis, or clearly labeled unknowns
8. Immediate containment
9. Corrective action and owner
10. Verification evidence
11. Follow-up prevention work

Never include credentials, protected source identities, private investigative material, or unnecessary personal data in a public issue.

## No-blame, high-accountability practice

- Focus on system behavior and contributing conditions, not humiliation.
- Do not conceal material errors or quietly rewrite history.
- Correct public claims promptly and link corrections to the original record.
- Distinguish confirmed root cause from hypothesis.
- Give affected people a safe way to report harm or request review.
- Publish sanitized incident summaries when doing so does not increase risk.
- Treat repeated failures as signals to redesign, not merely add more warnings.

## Corrections in the evidence ledger

A correction is a new event referencing the prior record. It should identify what changed, why, who reviewed it, and when. The original record may be restricted or removed from service where required, especially for privacy, safety, or rights reasons. Append-only history is not permission to retain harmful data forever.

## Learning loop

Observe → document → contain → investigate → correct → independently verify → publish a safe lesson → update tests and SOP.

A failure record is complete only when the corrective behavior has been tested or the remaining uncertainty is explicitly documented.
