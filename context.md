# Project Context: RevenueTwin / FeeAudit

## Hackathon Theme
**Startup from the Future** — Build the Startup LPL Would Want to Buy

Envision the future of wealth management and build a compliant AI-powered startup that solves a meaningful challenge for advisors, investors, or the teams that support them. Then pitch why LPL should acquire your startup.

---

## Target Categories

| Category | Why We're Targeting It |
|---|---|
| **Startup We'd Buy Tomorrow** | One strong pitch deck + working demo can win this |
| **Biggest Business Impact** | Same pitch as above — moves a number LPL cares about |

> **Strategy:** These two categories are essentially the same pitch. Doubling down here means more time building instead of splitting effort across two different demo tracks.

---

## The Pitch

**Every advisory practice gets a real-time digital twin of its revenue.**

RevenueTwin predicts what the practice _should_ earn, detects where money will leak _before_ billing occurs, and deploys AI agents to fix the problem — with advisor approval.

### One-Line Analogy
> "The Revenue Cycle Management company for wealth management" — the same category Waystar and athenahealth occupy in healthcare, applied to advisory billing.

---

## Product: FeeAudit (Core MVP)

### One-Sentence Pitch
A practice management analytics tool that audits advisor billing schedules to find unlinked household tier discounts, unbilled accounts, and revenue drift.

### Target Users
- Practice Managers
- OSJ Principals
- LPL CFO Solutions Consultants

---

## Problem Statement

Advisory firms lose **2-4% of annual revenue** due to:
- Manual fee-schedule setup errors
- Failed breakpoint discounts on aggregated household assets
- Forgotten fee waivers

### Current (Broken) Workflow
Annual billing audits are conducted by manually sampling billing reports against client fee agreements in spreadsheets.

---

## Why This Matters to LPL

1. **Drives CFO/Business Solutions adoption** — directly recovers recurring top-line revenue for advisory practices.
2. **Echoes LPL's own stated thesis** — Steinmeier noted on the Q2 call that advisors who adopt LPL's business/CFO solutions grow ~2x faster than those who don't. FeeAudit is a literal instance of that claim.
3. **Massive addressable impact** — if even half of LPL's ~1,000 largest practices have this leakage, recovered revenue compounds into real, durable dollars every single year (not a one-time fix).
4. **Sellable beyond LPL** — every broker-dealer and RIA aggregator has the same billing-drift problem, making acquisition more compelling than "build in-house."

---

## Proposed Solution

Automated billing engine that reconciles client advisory agreements (scanned PDFs) against actual quarterly billing deduction logs in ClientWorks, identifying discrepancies.

### Example User Journey
1. Engine scans **400 client accounts**
2. Finds that the "Stevens Family" reached **\.2M aggregate assets**, qualifying them for a **75 bps tier** — but they are still being billed at **90 bps** across individual sub-accounts
3. Flags a **\,300 overcharge risk** and suggests a fee schedule realignment

---

## Technical Architecture

FastAPI Backend
  -> Pandas Data Reconciliation Pipeline
    -> MongoDB
      -> Next.js Financial Table Dashboard

### AI Component
- **Document text extraction**: OCR + LLM to read client advisory agreements
- Parses tiered fee tables into structured JSON schemas

### Data Required
- Synthetic client advisory agreement contracts
- Quarterly billing CSV transaction files

---

## MVP Scope (One-Day Build)

**Input:** Upload mock fee schedules + billing logs

**Output:** Dashboard instantly displays:
- Total revenue at risk
- Overcharged accounts
- Unbilled assets

### Demo Sequence
Run reconciliation on a **50-account mock firm** -> Identify **\,200 in revenue leakage** and **2 accounts billed incorrectly** within **5 seconds**

The demo moment is simple and punchy: run it, watch a dollar figure appear in seconds. That's a strong close for a judge.

---

## Stretch Features
- One-click generation of ClientWorks billing schedule adjustment batch files

---

## Risks
- Complex custom fee agreements with non-standard grandfathered clauses

---

## Differentiation
Solves a high-dollar operational headache that traditional portfolio accounting platforms overlook.

---

## Category Strategy Notes

- **"Startup We'd Buy Tomorrow" + "Biggest Business Impact"** -> Same pitch, same demo, maximum focus
- **Avoid** "Best Customer Experience" + "Best Technical Execution" as a pair — they reward different kinds of polish (delightful UI vs. hard engineering), and chasing both in one day usually means neither is fully baked
