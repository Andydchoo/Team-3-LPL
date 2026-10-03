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
- AI / Bedrock: AWS mode calls the validating investigation adapter for Anderson;
  the agent exposes only the two read-only tools. Morgan's agent and reliability
  checks are also available for direct development against local engine tools.
- AWS / integration: AWS mode retrieves private-S3 evidence and persists human
  review decisions. Keep relative `source_path` values and evidence IDs stable.

Do not edit the presentation code to connect a service. The mock implementations
are deliberately isolated in this module until those integrations are ready.

## Backend selection

`REVENUE_BACKEND=local` is the default. CASE-001 and CASE-005 use the local engine;
investigation and review remain explicitly labeled mocks. Installing an agent
package does not implicitly turn on live calls.

`REVENUE_BACKEND=aws` selects private-S3 case/evidence adapters, the validating
AI-owner handoff and private-S3 review writes for CASE-001. It never falls back to
mock success. Morgan's new fixtures remain local until its S3 storage, permissions,
and live workflow are validated. See `docs/AWS_SETUP.md` for
profile/resource settings and live validation.

Integration adds only mode labels, source evidence visibility and clean error/
retry handling to `app.py`. Layout and the frontend owner's mock case content
are retained; Morgan now displays the AI owner's agreement/billing/discussion
fixtures and an aligned mock explanation in local mode. Session-only review
timestamps follow the shared `Z` format;
starting another review does not revoke any stored AWS record.
