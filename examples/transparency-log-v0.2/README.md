# v0.2 Transparency Log Example

All values in `entries.json` are synthetic. The digests do not identify real sources or records.

From the repository root, after installing the project:

```bash
# Build a tree head for the two synthetic entries
ojek log-v2 head examples/transparency-log-v0.2/entries.json \
  --log-id example.newsroom.local/main \
  --issued-at 2026-11-22T00:05:00Z \
  --output /tmp/ojek-tree-head.json

# Verify the tree-head digest
ojek log-v2 verify-head /tmp/ojek-tree-head.json
```

The tree head is unsigned. The example demonstrates format and local verification only; it does not create a network service, trusted timestamp, witness attestation, or claim about source truth.
