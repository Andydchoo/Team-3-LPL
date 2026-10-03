# Five-owner work and integration

This repository is the shared source of truth. Owner prompts are in `docs/owners/`;
the coordinator is an additional responsibility of one technical owner, not a
sixth teammate. MASTER.md sets product scope and CONTRACTS.md sets interfaces.

| Owner | Owned locations / deliverables | Starting dependency |
|---|---|---|
| Revenue engine | `revenue_engine/`, `data/demo/cases/`, evidence content, financial tests, shared contracts | CASE-001 foundation available |
| AI / Bedrock | `investigation/`; investigate_case, two tool integrations, response validation | Anderson contribution integrated; two live S3-backed investigations passed |
| Frontend | `app.py` and `ui/`; dashboard, evidence viewer, human controls | Pulled frontend works in local demo mode; services select local or AWS explicitly |
| AWS / integration | `integration/`, `infra/`; credentials/config, S3 storage adapter, review persistence, integration tests | Anderson live workflow and human review write/read-back passed on the feature branch |
| Business / pitch | Planned `docs/pitch/`; product story, synthetic impact narrative, acquisition thesis, rehearsal | Agreed financial example and honest capability status |

The engine owns evidence contents; AWS owns storage/access. The frontend calls
record_review after the human chooses a decision; AI cannot access that tool.
Coordinate shared schema changes and keep storage details out of the UI and AI.

## Simultaneous and staggered contributions

Each teammate uses their own checkout and `codex/<role>-<change>` feature branch.
Avoid concurrent writes from multiple chats or teammates in the same checkout.
Keep changes scoped to the owned areas and use small PRs. Preserve each
contributor's commits and authorship; the coordinator reviews and integrates
changes into a stable main branch.

Each handoff or PR should state:

1. What works and the command to run or test it.
2. Which contracts and fixtures it uses.
3. Which dependencies are live, mocked or missing.
4. The next step and any decision another owner must make.

Check in these handoff notes with the owner's work so someone starting later can
continue without needing a live meeting. Owner prompts describe responsibilities;
they do not automatically coordinate file edits or enforce Git ownership.

## Integration gates

1. **Foundation:** shared contracts, CASE-001 local tools, correct $12,000 / $9,000
   / $3,000 result, evidence and financial tests.
2. **First live vertical slice:** Streamlit selects Anderson; Bedrock actually
   calls both tools; evidence comes from private S3; a validated explanation is
   rendered; a human action is persisted.
3. **Secondary cases:** Patel protects clients, Chen verifies marginal tiers,
   Ramirez verifies billing exclusions, Morgan surfaces unresolved authorization.
4. **Freeze:** stable main, clean retry/error states, working credentials,
   clearly labeled synthetic metrics and rehearsed demo.

Integrate the Anderson flow early. The frontend may use explicitly labeled mocks
while services are unfinished; a mock investigation must never be presented as a
live Bedrock result. Use the first live gate before expanding AWS architecture.

## Current status and remaining engine work

Foundation: implemented in this branch; run the README test command to verify.
CASE-001 uses a fixed January 1, 2026 evaluation date and three local synthetic
evidence documents. The frontend contribution is merged into main and pulled into
this checkout. AWS setup, S3 adapters, review storage and frontend service/error
connections are implemented locally with offline tests. The first AWS access
milestone has passed in the event account: identity, us-east-1, private S3 evidence
and a real Nova Lite response. The AI owner's Anderson investigation package is
integrated. Two real Streamlit investigations called both S3-backed tools and
returned validated explanations; the coordinator's `investigate_further` choice
was saved and read back from S3. The Anderson vertical slice gate passes on
`codex/aws-integration`; review/merge into stable main and visual rehearsal remain.
See AWS_SETUP.md and `validation/aws-anderson-2026-10-03.json` for the evidence.

The AWS feature branch retains the authorship of the AI owner's four Anderson
commits (one-tool smoke, two-tool smoke, structured investigation, and reliability
checks). AWS changes connect those tools to private S3 and add bounded, paced
clients. Later Morgan fixtures and engine changes from the AI branch are deferred
until their assumptions are coordinated with the engine owner and shared scope.

The legacy dataset and report remain a separate regression demo. Follow-up engine
work includes volume/marginal pricing, curated secondary cases and corrected
legacy household summaries: structural-only issues must count as flagged;
expected totals must include unbilled assets exactly once and exclude duplicate
charges from expected fees; exclusion rules and impact aggregation need explicit
semantics. Legacy 8/8 detection coverage does not prove those dollar totals.
