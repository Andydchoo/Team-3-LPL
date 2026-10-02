# RevenueTwin shared contracts — v1

These contracts implement the approximate shapes in MASTER.md. They are the
integration boundary for all five owners. Coordinate changes before updating
them; the Python types are in `revenue_engine/contracts.py` and machine-readable
definitions are in `contracts/revenuetwin.schema.json`.

## Public interfaces

| Interface | Return value | Owner | Current status |
|---|---|---|---|
| `get_revenue_case(case_id)` | RevenueCase dictionary | Engine | CASE-001 implemented |
| `get_case_evidence(case_id)` | Ordered list of Evidence dictionaries | Engine contract; AWS storage adapter | CASE-001 local evidence implemented |
| `investigate_case(case_id)` | Investigation dictionary | AI / Bedrock | Contract only |
| `record_review(case_id, decision)` | ReviewRecord dictionary | AWS / integration | Contract only |

Import the implemented tools from `revenue_engine`. Case lookups raise `KeyError`
for unknown IDs. Source read failures raise `OSError`; malformed records or
unsupported/ambiguous pricing raise `ValueError`. Integration should retain the
financial finding when AI fails and show an appropriate error, rather than
substituting a guessed result. Returned records are freshly loaded: caller
mutations cannot alter the files or subsequent calls.

The AI is given only the two read-only tools. The application calls record_review
after a human action. No AI tool may record reviews or modify financial records.

## Financial case semantics

- Rates are annual fractions: `0.01` means 1.00%, not 1 basis point.
- Financial calculations use Decimal and ROUND_HALF_UP to cents at the final
  fee boundary. JSON monetary fields are numbers representing USD.
- `annual_difference` is the nonnegative magnitude of expected minus actual.
  `impact_direction` separately identifies potential underbilling, potential
  overbilling, no discrepancy or review-dependent value. Do not sum underbilling
  and overbilling as revenue recovery.
- `as_of_date` is an explicit ISO date. The demo does not use the machine clock
  to decide whether an agreement or exception is active. Effective and expiration
  dates are inclusive. Invalid date ranges require review.
- A dated, explicitly authorized exception overrides the flat agreement rate
  during its validity period. Missing authorization or conflicting records do
  not establish a new contractual rate.
- `actual_annual_fee` for Anderson is the annualized current configuration on
  the evidence's billable AUM. It is not a claim that a full year was charged.
  Posted-fee annualization must specify the billing frequency when added.
- `status` reflects the deterministic finding (`requires_review` or
  `no_discrepancy`). Human decisions are separate review records.
- `anomaly_type` labels a deterministic issue category. The investigation's
  `likely_cause` is an evidence-grounded explanation, not a financial calculation.

## Pricing and uncertainty reserved for subsequent cases

`calculation_method` distinguishes flat, volume, marginal and review-dependent
pricing. CASE-001 implements flat pricing only; declaring another method raises
ValueError until that method is implemented and tested.

Chen requires marginal pricing: $1M at 1.00% plus $1M at 0.75% = $17,500.
For a multi-tier case, `expected_rate` represents the effective blended rate
on billable AUM (0.00875 for Chen), and the evidence retains the full schedule.
The original Stevens example remains volume pricing with one rate on all AUM.

Asset exclusion from billing and exclusion from breakpoint qualification are
distinct inputs. Ramirez must explicitly exclude $250,000 from billable assets;
there is no inferred universal account-type policy for the curated engine.

For Morgan, uncertain contractual financial values may be null, with
`impact_direction` and `calculation_method` set to `review_dependent`. Do not
invent an AUM or turn a discussion note into an authorization. Final Morgan and
Ramirez fixture details must be resolved before those cases are implemented.
CASE-002 through CASE-005 are reserved for Patel, Chen, Ramirez and Morgan;
they are not yet implemented.

## Evidence contract

Evidence includes `evidence_id`, `case_id`, `evidence_type`, `title`, `source_path`
and `content`. `source_path` is a relative object key such as
`evidence/anderson/agreement.json`; it is identical under `data/demo/` and a
future private S3 bucket. It is not proof that an S3 object already exists.
`content` contains the synthetic document's facts, including dates and rates.

The engine owner defines document contents and case-to-evidence mapping. The AWS
owner implements private storage and retrieval while returning the same envelope.
Investigation `evidence_used` IDs must exist in the case's returned evidence.

## Investigation and human review

Investigation statuses are supported_explanation, partial_explanation,
conflicting_evidence, insufficient_evidence and investigation_error.
Evidence strength is high, medium or low; uncertainty belongs in `uncertainties`.
`requires_human_review` is always true. Validate structured output and evidence
references before rendering. No financial arithmetic is delegated to the model.

Review decisions are `send_for_review`, `investigate_further` and `dismiss`.
The application supplies the decision and records a unique `review_id`, the case
ID, `actor: "human"` and a UTC ISO timestamp in `recorded_at`. These are workflow
decisions; they neither authorize nor execute a fee change. Persistence remains
the AWS/integration owner's next deliverable.

## JSON Schema use

The schema's root validates RevenueCase. Other shapes are available at
`#/$defs/Evidence`, `#/$defs/EvidenceList`, `#/$defs/Investigation` and
`#/$defs/ReviewRecord`. Use a Draft 2020-12 validator with format checking at
integration boundaries. JSON Schema checks shape; the engine and integration
tests check arithmetic, dates, matching case IDs and valid evidence references.
