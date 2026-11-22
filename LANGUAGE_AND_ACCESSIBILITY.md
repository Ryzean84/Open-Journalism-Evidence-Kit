# Global Language and Accessibility Strategy

## Principle
Language must not be a gatekeeping mechanism. The project should support original-language access first and translation as a transparent, reviewable layer.

## Language architecture
- Store the original source language and script exactly as published where permitted.
- Use BCP 47 language tags for language and locale metadata.
- Preserve right-to-left and bidirectional text correctly.
- Support Unicode throughout storage, search, export, and interface layers.
- Keep original and translated text side by side.
- Record whether a translation is human, machine-generated, community-reviewed, or professionally certified.
- Retain translation history and identify the tool/model and version when machine translation is used.
- Do not overwrite an original text with a translation.
- Preserve names, dates, legal terms, and quoted language with special care.

## Translation workflow
1. Identify source language; do not guess silently.
2. Preserve the original text and source citation.
3. Generate an optional machine translation where suitable.
4. Mark the translation clearly as machine-generated and unverified.
5. Invite review by fluent speakers and subject-matter experts.
6. Record corrections as new translation versions.
7. Keep disputed terminology and alternative translations visible.
8. Never use translation alone to establish legal meaning or a factual allegation.

## Practical rollout
Start with a translation-ready interface and metadata model, not a promise to translate every language immediately. Prioritize languages based on community participation, journalist needs, regional diversity, and the availability of reviewers. Design so additional languages can be added without redesigning the database.

## Accessibility and low-resource environments
- WCAG-aligned interface design.
- Keyboard navigation and screen-reader support.
- Low-bandwidth pages and compressed assets.
- Offline-capable reading and export.
- Modest hardware and no mandatory GPU.
- Portable formats such as JSON, CSV, Markdown, HTML, and PDF where appropriate.
- Search that tolerates diacritics and script variation without discarding original spellings.
- Clear date/time zones, localized number formats, and accessible charts.

## Community translation governance
Contributors should be credited by consent, and sensitive identities need not be public. Establish review roles, conflict-of-interest disclosure, terminology glossaries, and a process to challenge or correct translations. No language community should be treated as a single political or cultural viewpoint.
