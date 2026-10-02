# Team-3-LPL

# 💰 FeeAudit AI

> **Every dollar. Every account. Every fee. Verified.**

FeeAudit is an AI-powered fee auditing platform for wealth management firms that automatically reads financial advisory agreements, determines what each client **should have been charged**, compares it against what they were **actually billed**, and flags potential overcharges, undercharges, missing fees, incorrect breakpoints, and other billing discrepancies.

---

## 🎯 The Problem

Wealth management firms may manage thousands of client accounts with different:

- Fee schedules
- AUM breakpoints
- Household discounts
- Special negotiated rates
- Fee waivers
- Billing frequencies
- Account exclusions
- Grandfathered agreements

These rules are often stored inside PDFs and manually configured in billing systems.

That creates a simple but expensive problem:

> **What the contract says and what the billing system does can become different.**

### Example

A client's agreement states:

| Assets | Advisory Fee |
|---|---:|
| $0 – $1M | 1.00% |
| $1M – $2M | 0.90% |
| $2M+ | 0.75% |

The client's household now contains:

**$2.2M AUM**

Therefore, the applicable contractual rate is:

**0.75%**

But the billing system still contains:

**0.90%**

FeeAudit detects the discrepancy automatically.

```text
🚨 POTENTIAL BILLING DISCREPANCY

Household: Stevens Family

Household AUM:       $2,200,000
Contract Rate:             0.75%
Billing Rate:              0.90%

Potential annual impact: $3,300

Likely Cause:
Household crossed the $2M contractual breakpoint,
but the billing configuration was not updated.

Status:
REQUIRES HUMAN REVIEW

