# RevenueTwin — Team-3-LPL

RevenueTwin checks whether advisory agreements and actual billing remain aligned,
protecting the practice from potential underbilling and clients from potential
overbilling. Deterministic code calculates financial findings; AI investigates
evidence; humans choose consequential actions.

This repository combines the original FeeAudit reconciliation code and contributor
history with the five-owner RevenueAudit requirements. The authoritative product
specification is [docs/MASTER.md](docs/MASTER.md). The shared integration contract
is [docs/CONTRACTS.md](docs/CONTRACTS.md), and the work split and handoff process
are in [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md).

## Working foundation

Python 3.11 or newer is sufficient; the engine and financial tests use only the
standard library. Run these commands from the repository root:

```powershell
python -m unittest discover -s tests -v
python -c "import json; from revenue_engine import get_revenue_case; print(json.dumps(get_revenue_case('CASE-001'), indent=2))"
python -c "import json; from revenue_engine import get_case_evidence; print(json.dumps(get_case_evidence('CASE-001'), indent=2))"
```

CASE-001 is the fictional Anderson Household, evaluated on January 1, 2026:

| Finding | Annual amount |
|---|---:|
| Expected fee: $1.2M at 1.00% | $12,000 |
| Current billing configuration: $1.2M at 0.75% | $9,000 |
| Potential underbilling | $3,000 |

The authorized 0.75% pricing exception ended on December 31, 2025. Three readable
synthetic evidence documents are stored under `data/demo/evidence/anderson/`.
Annualized impact is a recurring run-rate estimate, not realized recovery.

`get_revenue_case(case_id)` and `get_case_evidence(case_id)` are implemented for
CASE-001 with local storage. Streamlit, live Bedrock investigation, S3 retrieval,
and human review persistence remain work for their respective owners. Their
interfaces are defined in the shared contract.

## Repository layout

| Location | Responsibility |
|---|---|
| `revenue_engine/` | Import-safe case tools, Decimal calculations and shared Python types |
| `contracts/revenuetwin.schema.json` | Shared JSON Schema definitions |
| `data/demo/` | Curated case inputs and synthetic source evidence |
| `tests/` | Financial, evidence, date and legacy regression checks |
| `docs/MASTER.md`, `docs/owners/` | Product requirements and owner prompts |
| `scripts/`, original `data/*.json` | Legacy FeeAudit bulk reconciliation demo |

## Legacy FeeAudit dataset

The original 50-household dataset and its eight seeded anomalies remain available.
The legacy report is a separate volume-pricing demonstration, and its saved
summary is not the authoritative dashboard source for the curated demo cases.

```powershell
# Explicitly writes data/reconciliation_results.json:
python scripts/reconciliation_engine.py

# Explicitly regenerates the original dataset and changes its UUIDs:
python scripts/generate_synthetic_data.py
```

Importing `scripts.reconciliation_engine` performs no reads, writes or reporting.
Its `reconcile(...)` function accepts records and returns the legacy result shape.
The generator remains an explicit standalone script and is not an application
import. Do not run it to populate the curated demo cases.

## Next integration milestone

Complete Anderson through Streamlit, live Bedrock tool calls, private S3 evidence,
and a human-selected review action. Then add Patel, Chen, Ramirez and Morgan.
Use the minimal architecture in the master specification: Streamlit, one Bedrock
investigation agent, normal Python tools and private S3 evidence. All demo data
must be synthetic.
