# Blueprint: Distributed Public-Information Catalog

**Proposal v0.1 — metadata model only; no global crawler or central index is implemented.**

## Purpose
Make it easier for journalists and communities to discover authoritative public-interest records across jurisdictions while keeping catalogs federated and independently maintained.

## Catalog entry
A catalog entry should describe a public source or collection, not make a claim about the truth of its contents.

Suggested fields:
- Stable catalog ID.
- Institution or publisher name.
- Country and subnational jurisdiction identifiers.
- Institution type and subject areas.
- Official homepage and specific collection URL.
- Record formats and languages.
- Access method and known rate limits.
- Publication/update frequency, if known.
- Rights and reuse terms URL.
- Accessibility and low-bandwidth notes.
- Last checked date and checker role.
- Known gaps, outages, and historical coverage.
- Contact / correction channel.

## Source classes
- Legislation, regulations, constitutions, court decisions.
- Public budgets, procurement, contracts, and audits.
- Legislative proceedings and public meeting records.
- Environmental monitoring and public health statistics.
- Election administration and official results.
- Corporate and beneficial ownership registries where lawfully public.
- Public-interest journalism archives and community collections.
- Human-rights instruments and official treaty repositories.

## Quality controls
- Prefer the issuing authority's canonical portal.
- Distinguish official source from third-party mirror.
- Record the exact jurisdiction and time period.
- Check whether the portal is current, complete, and searchable.
- Never infer legal authority from a domain name alone.
- Keep a correction history when an endpoint changes.
- Record inaccessible or removed resources without bypassing access controls.

## Federation model
Each regional or topical catalog is a repository or signed data package. Nodes may subscribe to selected catalogs and maintain local copies. A shared vocabulary and schema can support discovery without a central service. Any public aggregation should disclose its coverage, freshness, selection criteria, and missing regions.

## Initial pilot recommendation
Start with a small, manually verified Colorado public-information catalog. Include official state statutes and legislative resources, state courts, state agencies, local government portals, county records, and public meeting archives. Expand only after source authority, jurisdiction metadata, and update responsibilities are clear.
