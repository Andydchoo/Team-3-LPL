"""
generate_synthetic_data.py
==========================
Generates synthetic FeeAudit data: ~50 households, 1-4 sub-accounts each,
advisory agreements with tiered fee schedules, and quarterly billing logs.

8 deliberately seeded errors are injected so the reconciliation engine can
"discover" them during the demo. Each error is tagged with an _injected_error
field (stripped before production use) so we can verify demo coverage.

Outputs → ../data/
    advisory_agreements.json
    household_mappings.json
    billing_logs.json
    seeded_errors_manifest.json   ← cheat sheet for presenters
"""

import json
import uuid
import random
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NUM_HOUSEHOLDS = 50
BILLING_PERIOD = {"year": 2025, "quarter": 3}
BILLING_DATE = "2025-07-01"
PRACTICE_ID = str(uuid.uuid4())
ADVISOR_IDS = [str(uuid.uuid4()) for _ in range(6)]  # 6 advisors in the firm

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"

# ---------------------------------------------------------------------------
# Name pools (no Faker dependency — keeps setup zero-friction)
# ---------------------------------------------------------------------------
LAST_NAMES = [
    "Stevens", "Whitaker", "Nakamura", "Patel", "O'Brien", "Johansson",
    "Fernandez", "Kim", "Abernathy", "Liu", "Morrison", "Gupta",
    "Thornton", "Bianchi", "Delacroix", "Huang", "Okafor", "Petrov",
    "Sandoval", "Andersen", "Yilmaz", "Dubois", "Kowalski", "Malone",
    "Reeves", "Tanaka", "Vasquez", "Brennan", "Cho", "El-Amin",
    "Fischer", "Goldstein", "Hassan", "Ibrahim", "Jensen", "Kapoor",
    "Larsen", "Mendoza", "Novak", "Ortiz", "Quinn", "Romero",
    "Singh", "Tran", "Ueda", "Volkov", "Walsh", "Xu", "Yamamoto", "Zhao",
    "Crawford", "Donovan", "Eriksson"
]

ACCOUNT_TYPES = ["individual", "joint", "IRA", "Roth IRA", "trust", "529", "other"]
ACCOUNT_TYPE_WEIGHTS = [0.25, 0.25, 0.20, 0.15, 0.10, 0.03, 0.02]

# Standard fee tier schedules — most practices use one of these
FEE_SCHEDULES = {
    "standard": [
        {"tier_label": "Tier 1", "aum_min": 0,       "aum_max": 500000,  "bps": 100},
        {"tier_label": "Tier 2", "aum_min": 500000,   "aum_max": 1000000, "bps": 90},
        {"tier_label": "Tier 3", "aum_min": 1000000,  "aum_max": 2000000, "bps": 80},
        {"tier_label": "Tier 4", "aum_min": 2000000,  "aum_max": 5000000, "bps": 75},
        {"tier_label": "Tier 5", "aum_min": 5000000,  "aum_max": None,    "bps": 60},
    ],
    "premium": [
        {"tier_label": "Tier 1", "aum_min": 0,       "aum_max": 1000000, "bps": 110},
        {"tier_label": "Tier 2", "aum_min": 1000000,  "aum_max": 3000000, "bps": 85},
        {"tier_label": "Tier 3", "aum_min": 3000000,  "aum_max": None,    "bps": 65},
    ],
    "value": [
        {"tier_label": "Tier 1", "aum_min": 0,       "aum_max": 250000,  "bps": 125},
        {"tier_label": "Tier 2", "aum_min": 250000,   "aum_max": 750000,  "bps": 100},
        {"tier_label": "Tier 3", "aum_min": 750000,   "aum_max": 1500000, "bps": 85},
        {"tier_label": "Tier 4", "aum_min": 1500000,  "aum_max": None,    "bps": 70},
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def uid():
    return str(uuid.uuid4())


def pick_aum():
    """Realistic AUM distribution — long tail with most accounts 100k-2M."""
    r = random.random()
    if r < 0.10:
        return round(random.uniform(25_000, 100_000), 2)
    elif r < 0.50:
        return round(random.uniform(100_000, 500_000), 2)
    elif r < 0.80:
        return round(random.uniform(500_000, 1_500_000), 2)
    elif r < 0.95:
        return round(random.uniform(1_500_000, 5_000_000), 2)
    else:
        return round(random.uniform(5_000_000, 15_000_000), 2)


def find_tier(fee_tiers, total_aum):
    """Return the correct tier for a given AUM."""
    for tier in fee_tiers:
        if total_aum >= tier["aum_min"] and (tier["aum_max"] is None or total_aum < tier["aum_max"]):
            return tier
    return fee_tiers[-1]  # fallback to highest tier


def quarterly_fee(aum, bps):
    """Compute one quarter's dollar fee."""
    return round((aum * bps / 10_000) / 4, 2)


# ---------------------------------------------------------------------------
# Generate clean baseline data
# ---------------------------------------------------------------------------
random.seed(42)  # reproducible

households = []
agreements = []
billing_entries = []
seeded_errors = []

used_names = set()

for i in range(NUM_HOUSEHOLDS):
    # Pick a unique household name
    last = LAST_NAMES[i % len(LAST_NAMES)]
    if last in used_names:
        last = f"{last}-{i}"
    used_names.add(last)
    household_name = f"{last} Family"

    hh_id = uid()
    agreement_id = uid()
    advisor_id = random.choice(ADVISOR_IDS)
    schedule_key = random.choice(list(FEE_SCHEDULES.keys()))
    fee_tiers = FEE_SCHEDULES[schedule_key]

    # Generate 1-4 sub-accounts
    num_accounts = random.choices([1, 2, 3, 4], weights=[0.20, 0.35, 0.30, 0.15])[0]
    accounts = []
    for j in range(num_accounts):
        acct_type = random.choices(ACCOUNT_TYPES, weights=ACCOUNT_TYPE_WEIGHTS)[0]
        acct_aum = pick_aum()
        include_in_hh = not (acct_type == "529")  # 529s excluded from breakpoint by default
        accounts.append({
            "account_id": uid(),
            "account_label": f"{last} {acct_type.replace('_', ' ').title()}",
            "account_type": acct_type,
            "current_aum": acct_aum,
            "is_active": True,
            "include_in_household_aum": include_in_hh,
            "opened_date": str(date(2020, 1, 1) + timedelta(days=random.randint(0, 1500))),
            "closed_date": None,
        })

    total_aum = sum(a["current_aum"] for a in accounts if a["include_in_household_aum"])
    correct_tier = find_tier(fee_tiers, total_aum)

    # --- Household Mapping ---
    household = {
        "household_id": hh_id,
        "household_name": household_name,
        "practice_id": PRACTICE_ID,
        "advisor_id": advisor_id,
        "agreement_id": agreement_id,
        "total_aum": round(total_aum, 2),
        "aum_as_of": "2025-06-30",
        "accounts": accounts,
        "tier_qualified": {
            "tier_label": correct_tier["tier_label"],
            "bps": correct_tier["bps"],
        },
        "created_at": "2024-01-15T09:00:00Z",
        "updated_at": "2025-06-30T18:00:00Z",
    }
    households.append(household)

    # --- Advisory Agreement ---
    agreement = {
        "agreement_id": agreement_id,
        "household_id": hh_id,
        "household_name": household_name,
        "advisor_id": advisor_id,
        "practice_id": PRACTICE_ID,
        "effective_date": str(date(2020, 1, 1) + timedelta(days=random.randint(0, 1000))),
        "expiration_date": None,
        "agreement_type": random.choice(["wrap", "AUM", "AUM", "AUM"]),
        "billing_frequency": "quarterly",
        "fee_tiers": fee_tiers,
        "fee_waivers": [],
        "notes": "",
        "source_document_url": f"s3://feeaudit-docs/agreements/{agreement_id}.pdf",
        "parsed_at": "2025-06-15T12:00:00Z",
        "parse_confidence": round(random.uniform(0.88, 0.99), 2),
    }
    agreements.append(agreement)

    # --- Billing Log Entries (one per account, clean) ---
    for acct in accounts:
        bps_to_charge = correct_tier["bps"]
        fee_amt = quarterly_fee(acct["current_aum"], bps_to_charge)

        entry = {
            "entry_id": uid(),
            "account_id": acct["account_id"],
            "household_id": hh_id,
            "practice_id": PRACTICE_ID,
            "advisor_id": advisor_id,
            "billing_period": BILLING_PERIOD,
            "billing_date": BILLING_DATE,
            "aum_billed": acct["current_aum"],
            "bps_charged": bps_to_charge,
            "fee_dollar_amount": fee_amt,
            "billing_method": "in-arrears",
            "fee_type": "advisory",
            "status": "posted",
            "source_system": "ClientWorks",
            "reconciliation": None,
        }
        billing_entries.append(entry)


# ---------------------------------------------------------------------------
# Inject 8 seeded errors — the "discoveries" for demo day
# ---------------------------------------------------------------------------

def error_manifest(error_id, hh_name, error_type, description, dollar_impact):
    """Record for the presenter cheat sheet."""
    return {
        "error_id": error_id,
        "household": hh_name,
        "error_type": error_type,
        "description": description,
        "annual_dollar_impact": dollar_impact,
    }


# --- ERROR 1: Breakpoint crossed — Stevens Family ---
# Household #0 (Stevens) — total AUM pushed above $2M but billed at Tier 3 (80bps)
# instead of Tier 4 (75bps) because sub-accounts weren't aggregated.
err1_hh = households[0]
err1_hh["household_name"] = "Stevens Family"
err1_hh["total_aum"] = 2_200_000.00
err1_tiers = FEE_SCHEDULES["standard"]
err1_hh["tier_qualified"] = {"tier_label": "Tier 4", "bps": 75}

# Fix sub-account AUMs to total 2.2M
err1_hh["accounts"][0]["current_aum"] = 950_000.00
err1_hh["accounts"][0]["account_label"] = "Stevens Joint Brokerage"
err1_hh["accounts"][0]["account_type"] = "joint"
if len(err1_hh["accounts"]) >= 2:
    err1_hh["accounts"][1]["current_aum"] = 750_000.00
    err1_hh["accounts"][1]["account_label"] = "Stevens IRA"
    err1_hh["accounts"][1]["account_type"] = "IRA"
if len(err1_hh["accounts"]) >= 3:
    err1_hh["accounts"][2]["current_aum"] = 500_000.00
    err1_hh["accounts"][2]["account_label"] = "Stevens Roth IRA"
    err1_hh["accounts"][2]["account_type"] = "Roth IRA"
# Trim to 3 accounts
err1_hh["accounts"] = err1_hh["accounts"][:3]

# Ensure the agreement uses the standard schedule
agreements[0]["fee_tiers"] = err1_tiers
agreements[0]["household_name"] = "Stevens Family"

# The ERROR: billing entries still charge 90bps (Tier 2 — the rate when they were under $1M)
for entry in billing_entries:
    if entry["household_id"] == err1_hh["household_id"]:
        entry["bps_charged"] = 90  # WRONG — should be 75
        entry["fee_dollar_amount"] = quarterly_fee(entry["aum_billed"], 90)
        entry["_injected_error"] = "ERR-1"

err1_impact = round((90 - 75) / 10_000 * 2_200_000, 2)  # $3,300/yr
seeded_errors.append(error_manifest(
    "ERR-1", "Stevens Family", "breakpoint_not_applied",
    "Household crossed $2M threshold (now $2.2M) qualifying for 75bps Tier 4, "
    "but all 3 sub-accounts still billed at 90bps (stale Tier 2 rate). "
    "Overcharge: 15bps across $2.2M aggregate.",
    err1_impact
))


# --- ERROR 2: Stale fee schedule — Whitaker Family ---
# Whitaker signed a new agreement in Jan 2025 lowering rates, but billing
# still uses the old schedule.
err2_hh = households[1]
err2_hh["household_name"] = "Whitaker Family"
agreements[1]["household_name"] = "Whitaker Family"
agreements[1]["effective_date"] = "2025-01-15"
agreements[1]["fee_tiers"] = [
    {"tier_label": "Tier 1", "aum_min": 0,       "aum_max": 1000000, "bps": 85},
    {"tier_label": "Tier 2", "aum_min": 1000000,  "aum_max": None,    "bps": 70},
]
# But billing is at OLD rates (100/90)
old_tier_bps = 100 if err2_hh["total_aum"] < 1_000_000 else 90
for entry in billing_entries:
    if entry["household_id"] == err2_hh["household_id"]:
        entry["bps_charged"] = old_tier_bps
        entry["fee_dollar_amount"] = quarterly_fee(entry["aum_billed"], old_tier_bps)
        entry["_injected_error"] = "ERR-2"

new_bps = 85 if err2_hh["total_aum"] < 1_000_000 else 70
err2_impact = round((old_tier_bps - new_bps) / 10_000 * err2_hh["total_aum"], 2)
seeded_errors.append(error_manifest(
    "ERR-2", "Whitaker Family", "stale_fee_schedule",
    f"New agreement effective 2025-01-15 specifies {new_bps}bps, but billing "
    f"still uses old rate of {old_tier_bps}bps. Two quarters of overcharges.",
    err2_impact
))


# --- ERROR 3: Completely unbilled account — Nakamura Family ---
# One sub-account just… missing from the billing run entirely.
err3_hh = households[2]
err3_hh["household_name"] = "Nakamura Family"
agreements[2]["household_name"] = "Nakamura Family"
# Remove billing entry for the first account
unbilled_acct = err3_hh["accounts"][0]
billing_entries = [
    e for e in billing_entries
    if not (e["household_id"] == err3_hh["household_id"] and e["account_id"] == unbilled_acct["account_id"])
]
unbilled_aum = unbilled_acct["current_aum"]
correct_bps = err3_hh["tier_qualified"]["bps"]
err3_impact = round(unbilled_aum * correct_bps / 10_000, 2)
seeded_errors.append(error_manifest(
    "ERR-3", "Nakamura Family", "unbilled_account",
    f"Account '{unbilled_acct['account_label']}' ({unbilled_acct['account_type']}) "
    f"with ${unbilled_aum:,.2f} AUM has no billing entry for Q3 2025. "
    f"Missed revenue: ${err3_impact:,.2f}/yr at {correct_bps}bps.",
    err3_impact
))


# --- ERROR 4: Expired waiver still being applied — Patel Family ---
# Fee waiver expired Dec 2024 but billing still deducts 15bps.
err4_hh = households[3]
err4_hh["household_name"] = "Patel Family"
agreements[3]["household_name"] = "Patel Family"
agreements[3]["fee_waivers"] = [{
    "waiver_id": uid(),
    "account_id": None,
    "waiver_bps": 15,
    "reason": "Promotional rate — first 2 years",
    "expiry": "2024-12-31",  # EXPIRED
}]
correct_bps_4 = err4_hh["tier_qualified"]["bps"]
waived_bps = correct_bps_4 - 15  # what they're being charged (too low)
for entry in billing_entries:
    if entry["household_id"] == err4_hh["household_id"]:
        entry["bps_charged"] = waived_bps
        entry["fee_dollar_amount"] = quarterly_fee(entry["aum_billed"], waived_bps)
        entry["_injected_error"] = "ERR-4"

err4_impact = round(15 / 10_000 * err4_hh["total_aum"], 2)
seeded_errors.append(error_manifest(
    "ERR-4", "Patel Family", "expired_waiver_still_applied",
    f"15bps promotional waiver expired 2024-12-31 but billing still charges "
    f"{waived_bps}bps instead of {correct_bps_4}bps. Undercharge across "
    f"${err4_hh['total_aum']:,.2f} AUM.",
    err4_impact
))


# --- ERROR 5: 529 account incorrectly included in household AUM ---
# Fernandez household has a 529 that's being counted toward breakpoint
# aggregation, which inflates their AUM and gives them a lower tier than
# they actually qualify for.
err5_hh = households[6]
err5_hh["household_name"] = "Fernandez Family"
agreements[6]["household_name"] = "Fernandez Family"
# Add a 529 account that's being incorrectly included
err5_529 = {
    "account_id": uid(),
    "account_label": "Fernandez 529 College Savings",
    "account_type": "529",
    "current_aum": 180_000.00,
    "is_active": True,
    "include_in_household_aum": True,  # ERROR — should be False per agreement
    "opened_date": "2022-03-15",
    "closed_date": None,
}
err5_hh["accounts"].append(err5_529)
# The 529's inclusion pushes total_aum over a breakpoint
old_total = err5_hh["total_aum"]
err5_hh["total_aum"] = round(old_total + 180_000, 2)
# Recalculate tier (now lower bps because of inflated AUM)
wrong_tier = find_tier(agreements[6]["fee_tiers"], err5_hh["total_aum"])
correct_tier_5 = find_tier(agreements[6]["fee_tiers"], old_total)
err5_hh["tier_qualified"] = {"tier_label": wrong_tier["tier_label"], "bps": wrong_tier["bps"]}
# All accounts billed at wrong (lower) rate
for entry in billing_entries:
    if entry["household_id"] == err5_hh["household_id"]:
        entry["bps_charged"] = wrong_tier["bps"]
        entry["fee_dollar_amount"] = quarterly_fee(entry["aum_billed"], wrong_tier["bps"])
        entry["_injected_error"] = "ERR-5"
# Add billing entry for the 529 too
billing_entries.append({
    "entry_id": uid(),
    "account_id": err5_529["account_id"],
    "household_id": err5_hh["household_id"],
    "practice_id": PRACTICE_ID,
    "advisor_id": err5_hh["advisor_id"],
    "billing_period": BILLING_PERIOD,
    "billing_date": BILLING_DATE,
    "aum_billed": 180_000.00,
    "bps_charged": wrong_tier["bps"],
    "fee_dollar_amount": quarterly_fee(180_000, wrong_tier["bps"]),
    "billing_method": "in-arrears",
    "fee_type": "advisory",
    "status": "posted",
    "source_system": "ClientWorks",
    "reconciliation": None,
    "_injected_error": "ERR-5",
})

if wrong_tier["bps"] != correct_tier_5["bps"]:
    err5_impact = round((correct_tier_5["bps"] - wrong_tier["bps"]) / 10_000 * old_total, 2)
else:
    err5_impact = round(wrong_tier["bps"] / 10_000 * 180_000, 2)  # just the 529 being billed at all
seeded_errors.append(error_manifest(
    "ERR-5", "Fernandez Family", "529_included_in_breakpoint",
    f"529 account ($180K) incorrectly included in household AUM aggregation. "
    f"Inflates total to ${err5_hh['total_aum']:,.2f}, potentially qualifying for "
    f"a lower tier than the actual ${old_total:,.2f} warrants.",
    err5_impact
))


# --- ERROR 6: Duplicate billing — Kim Family ---
# One account has two billing entries for the same quarter.
err6_hh = households[4]
err6_hh["household_name"] = "Kim Family"
agreements[4]["household_name"] = "Kim Family"
# Find an existing entry and duplicate it
err6_original = None
for entry in billing_entries:
    if entry["household_id"] == err6_hh["household_id"]:
        err6_original = entry
        break

if err6_original:
    err6_duplicate = dict(err6_original)
    err6_duplicate["entry_id"] = uid()
    err6_duplicate["billing_date"] = "2025-07-15"  # billed again 2 weeks later
    err6_duplicate["_injected_error"] = "ERR-6"
    billing_entries.append(err6_duplicate)
    err6_impact = err6_original["fee_dollar_amount"] * 4  # annualized
    seeded_errors.append(error_manifest(
        "ERR-6", "Kim Family", "duplicate_billing",
        f"Account '{err6_hh['accounts'][0]['account_label']}' billed twice in Q3 2025 "
        f"(Jul 1 and Jul 15). Duplicate fee: ${err6_original['fee_dollar_amount']:,.2f} "
        f"per quarter.",
        round(err6_impact, 2)
    ))


# --- ERROR 7: Closed account still being billed — Morrison Family ---
err7_hh = households[10]
err7_hh["household_name"] = "Morrison Family"
agreements[10]["household_name"] = "Morrison Family"
# Mark first account as closed
err7_acct = err7_hh["accounts"][0]
err7_acct["is_active"] = False
err7_acct["closed_date"] = "2025-03-31"
err7_acct["account_label"] = "Morrison Old Trust"
err7_acct["account_type"] = "trust"
err7_acct["current_aum"] = 0.00  # closed, zeroed out
# But billing entry still exists with old AUM
ghost_aum = 420_000.00
for entry in billing_entries:
    if entry["account_id"] == err7_acct["account_id"]:
        entry["aum_billed"] = ghost_aum
        entry["bps_charged"] = err7_hh["tier_qualified"]["bps"]
        entry["fee_dollar_amount"] = quarterly_fee(ghost_aum, err7_hh["tier_qualified"]["bps"])
        entry["_injected_error"] = "ERR-7"

err7_impact = round(ghost_aum * err7_hh["tier_qualified"]["bps"] / 10_000, 2)
seeded_errors.append(error_manifest(
    "ERR-7", "Morrison Family", "closed_account_still_billed",
    f"Trust account closed 2025-03-31 with $0 AUM, but Q3 2025 billing "
    f"charged against stale ${ghost_aum:,.2f} valuation. Ghost fee: "
    f"${quarterly_fee(ghost_aum, err7_hh['tier_qualified']['bps']):,.2f}/quarter.",
    err7_impact
))


# --- ERROR 8: Partial household — two accounts not linked ---
# Thornton household has 3 accounts but only 1 is linked to the household
# in billing. The other 2 are billed as standalone at higher individual rates.
err8_hh = households[12]
err8_hh["household_name"] = "Thornton Family"
agreements[12]["household_name"] = "Thornton Family"
# Ensure at least 3 accounts
while len(err8_hh["accounts"]) < 3:
    err8_hh["accounts"].append({
        "account_id": uid(),
        "account_label": f"Thornton Account {len(err8_hh['accounts']) + 1}",
        "account_type": random.choice(["IRA", "individual"]),
        "current_aum": pick_aum(),
        "is_active": True,
        "include_in_household_aum": True,
        "opened_date": "2021-06-01",
        "closed_date": None,
    })

# Recalculate total AUM
err8_total = sum(a["current_aum"] for a in err8_hh["accounts"] if a["include_in_household_aum"])
err8_hh["total_aum"] = round(err8_total, 2)
correct_tier_8 = find_tier(agreements[12]["fee_tiers"], err8_total)
err8_hh["tier_qualified"] = {"tier_label": correct_tier_8["tier_label"], "bps": correct_tier_8["bps"]}

# The unlinked accounts get billed at standalone (higher) tier based only on their own AUM
orphan_impact = 0.0
for acct in err8_hh["accounts"][1:]:  # accounts[1:] are "orphaned" from household
    standalone_tier = find_tier(agreements[12]["fee_tiers"], acct["current_aum"])
    # Update or create billing entry
    found = False
    for entry in billing_entries:
        if entry["account_id"] == acct["account_id"]:
            entry["bps_charged"] = standalone_tier["bps"]
            entry["fee_dollar_amount"] = quarterly_fee(acct["current_aum"], standalone_tier["bps"])
            entry["household_id"] = None  # NOT linked to household in billing
            entry["_injected_error"] = "ERR-8"
            found = True
            break
    if not found:
        billing_entries.append({
            "entry_id": uid(),
            "account_id": acct["account_id"],
            "household_id": None,  # NOT linked
            "practice_id": PRACTICE_ID,
            "advisor_id": err8_hh["advisor_id"],
            "billing_period": BILLING_PERIOD,
            "billing_date": BILLING_DATE,
            "aum_billed": acct["current_aum"],
            "bps_charged": standalone_tier["bps"],
            "fee_dollar_amount": quarterly_fee(acct["current_aum"], standalone_tier["bps"]),
            "billing_method": "in-arrears",
            "fee_type": "advisory",
            "status": "posted",
            "source_system": "ClientWorks",
            "reconciliation": None,
            "_injected_error": "ERR-8",
        })
    bps_diff = standalone_tier["bps"] - correct_tier_8["bps"]
    if bps_diff > 0:
        orphan_impact += bps_diff / 10_000 * acct["current_aum"]

seeded_errors.append(error_manifest(
    "ERR-8", "Thornton Family", "unlinked_household_accounts",
    f"2 of 3 accounts not linked to household in billing system. "
    f"Billed at standalone rates instead of household-aggregated tier "
    f"({correct_tier_8['bps']}bps on ${err8_total:,.2f}). "
    f"Overcharge from rate differential.",
    round(orphan_impact, 2)
))


# ---------------------------------------------------------------------------
# Compute summary stats
# ---------------------------------------------------------------------------
total_leakage = sum(e["annual_dollar_impact"] for e in seeded_errors)
total_entries = len(billing_entries)
total_accounts = sum(len(h["accounts"]) for h in households)

summary = {
    "generated_at": datetime.now().isoformat(),
    "seed": 42,
    "num_households": len(households),
    "num_accounts": total_accounts,
    "num_billing_entries": total_entries,
    "num_seeded_errors": len(seeded_errors),
    "total_annual_leakage": round(total_leakage, 2),
    "errors": seeded_errors,
}


# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_json(filename, data):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  [OK] {path}  ({len(data) if isinstance(data, list) else 'object'})")


print(f"\n{'='*60}")
print(f"  FeeAudit Synthetic Data Generator")
print(f"{'='*60}")
print(f"  Households:        {len(households)}")
print(f"  Total accounts:    {total_accounts}")
print(f"  Billing entries:   {total_entries}")
print(f"  Seeded errors:     {len(seeded_errors)}")
print(f"  Total leakage:     ${total_leakage:,.2f}/year")
print(f"{'='*60}\n")
print("Writing files:")

write_json("advisory_agreements.json", agreements)
write_json("household_mappings.json", households)
write_json("billing_logs.json", billing_entries)
write_json("seeded_errors_manifest.json", summary)

print(f"\n  Seeded errors:")
for e in seeded_errors:
    print(f"    [{e['error_id']}] {e['household']} — {e['error_type']}")
    print(f"           ${e['annual_dollar_impact']:,.2f}/yr — {e['description'][:80]}...")

print(f"\n  Done. Total annual revenue at risk: ${total_leakage:,.2f}")
print()
