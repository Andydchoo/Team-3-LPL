"""
reconciliation_engine.py
========================
Core reconciliation logic for FeeAudit.

Runs as a standalone script against the JSON data in ../data/.
No API, no frontend — just the math.

For each household:
  1. Sum aggregate AUM across eligible sub-accounts
  2. Look up the correct fee tier from the advisory agreement
  3. Apply any active (non-expired) waivers
  4. Calculate expected quarterly fee per account
  5. Compare expected vs. actual billing
  6. Flag discrepancies

Also performs structural checks:
  - Unbilled accounts (account exists, no billing entry)
  - Duplicate billing (same account billed twice in one period)
  - Closed accounts still being billed
  - Unlinked accounts (billing entry with no household linkage)
  - 529 accounts incorrectly included in household AUM

Outputs:
  - reconciliation_results.json  (full detailed results)
  - Console summary with all flagged issues

Validates against seeded_errors_manifest.json to confirm full coverage.
"""

import json
import sys
from datetime import date
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = DATA_DIR


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
agreements = load_json("advisory_agreements.json")
households = load_json("household_mappings.json")
billing_logs = load_json("billing_logs.json")
manifest = load_json("seeded_errors_manifest.json")

# Build indexes
agreement_by_id = {a["agreement_id"]: a for a in agreements}
household_by_id = {h["household_id"]: h for h in households}

# Build account -> household reverse index from household_mappings
account_to_household = {}
for hh in households:
    for acct in hh["accounts"]:
        account_to_household[acct["account_id"]] = hh["household_id"]

# Group billing entries by household
billing_by_household = defaultdict(list)
orphan_billing = []  # entries with no household_id
for entry in billing_logs:
    hh_id = entry.get("household_id")
    if hh_id:
        billing_by_household[hh_id].append(entry)
    else:
        orphan_billing.append(entry)


# ---------------------------------------------------------------------------
# Tier lookup
# ---------------------------------------------------------------------------
def find_correct_tier(fee_tiers, total_aum):
    """Given an ordered fee tier schedule and aggregate AUM, return the matching tier."""
    for tier in fee_tiers:
        aum_max = tier["aum_max"]
        if total_aum >= tier["aum_min"] and (aum_max is None or total_aum < aum_max):
            return tier
    # Fallback to the last (highest) tier
    return fee_tiers[-1]


def quarterly_fee(aum, bps):
    """Compute one quarter's dollar fee from AUM and annual bps."""
    return round((aum * bps / 10_000) / 4, 2)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------
BILLING_DATE = date(2025, 7, 1)  # Q3 2025 billing date
TOLERANCE_BPS = 0  # flag any deviation at all

results = {
    "summary": {},
    "household_results": [],
    "discrepancies": [],
    "structural_issues": [],
    "validation": {},
}


# ---- Phase 1: Structural checks ----

# 1a. Duplicate billing detection
billing_by_account_period = defaultdict(list)
for entry in billing_logs:
    key = (entry["account_id"], json.dumps(entry["billing_period"], sort_keys=True))
    billing_by_account_period[key].append(entry)

for key, entries in billing_by_account_period.items():
    if len(entries) > 1:
        account_id = entries[0]["account_id"]
        hh_id = entries[0].get("household_id")
        hh = household_by_id.get(hh_id) if hh_id else None
        hh_name = hh["household_name"] if hh else "Unknown"

        # Find account label
        acct_label = account_id[:8]
        if hh:
            for a in hh["accounts"]:
                if a["account_id"] == account_id:
                    acct_label = a["account_label"]
                    break

        total_billed = sum(e["fee_dollar_amount"] for e in entries)
        single_fee = entries[0]["fee_dollar_amount"]

        results["structural_issues"].append({
            "issue_type": "duplicate_billing",
            "household": hh_name,
            "household_id": hh_id,
            "account_id": account_id,
            "account_label": acct_label,
            "detail": (
                f"Account billed {len(entries)} times in same period. "
                f"Each charge: ${single_fee:,.2f}. "
                f"Excess: ${total_billed - single_fee:,.2f}/quarter, "
                f"${(total_billed - single_fee) * 4:,.2f}/year."
            ),
            "annual_impact": round((total_billed - single_fee) * 4, 2),
        })


# 1b. Unlinked billing entries (orphan entries with no household_id)
for entry in orphan_billing:
    account_id = entry["account_id"]
    # Try to find this account in a household
    matched_hh_id = account_to_household.get(account_id)
    matched_hh = household_by_id.get(matched_hh_id) if matched_hh_id else None
    hh_name = matched_hh["household_name"] if matched_hh else "Unknown"

    acct_label = account_id[:8]
    if matched_hh:
        for a in matched_hh["accounts"]:
            if a["account_id"] == account_id:
                acct_label = a["account_label"]
                break

    results["structural_issues"].append({
        "issue_type": "unlinked_account",
        "household": hh_name,
        "household_id": matched_hh_id,
        "account_id": account_id,
        "account_label": acct_label,
        "detail": (
            f"Billing entry exists but household_id is null. "
            f"Account belongs to '{hh_name}' per household mapping. "
            f"Billed at {entry['bps_charged']}bps standalone instead of household rate."
        ),
        "bps_charged": entry["bps_charged"],
        "aum_billed": entry["aum_billed"],
        "fee_charged": entry["fee_dollar_amount"],
    })


# ---- Phase 2: Per-household reconciliation ----

for hh in households:
    hh_id = hh["household_id"]
    hh_name = hh["household_name"]
    agreement = agreement_by_id.get(hh["agreement_id"])

    if not agreement:
        results["structural_issues"].append({
            "issue_type": "missing_agreement",
            "household": hh_name,
            "household_id": hh_id,
            "detail": "No advisory agreement found for this household.",
        })
        continue

    fee_tiers = agreement["fee_tiers"]
    waivers = agreement.get("fee_waivers", [])

    # --- 2a. Check for 529 accounts incorrectly included in household AUM ---
    policy_issues = []
    for acct in hh["accounts"]:
        if acct["account_type"] == "529" and acct["include_in_household_aum"]:
            policy_issues.append({
                "issue_type": "529_included_in_breakpoint",
                "household": hh_name,
                "household_id": hh_id,
                "account_id": acct["account_id"],
                "account_label": acct["account_label"],
                "detail": (
                    f"529 account '{acct['account_label']}' with "
                    f"${acct['current_aum']:,.2f} is flagged include_in_household_aum=True. "
                    f"Per standard policy, 529 accounts should be excluded from "
                    f"breakpoint aggregation."
                ),
                "aum_impact": acct["current_aum"],
            })

    results["structural_issues"].extend(policy_issues)

    # --- 2b. Calculate CORRECT household aggregate AUM ---
    #     Use include_in_household_aum flag as-is (the engine reports the 529
    #     issue separately; tier calculation here reflects what SHOULD happen
    #     if the 529 were properly excluded).
    correct_aum = sum(
        a["current_aum"]
        for a in hh["accounts"]
        if a["include_in_household_aum"]
        and a["is_active"]
        and a["account_type"] != "529"  # Engine enforces 529 exclusion
    )

    correct_tier = find_correct_tier(fee_tiers, correct_aum)
    expected_bps = correct_tier["bps"]

    # --- 2c. Apply active waivers (skip expired ones) ---
    active_waivers = []
    expired_waivers_in_use = []
    for w in waivers:
        expiry = w.get("expiry")
        if expiry:
            expiry_date = date.fromisoformat(expiry)
            if expiry_date < BILLING_DATE:
                # Waiver is expired — do NOT apply, but track it
                expired_waivers_in_use.append(w)
                continue
        active_waivers.append(w)

    # Household-level waiver adjustment (account_id is null = applies to all)
    hh_waiver_bps = sum(
        w["waiver_bps"] for w in active_waivers
        if w.get("account_id") is None
    )
    expected_bps_after_waiver = expected_bps - hh_waiver_bps

    # --- 2d. Check for closed accounts still being billed ---
    closed_accounts = {
        a["account_id"]: a for a in hh["accounts"] if not a["is_active"]
    }

    # --- 2e. Check for unbilled accounts ---
    entries_for_hh = billing_by_household.get(hh_id, [])
    billed_account_ids = {e["account_id"] for e in entries_for_hh}

    # Also check orphan entries that belong to this household
    orphan_for_hh = [
        e for e in orphan_billing
        if account_to_household.get(e["account_id"]) == hh_id
    ]

    for acct in hh["accounts"]:
        if not acct["is_active"]:
            # Closed account — check if it's INCORRECTLY being billed
            if acct["account_id"] in billed_account_ids:
                matching_entry = next(
                    e for e in entries_for_hh
                    if e["account_id"] == acct["account_id"]
                )
                results["structural_issues"].append({
                    "issue_type": "closed_account_billed",
                    "household": hh_name,
                    "household_id": hh_id,
                    "account_id": acct["account_id"],
                    "account_label": acct["account_label"],
                    "detail": (
                        f"Account closed {acct['closed_date']} (AUM: $0) but "
                        f"billed ${matching_entry['fee_dollar_amount']:,.2f} on "
                        f"${matching_entry['aum_billed']:,.2f} stale AUM at "
                        f"{matching_entry['bps_charged']}bps."
                    ),
                    "annual_impact": round(matching_entry["fee_dollar_amount"] * 4, 2),
                })
            continue  # Don't flag closed accounts as "unbilled"

        # Active account — check if it has a billing entry
        also_orphan = any(
            e["account_id"] == acct["account_id"] for e in orphan_for_hh
        )
        if acct["account_id"] not in billed_account_ids and not also_orphan:
            # Account is UNBILLED
            expected_fee_annual = round(acct["current_aum"] * expected_bps_after_waiver / 10_000, 2)
            results["structural_issues"].append({
                "issue_type": "unbilled_account",
                "household": hh_name,
                "household_id": hh_id,
                "account_id": acct["account_id"],
                "account_label": acct["account_label"],
                "detail": (
                    f"Active account '{acct['account_label']}' "
                    f"({acct['account_type']}) with ${acct['current_aum']:,.2f} AUM "
                    f"has no billing entry for the period. "
                    f"Missing revenue: ${expected_fee_annual:,.2f}/year at "
                    f"{expected_bps_after_waiver}bps."
                ),
                "annual_impact": expected_fee_annual,
            })

    # --- 2f. Rate reconciliation per billing entry ---
    hh_expected_revenue_q = 0.0
    hh_actual_revenue_q = 0.0
    account_discrepancies = []

    for entry in entries_for_hh:
        acct_id = entry["account_id"]

        # Skip closed accounts (already flagged in structural issues)
        if acct_id in closed_accounts:
            hh_actual_revenue_q += entry["fee_dollar_amount"]
            continue

        # Per-account waiver adjustment
        acct_waiver_bps = sum(
            w["waiver_bps"] for w in active_waivers
            if w.get("account_id") == acct_id
        )
        entry_expected_bps = expected_bps_after_waiver - acct_waiver_bps

        entry_expected_fee = quarterly_fee(entry["aum_billed"], entry_expected_bps)
        variance_bps = entry["bps_charged"] - entry_expected_bps
        variance_dollar_q = entry["fee_dollar_amount"] - entry_expected_fee
        variance_dollar_annual = round(variance_dollar_q * 4, 2)

        hh_expected_revenue_q += entry_expected_fee
        hh_actual_revenue_q += entry["fee_dollar_amount"]

        # Find account label
        acct_label = acct_id[:8]
        for a in hh["accounts"]:
            if a["account_id"] == acct_id:
                acct_label = a["account_label"]
                break

        if abs(variance_bps) > TOLERANCE_BPS:
            # Determine discrepancy type
            if variance_bps > 0:
                disc_type = "overcharge"
            else:
                disc_type = "undercharge"

            # Check for expired waiver as root cause
            root_cause = "rate_mismatch"
            if expired_waivers_in_use:
                # If the charged rate equals what you'd get WITH the expired waiver
                for ew in expired_waivers_in_use:
                    if ew.get("account_id") is None or ew.get("account_id") == acct_id:
                        expected_with_expired = entry_expected_bps - ew["waiver_bps"]
                        if entry["bps_charged"] == expected_with_expired:
                            root_cause = "expired_waiver_still_applied"
                            break

            discrepancy = {
                "household": hh_name,
                "household_id": hh_id,
                "account_id": acct_id,
                "account_label": acct_label,
                "discrepancy_type": disc_type,
                "root_cause": root_cause,
                "expected_bps": entry_expected_bps,
                "actual_bps": entry["bps_charged"],
                "variance_bps": variance_bps,
                "aum_billed": entry["aum_billed"],
                "expected_fee_quarterly": entry_expected_fee,
                "actual_fee_quarterly": entry["fee_dollar_amount"],
                "variance_quarterly": round(variance_dollar_q, 2),
                "variance_annual": variance_dollar_annual,
            }
            account_discrepancies.append(discrepancy)
            results["discrepancies"].append(discrepancy)

    # Also reconcile orphan entries that belong to this household
    for entry in orphan_for_hh:
        acct_id = entry["account_id"]
        acct_label = acct_id[:8]
        for a in hh["accounts"]:
            if a["account_id"] == acct_id:
                acct_label = a["account_label"]
                break

        # These accounts are billed at standalone rate instead of household rate
        entry_expected_bps = expected_bps_after_waiver
        entry_expected_fee = quarterly_fee(entry["aum_billed"], entry_expected_bps)
        variance_bps = entry["bps_charged"] - entry_expected_bps
        variance_dollar_q = entry["fee_dollar_amount"] - entry_expected_fee
        variance_dollar_annual = round(variance_dollar_q * 4, 2)

        hh_expected_revenue_q += entry_expected_fee
        hh_actual_revenue_q += entry["fee_dollar_amount"]

        if abs(variance_bps) > TOLERANCE_BPS:
            discrepancy = {
                "household": hh_name,
                "household_id": hh_id,
                "account_id": acct_id,
                "account_label": acct_label,
                "discrepancy_type": "overcharge" if variance_bps > 0 else "undercharge",
                "root_cause": "unlinked_from_household",
                "expected_bps": entry_expected_bps,
                "actual_bps": entry["bps_charged"],
                "variance_bps": variance_bps,
                "aum_billed": entry["aum_billed"],
                "expected_fee_quarterly": entry_expected_fee,
                "actual_fee_quarterly": entry["fee_dollar_amount"],
                "variance_quarterly": round(variance_dollar_q, 2),
                "variance_annual": variance_dollar_annual,
            }
            account_discrepancies.append(discrepancy)
            results["discrepancies"].append(discrepancy)

    # Household-level summary
    hh_result = {
        "household_name": hh_name,
        "household_id": hh_id,
        "total_aum": round(correct_aum, 2),
        "correct_tier": correct_tier["tier_label"],
        "correct_bps": expected_bps,
        "effective_bps_after_waivers": expected_bps_after_waiver,
        "num_accounts": len(hh["accounts"]),
        "num_active_accounts": sum(1 for a in hh["accounts"] if a["is_active"]),
        "expected_quarterly_revenue": round(hh_expected_revenue_q, 2),
        "actual_quarterly_revenue": round(hh_actual_revenue_q, 2),
        "quarterly_variance": round(hh_actual_revenue_q - hh_expected_revenue_q, 2),
        "annual_variance": round((hh_actual_revenue_q - hh_expected_revenue_q) * 4, 2),
        "has_discrepancies": len(account_discrepancies) > 0,
        "discrepancy_count": len(account_discrepancies),
        "account_discrepancies": account_discrepancies,
    }
    results["household_results"].append(hh_result)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
flagged_households = [h for h in results["household_results"] if h["has_discrepancies"]]
total_annual_variance = sum(
    abs(d["variance_annual"]) for d in results["discrepancies"]
)
structural_impact = sum(
    i.get("annual_impact", 0) for i in results["structural_issues"]
)

results["summary"] = {
    "total_households": len(households),
    "flagged_households": len(flagged_households),
    "clean_households": len(households) - len(flagged_households),
    "total_rate_discrepancies": len(results["discrepancies"]),
    "total_structural_issues": len(results["structural_issues"]),
    "total_annual_revenue_at_risk": round(total_annual_variance + structural_impact, 2),
    "rate_discrepancy_annual_impact": round(total_annual_variance, 2),
    "structural_issue_annual_impact": round(structural_impact, 2),
    "issue_breakdown": {},
}

# Count by type
for issue in results["structural_issues"]:
    itype = issue["issue_type"]
    results["summary"]["issue_breakdown"][itype] = (
        results["summary"]["issue_breakdown"].get(itype, 0) + 1
    )
for disc in results["discrepancies"]:
    cause = disc["root_cause"]
    key = f"rate_{cause}"
    results["summary"]["issue_breakdown"][key] = (
        results["summary"]["issue_breakdown"].get(key, 0) + 1
    )


# ---------------------------------------------------------------------------
# Validate against seeded errors
# ---------------------------------------------------------------------------
expected_errors = {e["error_id"]: e for e in manifest["errors"]}
detected = {}

# ERR-1: breakpoint_not_applied (Stevens)
for d in results["discrepancies"]:
    if d["household"] == "Stevens Family" and d["actual_bps"] > d["expected_bps"]:
        detected["ERR-1"] = f"FOUND: {d['household']} overcharged {d['variance_bps']}bps"
        break

# ERR-2: stale_fee_schedule (Whitaker)
for d in results["discrepancies"]:
    if d["household"] == "Whitaker Family" and d["actual_bps"] > d["expected_bps"]:
        detected["ERR-2"] = f"FOUND: {d['household']} overcharged {d['variance_bps']}bps (stale schedule)"
        break

# ERR-3: unbilled_account (Nakamura)
for i in results["structural_issues"]:
    if i.get("household") == "Nakamura Family" and i["issue_type"] == "unbilled_account":
        detected["ERR-3"] = f"FOUND: {i['account_label']} unbilled"
        break

# ERR-4: expired_waiver (Patel)
for d in results["discrepancies"]:
    if d["household"] == "Patel Family" and d["root_cause"] == "expired_waiver_still_applied":
        detected["ERR-4"] = f"FOUND: {d['household']} expired waiver, undercharged {d['variance_bps']}bps"
        break

# ERR-5: 529 in breakpoint (Fernandez)
for i in results["structural_issues"]:
    if i.get("household") == "Fernandez Family" and i["issue_type"] == "529_included_in_breakpoint":
        detected["ERR-5"] = f"FOUND: {i['account_label']} 529 in breakpoint aggregation"
        break

# ERR-6: duplicate billing (Kim)
for i in results["structural_issues"]:
    if i.get("household") == "Kim Family" and i["issue_type"] == "duplicate_billing":
        detected["ERR-6"] = f"FOUND: {i['account_label']} billed twice"
        break

# ERR-7: closed account billed (Morrison)
for i in results["structural_issues"]:
    if i.get("household") == "Morrison Family" and i["issue_type"] == "closed_account_billed":
        detected["ERR-7"] = f"FOUND: {i['account_label']} closed but billed"
        break

# ERR-8: unlinked accounts (Thornton)
for i in results["structural_issues"]:
    if i.get("household") == "Thornton Family" and i["issue_type"] == "unlinked_account":
        detected["ERR-8"] = f"FOUND: unlinked account in Thornton household"
        break

results["validation"] = {
    "seeded_errors": len(expected_errors),
    "detected": len(detected),
    "all_caught": len(detected) == len(expected_errors),
    "details": {},
}

for err_id in sorted(expected_errors.keys()):
    results["validation"]["details"][err_id] = {
        "expected": expected_errors[err_id]["error_type"],
        "household": expected_errors[err_id]["household"],
        "status": "CAUGHT" if err_id in detected else "MISSED",
        "detection_detail": detected.get(err_id, "NOT DETECTED"),
    }


# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
output_path = OUTPUT_DIR / "reconciliation_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------
SEP = "=" * 64

print(f"\n{SEP}")
print("  FeeAudit Reconciliation Engine")
print(SEP)
print(f"  Households analyzed:      {results['summary']['total_households']}")
print(f"  Flagged households:       {results['summary']['flagged_households']}")
print(f"  Clean households:         {results['summary']['clean_households']}")
print(f"  Rate discrepancies:       {results['summary']['total_rate_discrepancies']}")
print(f"  Structural issues:        {results['summary']['total_structural_issues']}")
print(f"  Total revenue at risk:    ${results['summary']['total_annual_revenue_at_risk']:,.2f}/year")
print(SEP)

print("\n  RATE DISCREPANCIES:")
if results["discrepancies"]:
    for d in results["discrepancies"]:
        direction = "OVER" if d["variance_bps"] > 0 else "UNDER"
        print(
            f"    {d['household']:25s} | {d['account_label']:30s} | "
            f"{direction} {abs(d['variance_bps']):3d}bps | "
            f"${abs(d['variance_annual']):>10,.2f}/yr | "
            f"{d['root_cause']}"
        )
else:
    print("    (none)")

print("\n  STRUCTURAL ISSUES:")
if results["structural_issues"]:
    for i in results["structural_issues"]:
        impact = i.get("annual_impact", i.get("aum_impact", 0))
        impact_str = f"${impact:>10,.2f}" if impact else "    --    "
        print(
            f"    {i.get('household', 'N/A'):25s} | {i['issue_type']:30s} | "
            f"{impact_str}/yr"
        )
        print(f"      {i['detail'][:100]}")
else:
    print("    (none)")

print(f"\n{SEP}")
print("  SEEDED ERROR VALIDATION")
print(SEP)
all_pass = True
for err_id, detail in sorted(results["validation"]["details"].items()):
    status = detail["status"]
    marker = "[PASS]" if status == "CAUGHT" else "[FAIL]"
    if status != "CAUGHT":
        all_pass = False
    print(
        f"    {marker} {err_id} | {detail['household']:25s} | "
        f"{detail['expected']:30s} | {detail['detection_detail']}"
    )

print(f"\n  Result: {'ALL 8 SEEDED ERRORS CAUGHT' if all_pass else 'SOME ERRORS MISSED -- FIX ENGINE LOGIC'}")
print(f"  Output: {output_path}")
print()

if not all_pass:
    sys.exit(1)
