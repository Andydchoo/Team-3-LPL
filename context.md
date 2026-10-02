# RevenueTwin project context

The project requirements and owner prompts have been consolidated into this
repository from RevenueAudit. Use [docs/MASTER.md](docs/MASTER.md) as the
authoritative product specification and [docs/CONTRACTS.md](docs/CONTRACTS.md)
for the shared interfaces.

RevenueTwin is a revenue-integrity platform for wealth-management operations.
It protects both clients and the practice by comparing expected contractual fees
with billing, then presenting evidence for human review.

The hackathon MVP architecture is Streamlit, one Amazon Bedrock investigation
agent, deterministic Python tools and synthetic evidence in private Amazon S3.
The first integration goal is the complete Anderson workflow. Technical owners
can start independently against the shared contract and curated fixtures.

The earlier FastAPI/MongoDB/Next.js proposal and unsupported industry figures
have been superseded. Git history preserves that earlier context. The product
and pitch should distinguish implemented capabilities, synthetic examples and
future plans; factual industry or LPL claims require supporting sources.
