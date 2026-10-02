# Team-3-LPL

# RevenueTwin 💰

> **See the revenue you're missing before you miss it.**

RevenueTwin is an AI-powered **revenue intelligence platform for wealth management firms**.

It creates a digital twin of an advisory practice's revenue to answer three questions:

1. **What should we be earning?**
2. **What are we actually earning?**
3. **Why is there a difference?**

## 🔎 FeeAudit

**FeeAudit** is RevenueTwin's core product.

It reads client advisory agreements, calculates what clients should be billed, compares that against actual billing data, and detects:

- 💸 Potential underbilling
- ⚠️ Potential overbilling
- 📉 Incorrect fee breakpoints
- 👨‍👩‍👧 Householding errors
- 🧾 Unbilled accounts
- 🎟️ Fee waiver errors

### Example

```text
Stevens Family

Household AUM:       $2.2M
Contract Rate:       0.75%
Actual Rate:         0.90%

🚨 Potential Discrepancy: $3,300/year

Cause:
The household crossed the $2M fee breakpoint,
but billing remained at 0.90%.
```

## ⚙️ How It Works

```text
Fee Agreements + Account Data + Billing Data
                     ↓
                RevenueTwin
                     ↓
              AI reads rules
                     ↓
          Calculate expected fees
                     ↓
          Compare with actual fees
                     ↓
             Detect differences
                     ↓
              Explain why
                     ↓
               Human review
```

## ☁️ AWS

RevenueTwin uses:

- **Amazon S3** — store agreements and billing files
- **Amazon Textract** — extract fee schedules from PDFs
- **Amazon Bedrock** — understand agreements and explain findings
- **AWS Lambda** — calculate expected fees
- **AWS Step Functions** — orchestrate the audit
- **Amazon DynamoDB** — store findings and audit history

## 🧠 Core Principle

> **AI interprets. Code calculates. Humans approve.**

AI understands the contracts, deterministic code handles the financial math, and humans review consequential findings.

## 🚀 Hackathon MVP

Upload:

```text
Advisory Agreements
Accounts.csv
Billing.csv
```

Click:

**RUN REVENUE AUDIT**

Receive:

```text
50 Accounts Analyzed
48 Verified
2 Require Review

$17,500
BILLING DISCREPANCIES IDENTIFIED
```

## 🔮 Vision

FeeAudit is the first product.

The long-term goal is for **RevenueTwin to become the revenue operating system for wealth management**, moving firms from reactive billing audits to proactive revenue intelligence.

---

### RevenueTwin

**Know what you should earn. Know what you earned. Know why they're different.**
