# Deterministic revenue engine

This package owns authoritative financial calculations and the local
`get_revenue_case` / `get_case_evidence` interfaces. It does not own Streamlit,
Bedrock prompts, S3, review persistence, or business-pitch content.

## Integration boundary

Keep these contracts stable when adding cases:

```python
from revenue_engine import get_case_evidence, get_revenue_case
```

Financial truth is computed with `Decimal` and rounded to cents only at the fee
boundary. The engine returns plain JSON-compatible dictionaries to the UI and
AI layers. Evidence IDs and relative `source_path` values are stable join keys;
the AWS owner may change storage without changing those shapes.

## Current scope

- `CASE-001` / Anderson: implemented end to end with local synthetic evidence.
- Flat pricing: implemented.
- Marginal-tier calculation helper: implemented and tested for the Chen model.
- `CASE-002` Patel (flat, client overbilling), `CASE-003` Chen (marginal tiers,
  $17,500 expected) and `CASE-004` Ramirez (explicit `excluded_assets` in the
  agreement): implemented with local synthetic evidence. Regenerate fixtures
  with `python scripts/build_secondary_cases.py`.
- `CASE-005` Morgan: review-dependent; no fee impact is computed.
- Assumption to confirm: Ramirez household AUM is a synthetic $1.0M, so
  expected $6,000 vs billed $8,000 (the $2,000 difference is the 529 exclusion).

The frontend adapter in `ui/services.py` is the merge point. Do not import
Streamlit or AWS code into this package.
