# Data Model: FeeAudit / RevenueTwin

Three canonical schemas that drive the reconciliation engine, UI, and AI pipeline.
All IDs are UUIDs. All bps values are integers (basis points). All dollar amounts are floats rounded to 2 decimal places.

---

## Schema 1 — Client Advisory Agreement (`advisory_agreement`)

Represents the signed fee contract between the practice and a household.
Parsed from PDF via OCR + LLM into this structured form.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "advisory_agreement",
  "type": "object",
  "required": ["agreement_id", "household_id", "household_name", "effective_date", "fee_tiers", "billing_frequency", "agreement_type"],
  "properties": {
    "agreement_id":       { "type": "string", "format": "uuid", "description": "Unique ID for this agreement document" },
    "household_id":       { "type": "string", "format": "uuid", "description": "Links to the household_mapping record" },
    "household_name":     { "type": "string", "example": "Stevens Family" },
    "advisor_id":         { "type": "string", "format": "uuid" },
    "practice_id":        { "type": "string", "format": "uuid" },
    "effective_date":     { "type": "string", "format": "date" },
    "expiration_date":    { "type": ["string", "null"], "format": "date", "description": "null = evergreen agreement" },
    "agreement_type":     { "type": "string", "enum": ["wrap", "AUM", "flat", "hybrid"] },
    "billing_frequency":  { "type": "string", "enum": ["quarterly", "monthly", "annual"] },
    "fee_tiers": {
      "type": "array",
      "description": "Ordered breakpoints. Engine applies first matching tier.",
      "items": {
        "type": "object",
        "required": ["tier_label", "aum_min", "aum_max", "bps"],
        "properties": {
          "tier_label": { "type": "string", "example": "Tier 1" },
          "aum_min":    { "type": "number", "description": "Inclusive lower bound in USD", "example": 0 },
          "aum_max":    { "type": ["number", "null"], "description": "Exclusive upper bound; null = no cap", "example": 1000000 },
          "bps":        { "type": "integer", "description": "Annual fee rate in basis points", "example": 100 }
        }
      },
      "example": [
        { "tier_label": "Tier 1", "aum_min": 0,       "aum_max": 1000000, "bps": 100 },
        { "tier_label": "Tier 2", "aum_min": 1000000,  "aum_max": 2000000, "bps": 90  },
        { "tier_label": "Tier 3", "aum_min": 2000000,  "aum_max": null,    "bps": 75  }
      ]
    },
    "fee_waivers": {
      "type": "array",
      "description": "Grandfathered or promotional waivers that override tier logic",
      "items": {
        "type": "object",
        "properties": {
          "waiver_id":    { "type": "string", "format": "uuid" },
          "account_id":   { "type": ["string", "null"], "description": "null = applies to all accounts in household" },
          "waiver_bps":   { "type": "integer", "description": "Reduction in bps, e.g. 10 means charge 10bps less than tier rate" },
          "reason":       { "type": "string", "example": "Legacy grandfathered rate — pre-2020 client" },
          "expiry":       { "type": ["string", "null"], "format": "date" }
        }
      }
    },
    "notes": { "type": "string", "description": "Raw extracted text for edge cases / auditor review" },
    "source_document_url": { "type": "string", "description": "S3 or CDN path to the original PDF" },
    "parsed_at": { "type": "string", "format": "date-time", "description": "Timestamp of OCR/LLM extraction" },
    "parse_confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "LLM confidence score for extraction" }
  }
}
```

---

## Schema 2 — Quarterly Billing Log (`billing_log_entry`)

One record per account per billing period, as exported from ClientWorks.
This is the ground truth of what was actually charged.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "billing_log_entry",
  "type": "object",
  "required": ["entry_id", "account_id", "household_id", "billing_period", "aum_billed", "bps_charged", "fee_dollar_amount", "billing_date"],
  "properties": {
    "entry_id":          { "type": "string", "format": "uuid" },
    "account_id":        { "type": "string", "description": "ClientWorks individual account ID" },
    "household_id":      { "type": "string", "format": "uuid", "description": "Links to household_mapping; populated by reconciliation engine if missing" },
    "practice_id":       { "type": "string", "format": "uuid" },
    "advisor_id":        { "type": "string", "format": "uuid" },
    "billing_period": {
      "type": "object",
      "required": ["year", "quarter"],
      "properties": {
        "year":    { "type": "integer", "example": 2025 },
        "quarter": { "type": "integer", "enum": [1, 2, 3, 4] }
      }
    },
    "billing_date":       { "type": "string", "format": "date", "description": "Date the fee was deducted" },
    "aum_billed":         { "type": "number", "description": "AUM value used to compute this fee, in USD" },
    "bps_charged":        { "type": "integer", "description": "Actual rate applied — the number the engine compares against agreement" },
    "fee_dollar_amount":  { "type": "number", "description": "Dollar fee charged (aum_billed * bps_charged / 10000 / 4 for quarterly)" },
    "billing_method":     { "type": "string", "enum": ["in-advance", "in-arrears"] },
    "fee_type":           { "type": "string", "enum": ["advisory", "platform", "overlay", "other"] },
    "status":             { "type": "string", "enum": ["posted", "reversed", "pending", "waived"] },
    "source_system":      { "type": "string", "enum": ["ClientWorks", "manual", "imported"] },

    "reconciliation": {
      "type": "object",
      "description": "Populated by the reconciliation engine after processing",
      "properties": {
        "expected_bps":          { "type": ["integer", "null"], "description": "BPS the engine computed from the agreement" },
        "expected_dollar_amount":{ "type": ["number", "null"] },
        "variance_bps":          { "type": ["integer", "null"], "description": "bps_charged - expected_bps; negative = undercharge" },
        "variance_dollar":       { "type": ["number", "null"], "description": "Annualized dollar impact of variance" },
        "discrepancy_type":      { "type": ["string", "null"], "enum": [null, "overcharge", "undercharge", "unbilled", "waiver_not_applied", "tier_not_applied"] },
        "discrepancy_reason":    { "type": ["string", "null"], "description": "Human-readable engine explanation" },
        "flagged":               { "type": "boolean", "default": false },
        "resolved":              { "type": "boolean", "default": false },
        "resolved_by":           { "type": ["string", "null"] },
        "resolved_at":           { "type": ["string", "null"], "format": "date-time" }
      }
    }
  }
}
```

---

## Schema 3 — Household Mapping (`household_mapping`)

Defines which sub-accounts belong to which household, and tracks aggregated AUM.
This is the join table that makes household-level tier calculation possible.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "household_mapping",
  "type": "object",
  "required": ["household_id", "household_name", "practice_id", "accounts", "total_aum"],
  "properties": {
    "household_id":   { "type": "string", "format": "uuid" },
    "household_name": { "type": "string", "example": "Stevens Family" },
    "practice_id":    { "type": "string", "format": "uuid" },
    "advisor_id":     { "type": "string", "format": "uuid" },
    "agreement_id":   { "type": "string", "format": "uuid", "description": "Active advisory_agreement for this household" },
    "total_aum": {
      "type": "number",
      "description": "Sum of current_aum across all active accounts — the number used for tier lookup",
      "example": 2200000
    },
    "aum_as_of": { "type": "string", "format": "date", "description": "Date total_aum was last calculated" },
    "accounts": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["account_id", "account_type", "current_aum", "is_active", "include_in_household_aum"],
        "properties": {
          "account_id":               { "type": "string", "description": "ClientWorks account ID" },
          "account_label":            { "type": "string", "example": "Stevens Family Brokerage" },
          "account_type":             { "type": "string", "enum": ["individual", "joint", "IRA", "Roth IRA", "trust", "529", "other"] },
          "current_aum":              { "type": "number", "description": "Current market value in USD" },
          "is_active":                { "type": "boolean" },
          "include_in_household_aum": {
            "type": "boolean",
            "description": "Some accounts (e.g. 529s) may be excluded from breakpoint aggregation per agreement"
          },
          "opened_date":  { "type": "string", "format": "date" },
          "closed_date":  { "type": ["string", "null"], "format": "date" }
        }
      }
    },
    "tier_qualified": {
      "type": "object",
      "description": "Computed field: which fee tier this household qualifies for given total_aum",
      "properties": {
        "tier_label": { "type": "string", "example": "Tier 3" },
        "bps":        { "type": "integer", "example": 75 }
      }
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

---

## How the Three Schemas Connect

```
advisory_agreement
    household_id ──────────────────────────────┐
                                               ▼
                                    household_mapping
                                        household_id ──── total_aum ──► tier_qualified.bps
                                        accounts[]
                                            account_id ───────────────────────────────────┐
                                                                                          ▼
                                                                             billing_log_entry
                                                                                 account_id
                                                                                 household_id
                                                                                 bps_charged
                                                                                 reconciliation.expected_bps
                                                                                 reconciliation.variance_bps  ◄── ENGINE COMPARES
```

## Reconciliation Engine Logic (pseudocode)

```
for each billing_log_entry in billing_period:
    household  = household_mapping.find(entry.household_id)
    agreement  = advisory_agreement.find(household.agreement_id)

    # 1. Aggregate AUM across all included sub-accounts
    total_aum  = sum(acct.current_aum for acct in household.accounts if acct.include_in_household_aum)

    # 2. Look up correct tier
    tier       = first tier where total_aum >= tier.aum_min and (total_aum < tier.aum_max or tier.aum_max is null)
    expected_bps = tier.bps

    # 3. Apply any active waivers
    for waiver in agreement.fee_waivers:
        if waiver is active and (waiver.account_id is null or waiver.account_id == entry.account_id):
            expected_bps -= waiver.waiver_bps

    # 4. Compare
    variance_bps   = entry.bps_charged - expected_bps
    variance_dollar = (variance_bps / 10000) * total_aum   # annualized

    # 5. Flag if outside tolerance
    if abs(variance_bps) > 0:
        entry.reconciliation.flagged         = True
        entry.reconciliation.expected_bps    = expected_bps
        entry.reconciliation.variance_bps    = variance_bps
        entry.reconciliation.variance_dollar = variance_dollar
        entry.reconciliation.discrepancy_type = "overcharge" if variance_bps > 0 else "undercharge"
```

---

## Field Cross-Reference (Join Keys)

| Field | advisory_agreement | household_mapping | billing_log_entry |
|---|:---:|:---:|:---:|
| `household_id` | ✓ | ✓ (PK) | ✓ |
| `agreement_id` | ✓ (PK) | ✓ | — |
| `account_id` | — | ✓ (in array) | ✓ |
| `practice_id` | ✓ | ✓ | ✓ |
| `advisor_id` | ✓ | ✓ | ✓ |
