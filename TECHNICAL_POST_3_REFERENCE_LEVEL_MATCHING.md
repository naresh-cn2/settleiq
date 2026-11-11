# Reference-Level Matching and Financial Discrepancy Detection in SettleIQ

> **Publication date:** November 10, 2026  
> **Production URL:** https://settleiq-zeta.vercel.app  
> **Repository:** github.com/naresh-cn2/settleiq  
> **Data note:** All examples use synthetic financial data only. No real customer information is used.

## Why Reference-Level Matching Matters

In financial reconciliation, matching by batch or date is insufficient. Multiple settlement references can share a batch, and matching at the batch level conflates distinct settlements. SettleIQ uses **settlement reference** as the primary matching key, falling back to batch only when no reference is present.

## How Reference-Level Matching Works

### Step 1: Decomposition by Reference

Each payout is decomposed into constituents whose settlement reference matches the payout's reference:

```
Payout pay-001 (BATCH-001, REF-001, $90.00)
├── Charge chg-001 (BATCH-001, REF-001, $100.00, +1)
└── Fee fee-001 (BATCH-001, REF-001, $10.00, -1)
    Reference match: REF-001 == REF-001 ✓
```

```
Payout pay-002 (BATCH-001, REF-002, $150.00)
├── Charge chg-002 (BATCH-001, REF-002, $200.00, +1)
└── Fee fee-002 (BATCH-001, REF-002, $20.00, -1)
    Reference match: REF-002 == REF-002 ✓
```

Even though both payouts share `BATCH-001`, they decompose independently because their references differ.

### Step 2: Net Calculation

For each decomposition, the engine computes:

```
net_expected = gross - fees - refunds - adjustments
residual = net_expected - net_paid
closes_exactly = (residual == 0)
```

### Step 3: Discrepancy Classification

When `closes_exactly` is false, the engine classifies the break:

| Break Type | Condition | Severity |
|------------|-----------|----------|
| NET_GROSS_BREAK | net_expected ≠ net_paid | HIGH |
| PHANTOM_PROCESSOR | Charge/fee has no payout | HIGH |
| PHANTOM_BANK | Payout has no charge/fee | HIGH |
| AMOUNT_BREAK | Matched pair amounts disagree | HIGH |

## Discrepancy Examples from the Three-Record Test

### REF-001: Exact Match (No Discrepancy)

Charge $100.00 − Fee $10.00 = Net $90.00 = Payout $90.00

```
Result: closes_exactly = true
No discrepancy generated
```

### REF-002: $30.00 Short Payment (NET_GROSS_BREAK)

Charge $200.00 − Fee $20.00 = Net $180.00 ≠ Payout $150.00

```
Residual: $30.00
Discrepancy: dsc:NET_GROSS_BREAK:pay-002
Type: NET_GROSS_BREAK
Severity: HIGH
Reason: "batch 'BATCH-001' nets 180.00|USD but the payout paid 150.00|USD; residual 30.00|USD"
```

### REF-003: Missing Payout (PHANTOM_PROCESSOR)

Charge $300.00 − Fee $30.00 = Net $330.00 ≠ No Payout

```
Discrepancy 1: dsc:PHANTOM_PROCESSOR:chg-003
Type: PHANTOM_PROCESSOR
Severity: HIGH
Reason: "charge in batch 'BATCH-002' has no payout on the processor side"

Discrepancy 2: dsc:PHANTOM_PROCESSOR:fee-003
Type: PHANTOM_PROCESSOR
Severity: HIGH
Reason: "fee in batch 'BATCH-002' has no payout on the processor side"
```

## Investigation Trace

Each discrepancy supports an autonomous investigation that produces:

- **Transaction trace:** Node graph showing gross, fees, net expected, net paid, residual
- **AI-generated hypotheses:** Ranked explanations with confidence scores (HIGH/MEDIUM/LOW/INSUFFICIENT)
- **Recommended action:** Suggested next step for the investigator

Example investigation output for REF-002:

```json
{
  "discrepancy_id": "dsc:NET_GROSS_BREAK:pay-002",
  "type": "NET_GROSS_BREAK",
  "severity": "HIGH",
  "trace": {
    "gross_amount": "200.00",
    "fee_amount": "20.00",
    "net_expected": "180.00",
    "net_paid": "150.00",
    "residual": "30.00"
  },
  "hypotheses": [
    {
      "rank": 1,
      "title": "Short payment",
      "description": "Payout paid $150.00 but $180.00 was expected",
      "confidence": "HIGH",
      "recommended_action": "Contact payer to remit remaining $30.00"
    }
  ]
}
```

## Discrepancy-to-Source Mapping

Every discrepancy maps to its actual source record ID, not a batch aggregate:

```python
# Valid: constituent_id is an actual input record ID
dsc:PHANTOM_PROCESSOR:chg-003 → constituent_id = "chg-003"

# Invalid: would be rejected
dsc:NET_GROSS_BREAK:pay-002 → constituent_id = "BATCH-001"  ← rejected
```

This ensures investigators can trace every discrepancy back to the specific record that caused it.

## Severity Matrix

Severity is derived from a declared matrix, never manual judgement:

| Type Prefix | Severity |
|-------------|----------|
| AMOUNT_BREAK, NET_GROSS_BREAK, RULE_CONFLICT, CURRENCY_BREAK, UNKNOWN | HIGH |
| PHANTOM_* | HIGH |
| TIMING_BREAK, SETTLEMENT_LAG_BREAK | MEDIUM |
| FEE_*, AMBIGUOUS_MATCH, INSUFFICIENT_EVIDENCE, SIDE_MISMATCH | MEDIUM |

## Implementation

**File:** `src/settleiq/engine/decompose.py` (lines 112-202)
**File:** `src/settleiq/engine/discrepancy.py` (lines 1-146)
**File:** `src/settleiq/engine/reconcile.py` (lines 1-560)

## Production Verification

All examples verified against the live production deployment at https://settleiq-zeta.vercel.app:

- REF-001: closes exactly, no discrepancy ✅
- REF-002: NET_GROSS_BREAK with $30.00 residual, HIGH severity ✅  
- REF-003: PHANTOM_PROCESSOR for both charge and fee, HIGH severity ✅
- All examples use synthetic data only — no real customer financial information
