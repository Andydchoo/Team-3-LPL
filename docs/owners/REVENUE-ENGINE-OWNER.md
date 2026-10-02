You are my senior backend engineer for a 24-hour LPL Financial hackathon.

My responsibility is the deterministic financial engine and synthetic dataset for a startup called RevenueTwin.

RevenueTwin separates responsibilities:

CODE = authoritative financial facts
AI = contextual investigation
HUMAN = consequential decision

Therefore my implementation must be predictable, testable and auditable.

==================================================
MY DELIVERABLES
==================================================

I own:

- shared case schema
- synthetic practice data
- deterministic fee calculations
- expected vs actual comparisons
- annualized financial impact
- anomaly metadata
- evidence metadata
- get_revenue_case(case_id)
- get_case_evidence(case_id)
- tests for financial calculations

I do NOT own the Streamlit UI or Bedrock prompting.

==================================================
FIRST PRIORITY
==================================================

Implement CASE-001 first.

Anderson Household:

AUM:
$1,200,000

Active agreement:
1.00%

Current billing:
0.75%

Expected annual fee:
$12,000

Actual annualized fee:
$9,000

Difference:
$3,000 potential underbilling/year

Evidence:

Active Agreement:
1.00%

Temporary Pricing Exception:
0.75%
Jan 1, 2025 – Dec 31, 2025

Current Billing:
0.75%

==================================================
FUNCTION CONTRACTS
==================================================

Implement predictable interfaces:

get_revenue_case(case_id)

get_case_evidence(case_id)

Potential helper functions:

calculate_expected_fee(...)
calculate_actual_fee(...)
annualize_impact(...)
compare_expected_vs_actual(...)

Do not expose unnecessary complexity to the frontend or agent.

==================================================
CASE SCHEMA
==================================================

Use approximately:

{
"case_id": "CASE-001",
"household": "Anderson Household",
"anomaly_type": "expired_pricing_exception",
"aum": 1200000,
"expected_rate": 0.01,
"actual_rate": 0.0075,
"expected_annual_fee": 12000,
"actual_annual_fee": 9000,
"annual_difference": 3000,
"impact_direction": "potential_underbilling",
"evidence_ids": [],
"status": "requires_review"
}

Maintain compatibility with this contract unless the team explicitly agrees to change it.

==================================================
SECONDARY CASES
==================================================

After Anderson:

Patel:
$800K AUM
agreement 0.80%
billing 1.00%
$1,600/year potential overbilling

Chen:
$2M household
first $1M at 1.00%
next $1M at 0.75%
expected $17,500
actual $20,000
$2,500 potential overbilling

Ramirez:
$250K excluded assets incorrectly included
0.80% fee
$2,000 potential overbilling

Morgan:
agreement 1.00%
billing 0.75%
conflicting evidence
financial value may remain review-dependent

==================================================
IMPORTANT
==================================================

Do not use the language model for arithmetic.

Do not create hundreds of useless fake accounts.

We only need enough real records to support the demo.

Use clean, human-readable synthetic data.

Prioritize correctness over architectural sophistication.

==================================================
TESTS
==================================================

Create straightforward tests for:

- Anderson expected fee
- Anderson actual fee
- Anderson difference
- Chen breakpoint calculation
- Patel difference
- Ramirez asset exclusion

If there is ambiguity in the financial model, flag it before inventing a rule.

Help me implement this incrementally, beginning with the shared schemas and CASE-001.
