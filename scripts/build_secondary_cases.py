"""Write the curated CASE-002..004 fixtures under data/demo (synthetic only).

Run: python scripts/build_secondary_cases.py
Patel = agreement amendment not billed; Chen = marginal household tiers;
Ramirez = explicit $250K billing exclusion missing from billing config.
"""

import json
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "data" / "demo"


def write(rel: str, obj: dict) -> None:
    path = DEMO / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def evidence(case_id, folder, name, ev_id, ev_type, title, content):
    rel = f"evidence/{folder}/{name}.json"
    write(rel, {
        "evidence_id": ev_id, "case_id": case_id, "evidence_type": ev_type,
        "title": title, "source_path": rel,
        "content": {**content, "synthetic": True},
    })
    return rel


def case(case_id, household, anomaly, aum, method, paths):
    write(f"cases/{case_id}.json", {
        "case_id": case_id, "household": household, "anomaly_type": anomaly,
        "aum": aum, "as_of_date": "2026-01-01", "calculation_method": method,
        "evidence_paths": paths,
    })


def billing(household, rate, aum, since, note):
    return {
        "household": household, "annual_rate": rate, "billable_aum": aum,
        "billing_frequency": "quarterly", "effective_date": since,
        "status": "active", "note": note,
    }


# CASE-002 Patel: executed amendment (0.80%) never reached billing (1.00%).
case("CASE-002", "Patel Household", "agreement_amendment", 800000, "flat", [
    evidence("CASE-002", "patel", "amendment", "patel_amendment",
             "advisory_agreement", "Patel executed fee schedule amendment (synthetic)", {
                 "household": "Patel Household", "annual_rate": 0.008,
                 "effective_date": "2025-10-15", "expiration_date": None,
                 "pricing_method": "flat",
                 "clause": "Amended advisory rate of 0.80% on household assets."}),
    evidence("CASE-002", "patel", "custodian_billing", "patel_custodian_billing",
             "billing_configuration", "Patel current billing configuration (synthetic)",
             billing("Patel Household", 0.01, 800000, "2024-01-01",
                     "Legacy 1.00% schedule still configured")),
])

# CASE-003 Chen: $2M household; marginal 1.00% first $1M, 0.75% next $1M.
case("CASE-003", "Chen Household", "household_breakpoint", 2000000, "marginal", [
    evidence("CASE-003", "chen", "schedule_b", "chen_tier_schedule",
             "advisory_agreement", "Chen marginal tier schedule (synthetic)", {
                 "household": "Chen Household", "annual_rate": 0.00875,
                 "effective_date": "2024-06-01", "expiration_date": None,
                 "pricing_method": "marginal",
                 "tiers": [
                     {"lower": 0, "upper": 1000000, "annual_rate": 0.01},
                     {"lower": 1000000, "upper": None, "annual_rate": 0.0075},
                 ],
                 "note": "annual_rate is informational; tiers govern."}),
    evidence("CASE-003", "chen", "billing", "chen_custodian_billing",
             "billing_configuration", "Chen current billing configuration (synthetic)",
             billing("Chen Household", 0.01, 2000000, "2024-06-01",
                     "Related accounts billed flat 1.00%; not householded")),
])

# CASE-004 Ramirez: agreement excludes $250K; billing still includes it.
# Household AUM of $1.0M is an assumed synthetic total (see docs/CONTRACTS.md).
case("CASE-004", "Ramirez Household", "asset_exclusion", 1000000, "flat", [
    evidence("CASE-004", "ramirez", "rider", "ramirez_exclusion_rider",
             "advisory_agreement", "Ramirez agreement with asset exclusion (synthetic)", {
                 "household": "Ramirez Household", "annual_rate": 0.008,
                 "effective_date": "2024-09-01", "expiration_date": None,
                 "pricing_method": "flat", "excluded_assets": 250000,
                 "exclusion_note": "Account 529-RAM (College Savings) excluded from billable AUM"}),
    evidence("CASE-004", "ramirez", "billing", "ramirez_custodian_billing",
             "billing_configuration", "Ramirez current billing configuration (synthetic)",
             billing("Ramirez Household", 0.008, 1000000, "2024-09-01",
                     "529 account still marked billable")),
])
print("Wrote CASE-002..004")
