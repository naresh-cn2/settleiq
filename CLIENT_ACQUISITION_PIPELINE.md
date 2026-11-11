# SettleIQ — B2B Client Acquisition Pipeline

## Service Offer

### SettleIQ Financial Reconciliation Engineering

**Product:** SettleIQ — deterministic, exact-decimal payment settlement reconciliation and discrepancy investigation engine.

**Core Capabilities:**
- Constituent-level payout decomposition with exact-decimal arithmetic
- Reference-level matching (prevents batch cross-contamination)
- Closed discrepancy taxonomy with severity classification
- Hash-chained audit journal for tamper-evident recordkeeping
- Idempotent reconciliation runs
- AI-backed discrepancy investigation with confidence scores
- API-first architecture with fail-closed authentication

**Service Model:**
- **SettleIQ Platform:** Licensed reconciliation engine deployed on customer infrastructure or managed cloud
- **Integration Engineering:** Custom adapters for payment processors, banks, and ERP systems
- **Reconciliation Rules Engineering:** Rule authoring, testing, and versioning for customer-specific settlement logic
- **Audit & Compliance:** Journal verification, discrepancy investigation workflows, regulatory reporting support

**Target Verticals:**
- Payment processors and gateways
- Fintech platforms with payout reconciliation needs
- E-commerce marketplaces with split payments
- Insurance carriers with claims payment reconciliation
- Financial services with multi-bank settlement

---

## Prospect Register

| # | Prospect | Vertical | Research Status | Problem | Proposal Status | Follow-up Status |
|---|----------|----------|-----------------|---------|-----------------|------------------|
| 1 | Stripe | Payment Processing | Pending | Payout reconciliation at scale; disputed settlements | Not started | Not started |
| 2 | Adyen | Payment Processing | Pending | Multi-currency settlement reconciliation; fee attribution | Not started | Not started |
| 3 | Shopify | E-commerce Marketplace | Pending | Split payment reconciliation across merchants | Not started | Not started |
| 4 | Brex | Fintech / Corporate Cards | Pending | Card transaction reconciliation; expense matching | Not started | Not started |
| 5 | Gusto | Payroll / Benefits | Pending | Payroll settlement reconciliation; tax payment matching | Not started | Not started |

---

## Prospect Dossiers

### Prospect 1: Stripe

**Profile:**
- **Company:** Stripe, Inc.
- **Vertical:** Payment Processing
- **Size:** Late-stage private / public company
- **Headquarters:** San Francisco, CA
- **Website:** stripe.com

**Potential Problem:**
Stripe processes billions in payments across millions of businesses. Payout reconciliation — matching charges, fees, refunds, and payouts — is a core operational challenge. Settlements can span multiple payment methods, currencies, and geographic regions, creating complex matching scenarios.

**How SettleIQ Helps:**
- Reference-level matching prevents batch cross-contamination (our fixed defect)
- Exact-decimal arithmetic eliminates floating-point reconciliation errors
- Hash-chained audit journal provides tamper-evident records for regulatory compliance
- Discrepancy investigation with AI hypotheses accelerates issue resolution
- API-first architecture integrates with Stripe's existing payout infrastructure

**Evidence from Our Implementation:**
- 213 backend tests pass with 0 failures
- Three-record synthetic dataset: REF-001 exact match, REF-002 $30 short payment detected, REF-003 missing payout detected
- Production deployment at `https://settleiq-zeta.vercel.app` with 28/28 E2E tests passing

---

### Prospect 2: Adyen

**Profile:**
- **Company:** Adyen N.V.
- **Vertical:** Payment Processing
- **Size:** Public (Euronext Amsterdam: ADYEN)
- **Headquarters:** Amsterdam, Netherlands
- **Website:** adyen.com

**Potential Problem:**
Adyen processes payments across 200+ payment methods and 185+ currencies. Reconciling settlements across different payment schemes (cards, bank transfers, wallets) with varying fee structures and settlement timing is complex.

**How SettleIQ Helps:**
- Multi-currency support via exact-decimal Money type
- Reference-level matching across different payment schemes
- NET_GROSS_BREAK detection for short payments
- PHANTOM_PROCESSOR/PHANTOM_BANK detection for missing settlements
- Configurable settlement window for cross-border timing differences

---

### Prospect 3: Shopify

**Profile:**
- **Company:** Shopify Inc.
- **Vertical:** E-commerce Marketplace
- **Size:** Public (NYSE: SHOP)
- **Headquarters:** Ottawa, Canada
- **Website:** shopify.com

**Potential Problem:**
Shopify processes payments for over 2 million merchants. Split payments (marketplace platform fee + merchant payout) need to be reconciled against payouts. Chargebacks, refunds, and disputed transactions create ongoing reconciliation complexity.

**How SettleIQ Helps:**
- Constituent-level decomposition handles split payments (charges + fees + refunds)
- PHANTOM_PROCESSOR detection identifies charges without payouts
- PHANTOM_BANK detection identifies payouts without corresponding charges
- Discrepancy resolution workflow supports chargeback investigation
- Idempotent runs prevent duplicate reconciliation of the same settlement

---

### Prospect 4: Brex

**Profile:**
- **Company:** Brex Inc.
- **Vertical:** Fintech / Corporate Cards
- **Size:** Late-stage private
- **Headquarters:** San Francisco, CA
- **Website:** brex.com

**Potential Problem:**
Brex issues corporate cards and manages expense reconciliation. Card transactions need to be matched against cardholder statements, receipts, and accounting system entries. Missing receipts and mismatched amounts create reconciliation backlog.

**How SettleIQ Helps:**
- INSUFFICIENT_EVIDENCE classification for transactions without receipts
- AMOUNT_BREAK detection for transaction amount mismatches
- Audit journal provides tamper-evident record for expense audits
- Investigation trace helps identify the root cause of mismatches
- Discrepancy resolution workflow supports receipt collection and correction

---

### Prospect 5: Gusto

**Profile:**
- **Company:** Gusto, Inc.
- **Vertical:** Payroll / Benefits
- **Size:** Late-stage private
- **Headquarters:** San Francisco, CA
- **Website:** gusto.com

**Potential Problem:**
Gusto processes payroll for hundreds of thousands of small businesses. Payroll settlements need to be reconciled against bank disbursements, tax payments, and benefits contributions. Timing differences between payroll run date and bank settlement date create reconciliation gaps.

**How SettleIQ Helps:**
- Configurable settlement window for timing differences
- TIMING_BREAK and SETTLEMENT_LAG_BREAK classification
- NET_GROSS_BREAK detection for payroll amount discrepancies
- Audit journal for payroll compliance and audit readiness
- Duplicate submission prevention via idempotent runs

---

## Personalized Proposal Templates

Each proposal includes:

1. **Executive Summary** — Value proposition tailored to the prospect's vertical
2. **Problem Statement** — Specific reconciliation challenges faced by the prospect
3. **Solution** — How SettleIQ addresses each challenge
4. **Technical Architecture** — Integration points, data flow, security model
5. **Implementation Plan** — Phased rollout with success criteria
6. **Pricing** — License fees, implementation services, ongoing support
7. **Case Evidence** — Test results, production deployment metrics, defect resolution examples

**Note:** Proposals are prepared but NOT sent. Outreach requires client authorization.

---

## Next Actions (Pending Authorization)

1. Research each prospect's public financials, engineering blog posts, and hiring signals
2. Customize proposal templates with prospect-specific details
3. Prepare outreach sequences (email, LinkedIn)
4. Obtain authorization before sending any proposals