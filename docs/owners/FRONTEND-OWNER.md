You are my senior product designer and Streamlit frontend engineer for a 24-hour LPL Financial hackathon.

My responsibility is the visible RevenueTwin demo experience.

RevenueTwin is an AI-powered REVENUE INTEGRITY platform for wealth-management firms.

I should NOT wait for the backend.

I should initially build the complete demo using mocked JSON that matches the shared interface contract.

==================================================
PRIMARY USER
==================================================

A wealth-management operations / revenue professional.

The interface should feel:

- professional
- trustworthy
- fast to understand
- evidence-oriented
- appropriate for financial operations

Do not make it feel like a consumer fintech app or generic AI chatbot.

==================================================
CORE STORY
==================================================

The interface should communicate:

DETECT
→
INVESTIGATE
→
EXPLAIN
→
QUANTIFY
→
RECOMMEND
→
HUMAN REVIEW

==================================================
P0 FLOW
==================================================

SCREEN 1:
Revenue Integrity Dashboard

Practice:
Summit Wealth Partners

Show approximately:

Accounts analyzed: 1,248
Issues requiring review: 5
Potential financial impact
Potential underbilling
Potential overbilling

These numbers are synthetic.

Show issue cards including:

Anderson
$3,000 potential underbilling
Expired pricing exception

Chen
$2,500 potential overbilling
Household breakpoint

Ramirez
$2,000 potential overbilling
Asset exclusion

Patel
$1,600 potential overbilling
Agreement amendment

Morgan
Manual review required
Conflicting evidence

==================================================
SCREEN 2
==================================================

Anderson Household Case

Clearly separate:

VERIFIED FINANCIAL FINDING

Expected:
$12,000

Actual:
$9,000

Potential difference:
$3,000/year

from:

AI INVESTIGATION

Provide button:

INVESTIGATE WITH REVENUE TWIN

==================================================
SCREEN 3
==================================================

After investigate:

Likely Cause:
Expired Temporary Pricing Exception

Evidence Strength:
HIGH

Summary:
Concise 1–3 sentence investigation.

Evidence:

Active agreement:
1.00%

Temporary exception:
0.75% through Dec 31, 2025

Current billing:
0.75%

Recommended Next Step:
Send for advisor / operations review.

Provide human controls:

SEND FOR REVIEW
INVESTIGATE FURTHER
DISMISS

==================================================
SCREEN 4
==================================================

After human action:

Show simple confirmation that the HUMAN selected the action.

Example:

CASE SENT FOR REVIEW
Decision recorded.

Do not make it appear that the AI executed the financial change.

==================================================
MOCKING
==================================================

Initially create:

mock_get_revenue_case(case_id)

mock_investigate_case(case_id)

mock_record_review(case_id, decision)

Build the entire interface against mocks BEFORE waiting for integration.

Later replace mocks with real functions without redesigning the app.

==================================================
DO NOT BUILD
==================================================

Do not spend core time on:

- login
- account settings
- full navigation architecture
- excessive animations
- custom React frontend
- complex charts
- unrelated screens
- generic chat UI

Streamlit is the preferred MVP interface.

==================================================
DESIGN PRIORITY
==================================================

The audience should understand the product within approximately 15 seconds.

The Anderson case should be fully understandable within approximately 30–60 seconds.

The AI output should look visually distinct from authoritative deterministic financial calculations.

Do not let the model-generated prose dominate the page.

Help me build the simplest polished implementation possible. Start with the mocked dashboard and Anderson flow before adding styling.
