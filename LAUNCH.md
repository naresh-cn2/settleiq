# SettleIQ — Public Release v0.1.0

## Overview

SettleIQ is an open-source financial reconciliation platform that helps finance teams and developers match payment transactions, processor payouts, and bank deposits with exact decimal arithmetic and cryptographic audit trails.

**Live Demo:** https://settleiq-zeta.vercel.app  
**GitHub:** https://github.com/naresh-cn2/settleiq

## What SettleIQ Does

SettleIQ helps finance teams and developers answer: *"Where did the money go?"*

It reconciles payment transactions, processor payouts, and bank deposits to identify:
- Successfully matched records
- Missing payments (phantom processor/bank)
- Incorrect amounts (amount breaks)
- Unexpected fees (net/gross breaks)
- Timing differences (settlement lag)
- Duplicate or ambiguous transactions
- Unexplained discrepancies (UNKNOWN type)

## Who Is It For

- **Finance operations teams** who need to reconcile payments without spreadsheets
- **Developers** building reconciliation into their applications (via API)
- **Accountants and auditors** who need tamper-evident audit trails
- **Small businesses** processing payments through Stripe, bank transfers, etc.

## Key Features

| Feature | Description |
|---------|-------------|
| Exact Decimal Arithmetic | No float errors — all money uses exact Decimal |
| Payout Decomposition | Breaks down payouts into charges, fees, refunds |
| Discrepancy Detection | 7 typed discrepancy categories |
| Investigation Workspace | Hypotheses, evidence, trace, resolution workflow |
| Hash-Chained Audit Journal | Tamper-evident record of all actions |
| CSV/JSON Export | Export runs and discrepancies |
| API Access | Full REST API for developers |
| Public Demo | Try it without signing up |

## How It Works

1. **Import data** — Upload CSV or JSON with charges, fees, payouts, deposits
2. **Validate** — System checks for missing fields, invalid amounts, duplicates
3. **Reconcile** — Engine matches records using reference and amount rules
4. **Investigate** — View discrepancies, transaction traces, and hypotheses
5. **Resolve** — Record resolutions with reasons and audit trails
6. **Export** — Download results as JSON or CSV

## Getting Started

### Option 1: Try the Public Demo (No Account Needed)
Visit https://settleiq-zeta.vercel.app and click "Explore Public Demo"

### Option 2: Create a Free Account
Visit https://settleiq-zeta.vercel.app/signup

### Option 3: Self-Host
```bash
git clone https://github.com/naresh-cn2/settleiq.git
cd settleiq
pip install -e ".[dev]"
python -m settleiq.cli run
```

## Pricing Tiers

| Plan | Price | Records/Month | Best For |
|------|-------|---------------|----------|
| Free | $0 | 1,000 | Individuals testing |
| Starter | $49/month | 10,000 | Freelancers, small businesses |
| Growth | $149/month | 100,000 | Growing finance teams |
| Business | $499/month | 1,000,000 | Larger finance teams |

## Security & Data

- All demo data is synthetic (no real financial data)
- Data is encrypted in transit and at rest
- Tenant isolation between organizations
- Audit journal records all actions
- No live banking connections (import CSV/JSON only)

## Feedback

We're in early release and would love your feedback. Please share:
- What reconciliation problems do you face?
- What features would make SettleIQ useful for you?
- Would you pay for this? How much?

Contact: [GitHub Issues](https://github.com/naresh-cn2/settleiq/issues)

---

*SettleIQ is an open-source project. All code is available on GitHub.*