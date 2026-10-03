# RevenueTwin 💰

> **See the revenue you're missing before you miss it.**

RevenueTwin checks whether advisory agreements and actual billing remain aligned,
protecting the practice from potential underbilling and clients from potential
overbilling. Deterministic code calculates financial findings; AI investigates
evidence; humans choose consequential actions.

Its digital revenue twin helps an advisory practice answer three questions:

1. **What should we be earning?**
2. **What are we actually earning?**
3. **Why is there a difference?**

This repository combines the original FeeAudit reconciliation code and contributor
history with the five-owner RevenueAudit requirements. The authoritative product
specification is [docs/MASTER.md](docs/MASTER.md). The shared integration contract
is [docs/CONTRACTS.md](docs/CONTRACTS.md), and the work split and handoff process
are in [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md).

## FeeAudit

**FeeAudit** is RevenueTwin's core fee-audit component. Its audit scope includes:

- Potential underbilling and overbilling
- Incorrect fee breakpoints and householding errors
- Unbilled accounts and fee waiver errors

The deterministic foundation, frontend and Anderson investigation agent are
connected. Live validation of the complete user workflow remains the next gate.

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
CASE-001 with local storage. The frontend calls its services through
`ui.services`, which connects the AWS adapters in explicit AWS mode. The pulled Streamlit
frontend works locally; AWS adapters and review storage are prepared with offline
tests. Event identity, private S3 evidence and a real Bedrock text response have
now passed live validation. The AI owner's Anderson package is integrated with
S3-backed tools and paced Bedrock clients; its live tool loop and full human-review
workflow still require validation. Their interfaces are defined in the shared contract.

Run the frontend without credentials:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-aws.txt
$env:REVENUE_BACKEND = 'local'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Local mode labels its mock investigation and session-only reviews. Use
`REVENUE_BACKEND=aws` only with the profile/resource settings and handoff described
in [docs/AWS_SETUP.md](docs/AWS_SETUP.md). AWS mode supports Anderson and never
replaces failed requests with mock success.

## Repository layout

| Location | Responsibility |
|---|---|
| `revenue_engine/` | Import-safe case tools, Decimal calculations and shared Python types |
| `contracts/revenuetwin.schema.json` | Shared JSON Schema definitions |
| `app.py`, `ui/` | Streamlit frontend and explicit local/AWS service boundary |
| `integration/`, `infra/` | AWS configuration, private S3 evidence/reviews, AI handoff validation and IAM templates |
| `investigation/` | AI owner's Bedrock tool loop, structured investigation and Anderson reliability checks |
| `data/demo/` | Curated case inputs and synthetic source evidence |
| `tests/` | Financial, evidence, date and legacy regression checks |
| `docs/MASTER.md`, `docs/owners/` | Product requirements and owner prompts |
| `scripts/`, original `data/*.json` | Legacy FeeAudit bulk reconciliation demo |

## Legacy FeeAudit dataset

The original 50-household dataset and its eight seeded anomalies remain available.
The legacy report is a separate volume-pricing demonstration, and its saved
summary is not the authoritative dashboard source for the curated demo cases.

The original Stevens example uses **volume pricing**: $2.2M household AUM
qualifies for 0.75% on all assets, while billing applies 0.90%. The annualized
potential overbilling is $3,300. This is separate from Anderson and from Chen's
planned marginal-tier example.

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

## AWS integration plan

The AWS owner's setup commands, private evidence adapter and live preflight are
available in [docs/AWS_SETUP.md](docs/AWS_SETUP.md). Install `requirements-aws.txt`
in `.venv` for AWS checks and the complete offline integration test suite.
Live access requires the event's temporary credentials and assigned bucket/model
settings.

The first live workflow uses **Amazon Bedrock** for evidence investigation and
**private Amazon S3** for synthetic documents, with deterministic Python tools
called by the application. The first AWS milestone is prepared locally; live
identity, bucket privacy/evidence access and a real Nova Lite response have passed
the access preflight. The agent's tool loop and human-review UI flow still need
live validation before the full integration is considered ready.

Amazon Textract, AWS Lambda, AWS Step Functions and Amazon DynamoDB are future
options. Add them only after the Anderson workflow works and a concrete need
justifies them, as specified in `docs/MASTER.md`.

## Next integration milestone

Complete Anderson through Streamlit, live Bedrock tool calls, private S3 evidence,
and a human-selected review action. Then add Patel, Chen, Ramirez and Morgan.
Use the minimal architecture in the master specification: Streamlit, one Bedrock
investigation agent, normal Python tools and private S3 evidence. All demo data
must be synthetic.

## Vision

FeeAudit is the first product. The long-term goal is for RevenueTwin to become
the revenue operating system for wealth management, moving firms from reactive
billing audits to proactive revenue intelligence with human governance.

**Know what you should earn. Know what you earned. Know why they're different.**
