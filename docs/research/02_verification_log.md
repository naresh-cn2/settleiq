# M2b Verification Log — Primary-Source Checks

**Date:** 2026-10-27
**Purpose:** Every claim carried forward from subagent reports into SettleIQ research was re-checked against the primary source before being accepted. This file records verified / unverified / contradicted status. Nothing here is a conclusion about SettleIQ; it is a record of what the sources actually say.

**Evidence classes:** A = official docs / pricing pages fetched directly · B = credible-unverified (vendor marketing, press, analyst) · C = anecdotal (reviews, forums) · D = unknown / not established

---

## RULE ADOPTED

A vendor's failure to publish a measurement methodology does **not** prove its software lacks internal auditability. Claims about competitor *capability* require positive evidence that the capability is absent — not absence of evidence that it is present.

---

## 1. VERIFIED — primary source fetched and quote confirmed

| # | Claim | Source | Class | Notes |
|---|---|---|---|---|
| V1 | Numeric pricing page states "Automated cash matching for up to 95% of your bank transactions" | numeric.io/pricing (fetched) | A | Confirmed verbatim. Units = **bank transactions**. |
| V2 | Numeric pricing is quote-based: "We take several pieces of information and business context into account, from number of transactions to number of seats" | numeric.io/pricing (fetched) | A | Confirmed verbatim. No dollar figures published. |
| V3 | Numeric blog: "buyers should still evaluate platforms on controls, explainability, and data quality over headline match-rate claims" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. |
| V4 | Numeric blog: reviewers "should see what was matched automatically, what was matched by suggestion, and what remains open, all in one place" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. |
| V5 | Numeric blog: "A strong platform captures who matched each transaction, who overrode a suggested match, who approved the reconciliation, and what changed after sign-off" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. |
| V6 | Numeric blog: platform must provide "timestamped, tamper-resistant evidence of every action for Section 302 and 404 requirements — not just a summary of who approved, but a complete record of what was matched, what was overridden, and what changed after sign-off" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. |
| V7 | Numeric blog: buyers should ask "whether your team can see why it suggested a match… what happens when the AI encounters a transaction type it hasn't seen before" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. |
| V8 | Numeric: "Real-time ERP integration pulls trial balance data directly from your GL (NetSuite, Xero, QuickBooks, Sage Intacct, or Workday), **with transaction-level detail for NetSuite**" | numeric.io/blog/reconciliation-automation (fetched) | A | Confirmed verbatim. Transaction-level depth is NetSuite-scoped, from the vendor itself. |
| V9 | Xero: "unreconciled bank statement data is not exposed via public APIs due to regulatory, contractual and risk constraints" | developer.xero.com/documentation/api/accounting/bankstatements (fetched) | A | Confirmed. |
| V10 | Xero admin (developer platform): "we have confirmed that we will not be adding the ability to reconcile bank statement lines via the API or to expose unreconciled bank statement data via the public API" — reason given: "Unreconciled bank statement lines are 'raw' banking data… treated as banking data under consumer data rights regimes" | xero.uservoice.com forum, Xero Developer Platform admin response (fetched) | A | Confirmed. **Reason is regulatory, not roadmap preference.** |
| V11 | Xero JAX: "JAX only automatically reconciles when it's highly confident. And in all cases, you can challenge or reject JAX's matches." JAX reconciles "using one of four methods" incl. "Rule" | xero.com/us/accounting-software/reconcile-bank-transactions (fetched) | A | Confirmed. Methods are named/explainable. |
| V12 | NetSuite: "Native NetSuite Bank Reconciliation does not take into account transaction fee reconciliation, which is included in NetSuite Pay Settlement and Fee Reconciliation." | docs.oracle.com NetSuite Pay Transaction Reconciliation FAQ (fetched) | A | Confirmed verbatim. |
| V13 | NetSuite: "Can I use Settlement and Fee Reconciliation if I'm not using Versapay? **No. This is only supported in NetSuite Pay.**" | same (fetched) | A | Confirmed verbatim. Fee reconciliation is processor-scoped to Versapay. |
| V14 | NetSuite: "The only manual steps required occur when there are payments that don't match between NetSuite and the payment processor." | same (fetched) | A | Confirmed verbatim. |
| V15 | NetSuite Open Settlement Report "reflects transactions that don't match… present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite" | same (fetched) | A | Confirmed verbatim. A vendor-published typed-discrepancy definition. |
| V16 | NetSuite: "If you manually edited a payment record in NetSuite, the auto-settlement will fail since the amounts don't match." | same (fetched) | A | Confirmed verbatim. Auto-matching is brittle to manual edits. |

---

## 2. NOT VERIFIED — source checked, quote absent

| # | Claim | Source checked | Status |
|---|---|---|---|
| U1 | Merge docs quote: "Receive vendor payment-related information in your application, **do reconciliation in your application**, and submit that information back" | docs.merge.dev/merge-unified/use-cases/vendor-reconciliation (fetched) | **NOT PRESENT.** The page instead reads: "your app can help your users keep their financial statements in balance, matching their payments to bills and reconciling the differences." Direction is consistent (Merge is a data-unification layer; the consuming app performs matching), but the exact quoted sentence could not be located. Treat the quote as **unverified**; the directional conclusion as **B**. |

---

## 3. CONTRADICTED / MATERIALLY OVERSTATED BY ME

| # | What I said earlier | What the source says |
|---|---|---|
| C1 | Two standalone reconciliation companies "exited the category in under 18 months" (counting Klarity) | Klarity was an **ASC 606 / contract-review revenue-recognition** vendor, renamed Within (Aug 2026) and divested its accounting platform to Cognida. That is a **different category** from payment/settlement reconciliation. Counting it was my category error. Only **Numeral** (payment operations, acquired by Mambu Dec 2024) is a genuine same-category exit. One data point, not two. |
| C2 | Numeric has "two different denominators for the same product" | Only one denominator is verified at the pricing page ("up to 95% of your **bank transactions**", V1). The claimed 90%+ figure on the cash-matching product page was **not fetched** and remains unverified. Do not assert the "two denominators" finding until that page is checked. |
| C3 | Klarity/Truewind positioned as direct settlement-reconciliation competitors | Klarity is revenue recognition; Truewind is AI bookkeeping/coding overlay for accounting firms. Neither is a settlement-decomposition product. Both should be classed **adjacent**, not direct. |

---

## 4. IMPLICATIONS FOR POSITIONING (evidence, not conclusions)

### 4.1 The "auditable AI / match provenance" space is occupied
Verified primary sources (V4–V7) show Numeric publishing, as capability requirements, the following: auto vs. suggested vs. open separation; who matched / who overrode / who approved; timestamped tamper-resistant evidence for SOX 302/404; and visibility of *why* a match was suggested. Xero (V11) names four JAX reconcile methods and guarantees the user can challenge or reject any match.

**Consequence:** "SettleIQ provides match provenance and rule traceability that incumbents lack" is **not supported**. That capability is documented by at least one mid-market vendor in its own product marketing and by Xero in its product docs.

### 4.2 What is *not* established either way
- No source examined states that Numeric, Ledge, or any competitor **cannot** decompose a Stripe/Adyen/Braintree settlement into charge → fee → refund → payout → bank deposit across multiple processors simultaneously. This is **D (unknown)**, not a proven gap.
- Numeric's verified transaction-level depth is NetSuite-only (V8); NetSuite's fee reconciliation is Versapay-only (V13). Whether that is a hard architectural boundary or a licensed-partner arrangement is **not established** by these sources.

### 4.3 A constraint that applies to SettleIQ, not just incumbents
Xero's API wall is **regulatory**: unreconciled bank statement lines are treated as raw banking data under consumer data rights regimes (V9, V10). Any design that proposes to act on a customer's behalf inside Xero — auto-reconciling their statement lines via API — would encounter the same barrier. This is not an incumbent weakness; it is a constraint on the integration path.

### 4.4 A corroborating signal for existing SettleIQ assets
NetSuite's own documentation (V15) defines discrepancies as "present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite," and (V14) confirms the exception path is manual. This is a vendor-published articulation of a two-sided presence/absence break — the same class of problem already modelled in `Forex-platform/reconciliation/reconciler.py`. Corroborating for the domain; **not** a market-gap proof.

---

## 5. OPEN VERIFICATION TASKS (must be closed before any positioning claim)

| Task | Target | Why it matters |
|---|---|---|
| Fetch Numeric cash-matching product page | numeric.io/product/cash-matching | Settles the "two denominators" question (C2) and reveals whether processor-side settlement tracing is claimed |
| Fetch Numeric integrations page | numeric.io/integrations | Determines which processors are natively supported and at what depth |
| Fetch Ledge cash-application solution page | ledge.co/solutions/cash-application | Establishes whether 3-way ERP + bank + PSP matching is charge-level or payout-level |
| Fetch Ledge pricing page | ledge.co/pricing | Verifies "single platform fee / no implementation fee" structure claim |
| Locate the Merge quote or drop it | docs.merge.dev (search) | U1 — currently unverified |
| Verify the Synder manual-payout limitation | synder.com/help/stripe-per-payout-limitations-manual-payouts-and-top-ups-explained | Cited in M2b-3 as a documented failure mode; not yet checked at source |
| Verify the Webgility "posts the fee side, not the whole payout" claim | webgility.com | M2b-3 classed it C; needs source check |

---

## 6. STATUS OF RESEARCH TRACKS

| Track | Status |
|---|---|
| M1 — payment reconciliation market | Complete |
| M2a — enterprise reconciliation platforms | Complete |
| M2b-2 — AI-native close startups | Received; **verified** (this file) |
| M2b-3 — GL tools, connectors, mid-market gap | Received; **partially verified** (Xero, NetSuite verified; Merge quote not) |
| M2b-1 — spend management / AP-AR (Ramp, Brex, BILL, Airbase) | Received; **partially verified** |

---

## 8. M2b-1 VERIFICATION — and the most consequential finding in this research

### 8.1 Verified

| # | Claim | Source | Class |
|---|---|---|---|
| V17 | **Ramp Stack launched June 3, 2026** — "an AI operating system built specifically for accounting firms" doing bank reconciliation, journal entries, prepaid/fixed-asset/deferred-revenue schedules, flux analysis, monthly close | prnewswire.com/news-releases/ramp-launches-stack-an-ai-operating-system-for-accounting-firms-302789630.html (fetched) | A |
| V18 | Ramp Stack: "Stack records every plan, source, action, and handoff in a **Session Audit Log**, giving teams a clear record of what happened and who did what." | ramp.com/blog/how-finance-teams-use-ramp-stack (fetched) | A |
| V19 | Ramp Stack: "Agents propose plans, ask questions, and route work to relevant reviewers within your existing processes" | same (fetched) | A |
| V20 | Ramp Stack: "**nothing syncs to your accounting system until you approve it**"; "Every session produces an exportable Session Audit Log" | ramp.com/blog/automated-bank-reconciliation + /accounting-reconciliation-software (fetched) | A |
| V21 | Ramp Stack: reusable firm procedures written in plain English as **"Skills"** that "agents follow them every month" | ramp.com/blog/account-reconciliation-software (fetched) | A |
| V22 | Ramp Stack standalone: "You can use Stack **on its own, without an existing Ramp account**. No credit application required." + "Get up and running within an hour" | ramp.com/blog/account-reconciliation-software (fetched) | A |
| V23 | Ramp Accounting Agent: "In QuickBooks Online and NetSuite, it handles credit card reconciliation end to end, matching transactions with **confidence scores** and a **full audit trail** so your team can verify every decision the Agent makes." | ramp.com/blog/payment-reconciliation (fetched) | A |
| V24 | Ramp Stack priced per-user, transparent tiers published: Free $0/user, Plus $15/user/mo + platform fee, Enterprise custom | ramp.com/pricing (via M2b-1; page not independently re-fetched by me) | B |
| V25 | Ramp Stack introductory free access ran through **August 31, 2026**; "Ramp has not published the ongoing price that follows that promotion" | therundown.ai/tools/stack-pk2rv | C |
| V26 | Ramp valued ~$44B after $750M Series F; 92 of the top 100 CPA firms in Ramp's partner network | beancount.io, PR Newswire | B |

### 8.2 Not verified

| # | Claim | Status |
|---|---|---|
| U2 | The exact Ramp sentence quoted by M2b-1: "Ramp Card reconciliation compares Ramp activity with transactions and balances imported from the card liability account in your accounting system, **not from your linked funding bank account**" | **NOT LOCATED** in Ramp help-center search results. Directionally supported by V20/V22 (Stack reconciles bank activity against GL) but the specific quoted limitation sentence is **unverified**. Do not cite it as verbatim until found. |
| U3 | Brex: "transactions older than 90 days will not sync"; documented duplicate payments that "will not auto-match" | Not checked at source. Class B pending. |

### 8.3 Consequence — the proposed wedge is substantially occupied

Verified sources now show, from vendors' own material:

- **Auditability** → Numeric (V4–V7), Ramp Stack (V18, V20), Ramp Accounting Agent (V23), Xero JAX (V11).
- **Explainability / confidence** → Ramp "confidence scores and a full audit trail so your team can verify every decision" (V23); agents "propose plans, ask questions" (V19); Xero's four named JAX methods (V11).
- **Human-in-the-loop gating** → Ramp Stack "nothing syncs… until you approve it" (V20); Numeric preparer-reviewer separation (V6).
- **Fast deployment** → Ramp Stack "up and running within an hour," standalone, no credit application (V22). This directly defeats any "deployable in under a day" positioning.
- **Published pricing** → Ramp Free $0 / Plus $15 per user (V24); BILL Essentials $49, Team $65, Corporate $89 per user (M2b-1, B); Brex Essentials $0 / Premium $12 (M2b-1, B). Published per-user pricing is standard, not differentiating.
- **Firm-channel distribution** → Ramp Stack into CPA firms with 92/100 partner penetration (V26). A new entrant has no comparable channel.

**Conclusion recorded, not argued:** every element of the differentiation thesis I previously recommended — auditable AI, match provenance, explainability, fast deployment, published pricing — is now documented by a funded competitor. The thesis as stated is **not viable**.

---

## 7. STANDING CONSTRAINTS ON THIS PROJECT

Until the open tasks in section 5 are closed and buyer contact exists:

1. No architecture decisions.
2. No language or framework selection.
3. No engine or algorithm specification.
4. No claim that incumbents lack auditable matching, charge-level decomposition, or explainability.
5. No claim that published pricing is a sufficient competitive advantage.
6. No statement that SettleIQ is commercially viable.
