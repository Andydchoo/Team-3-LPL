# RevenueTwin frontend boundary

`app.py` owns Streamlit layout, state, and presentation. The UI calls only the
functions exported by `ui.services`:

```text
get_revenue_case(case_id)    -> RevenueCase
get_case_evidence(case_id)   -> list[Evidence]
investigate_case(case_id)    -> Investigation
record_review(case_id, decision) -> ReviewRecord
```

This is the merge boundary for the other owners:

- Revenue engine: keep `RevenueCase` and `Evidence` shapes compatible with
  `revenue_engine/contracts.py` and `docs/CONTRACTS.md`.
- AI / Bedrock: replace the body of `investigate_case` or add an adapter that
  returns the documented `Investigation` shape. Do not add review writes to the
  AI path.
- AWS / integration: replace `record_review` with persistence and, if needed,
  replace `get_case_evidence` with the private-S3 adapter. Keep relative
  `source_path` values and evidence IDs stable.

Do not edit the presentation code to connect a service. The mock implementations
are deliberately isolated in this module until those integrations are ready.

## Backend selection

`REVENUE_BACKEND=local` is the default. CASE-001 uses the real local engine;
investigation and review remain explicitly labeled mocks. Installing an agent
package does not implicitly turn on live calls.

`REVENUE_BACKEND=aws` selects private-S3 case/evidence adapters, the validating
AI-owner handoff and private-S3 review writes for CASE-001. It never falls back to
mock success. Secondary cases remain local fixtures. See `docs/AWS_SETUP.md` for
profile/resource settings and live validation.

Integration adds only mode labels, source evidence visibility and clean error/
retry handling to `app.py`. Layout and the frontend owner's mock case content
are retained. Session-only review timestamps now follow the shared `Z` format;
starting another review does not revoke any stored AWS record.
