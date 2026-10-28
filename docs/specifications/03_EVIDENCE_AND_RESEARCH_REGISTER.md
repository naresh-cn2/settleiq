# 03 — Evidence and Research Register

**Document ID:** SETTLEIQ-EVD-001
**Title:** SettleIQ Evidence and Research Register — Verified Claims, Verification Discipline, and Research Phase Status
**Version:** 1.0.0
**Status:** PROPOSED — register of completed research; not a source of requirements
**Domain:** Research record, evidence classes, verified vs. unverified vs. contradicted claims, research phase status
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/03_EVIDENCE_AND_RESEARCH_REGISTER.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §1.2, §1.3, §8 (row 03); SETTLEIQ-REQ-001, SETTLEIQ-REQ-000

---

## Document Control

### Purpose

This document preserves the completed market research as **evidence**, and records the verification discipline that was applied to it. It exists so that:

1. every claim SettleIQ artifacts rely on is traceable to a primary source that was actually fetched;
2. claims that were checked and found absent are recorded as such and cannot silently become facts; and
3. one prior conclusion that its own source contradicted is recorded with its correction.

This document is a register, not an analysis. It adds no claim that does not appear in the source verification log. Where a URL is given, it is the URL recorded in that log. No URL has been reconstructed, inferred, or supplied from memory.

### Source of record

The primary source for every entry below is `docs/research/02_verification_log.md` ("M2b Verification Log — Primary-Source Checks", dated 2026-10-27). That log is append-only and is the authoritative record of verification status. This document reorganises it for specification purposes; it does not re-verify anything, and it does not extend it. Where this document and the log differ, **the log governs.**

### Evidence classes

As defined in the log:

| Class | Meaning |
|---|---|
| **A** | Official docs / pricing pages fetched directly |
| **B** | Credible-unverified (vendor marketing, press, analyst) |
| **C** | Anecdotal (reviews, forums) |
| **D** | Unknown / not established |

### Verification statuses

| Status | Meaning |
|---|---|
| **VERIFIED** | Primary source fetched; the quoted text was confirmed present in the source |
| **NOT VERIFIED** | Source checked; the quoted text was absent, or the source was not checked at all |
| **CONTRADICTED** | A prior statement was materially incorrect or overstated relative to what the source says |

---

## 1. Verified Claims Carried in the Verification Log

All entries below are **VERIFIED** unless their row says otherwise. Class and source URL are reproduced from the log without alteration.

### 1.1 Numeric — pricing page and reconciliation-automation blog

| ID | Claim | Source URL | Class | Verified status |
|---|---|---|---|---|
| V1 | Numeric pricing page states "Automated cash matching for up to 95% of your bank transactions" | numeric.io/pricing | A | VERIFIED — confirmed verbatim. Units are **bank transactions** |
| V2 | Numeric pricing is quote-based: "We take several pieces of information and business context into account, from number of transactions to number of seats" | numeric.io/pricing | A | VERIFIED — confirmed verbatim. No dollar figures published |
| V3 | Numeric blog: "buyers should still evaluate platforms on controls, explainability, and data quality over headline match-rate claims" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim |
| V4 | Numeric blog: reviewers "should see what was matched automatically, what was matched by suggestion, and what remains open, all in one place" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim |
| V5 | Numeric blog: "A strong platform captures who matched each transaction, who overrode a suggested match, who approved the reconciliation, and what changed after sign-off" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim |
| V6 | Numeric blog: platform must provide "timestamped, tamper-resistant evidence of every action for Section 302 and 404 requirements — not just a summary of who approved, but a complete record of what was matched, what was overridden, and what changed after sign-off" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim |
| V7 | Numeric blog: buyers should ask "whether your team can see why it suggested a match… what happens when the AI encounters a transaction type it hasn't seen before" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim |
| V8 | Numeric: "Real-time ERP integration pulls trial balance data directly from your GL (NetSuite, Xero, QuickBooks, Sage Intacct, or Workday), **with transaction-level detail for NetSuite**" | numeric.io/blog/reconciliation-automation | A | VERIFIED — confirmed verbatim. Transaction-level depth is NetSuite-scoped, from the vendor itself |

### 1.2 Xero — API constraint and JAX reconciliation

| ID | Claim | Source URL | Class | Verified status |
|---|---|---|---|---|
| V9 | Xero: "unreconciled bank statement data is not exposed via public APIs due to regulatory, contractual and risk constraints" | developer.xero.com/documentation/api/accounting/bankstatements | A | VERIFIED — confirmed |
| V10 | Xero Developer Platform admin: "we have confirmed that we will not be adding the ability to reconcile bank statement lines via the API or to expose unreconciled bank statement data via the public API" — reason given: unreconciled bank statement lines are "'raw' banking data… treated as banking data under consumer data rights regimes" | xero.uservoice.com (Xero Developer Platform admin response) | A | VERIFIED — confirmed. **The reason is regulatory, not roadmap preference** |
| V11 | Xero JAX: "JAX only automatically reconciles when it's highly confident. And in all cases, you can challenge or reject JAX's matches." JAX reconciles "using one of four methods" including "Rule" | xero.com/us/accounting-software/reconcile-bank-transactions | A | VERIFIED — confirmed. Methods are named and explainable |

### 1.3 NetSuite — settlement and fee reconciliation

All four rows share one source: the NetSuite Pay Transaction Reconciliation FAQ at docs.oracle.com, fetched directly.

| ID | Claim | Source URL | Class | Verified status |
|---|---|---|---|---|
| V12 | NetSuite: "Native NetSuite Bank Reconciliation does not take into account transaction fee reconciliation, which is included in NetSuite Pay Settlement and Fee Reconciliation." | docs.oracle.com (NetSuite Pay Transaction Reconciliation FAQ) | A | VERIFIED — confirmed verbatim |
| V13 | NetSuite: "Can I use Settlement and Fee Reconciliation if I'm not using Versapay? **No. This is only supported in NetSuite Pay.**" | docs.oracle.com (NetSuite Pay Transaction Reconciliation FAQ) | A | VERIFIED — confirmed verbatim. Fee reconciliation is processor-scoped to Versapay |
| V14 | NetSuite: "The only manual steps required occur when there are payments that don't match between NetSuite and the payment processor." | docs.oracle.com (NetSuite Pay Transaction Reconciliation FAQ) | A | VERIFIED — confirmed verbatim |
| V15 | NetSuite Open Settlement Report "reflects transactions that don't match… present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite" | docs.oracle.com (NetSuite Pay Transaction Reconciliation FAQ) | A | VERIFIED — confirmed verbatim. A vendor-published typed-discrepancy definition |
| V16 | NetSuite: "If you manually edited a payment record in NetSuite, the auto-settlement will fail since the amounts don't match." | docs.oracle.com (NetSuite Pay Transaction Reconciliation FAQ) | A | VERIFIED — confirmed verbatim. Auto-matching is brittle to manual edits |

### 1.4 Ramp Stack and Ramp Accounting Agent

| ID | Claim | Source URL | Class | Verified status |
|---|---|---|---|---|
| V17 | **Ramp Stack launched June 3, 2026** — "an AI operating system built specifically for accounting firms" doing bank reconciliation, journal entries, prepaid/fixed-asset/deferred-revenue schedules, flux analysis, monthly close | prnewswire.com/news-releases/ramp-launches-stack-an-ai-operating-system-for-accounting-firms-302789630.html | A | VERIFIED — fetched |
| V18 | Ramp Stack: "Stack records every plan, source, action, and handoff in a **Session Audit Log**, giving teams a clear record of what happened and who did what." | ramp.com/blog/how-finance-teams-use-ramp-stack | A | VERIFIED — fetched |
| V19 | Ramp Stack: "Agents propose plans, ask questions, and route work to relevant reviewers within your existing processes" | ramp.com/blog/how-finance-teams-use-ramp-stack | A | VERIFIED — fetched |
| V20 | Ramp Stack: "**nothing syncs to your accounting system until you approve it**"; "Every session produces an exportable Session Audit Log" | ramp.com/blog/automated-bank-reconciliation and ramp.com/accounting-reconciliation-software | A | VERIFIED — fetched |
| V21 | Ramp Stack: reusable firm procedures written in plain English as **"Skills"** that "agents follow them every month" | ramp.com/blog/account-reconciliation-software | A | VERIFIED — fetched |
| V22 | Ramp Stack standalone: "You can use Stack **on its own, without an existing Ramp account**. No credit application required." plus "Get up and running within an hour" | ramp.com/blog/account-reconciliation-software | A | VERIFIED — fetched |
| V23 | Ramp Accounting Agent: "In QuickBooks Online and NetSuite, it handles credit card reconciliation end to end, matching transactions with **confidence scores** and a **full audit trail** so your team can verify every decision the Agent makes." | ramp.com/blog/payment-reconciliation | A | VERIFIED — fetched |
| V24 | Ramp Stack priced per-user, transparent tiers published: Free $0/user, Plus $15/user/mo plus platform fee, Enterprise custom | ramp.com/pricing | **B** | VERIFIED as recorded in class B — the log records that this page was **not independently re-fetched** by the verifier (sourced via M2b-1) |
| V25 | Ramp Stack introductory free access ran through **August 31, 2026**; "Ramp has not published the ongoing price that follows that promotion" | therundown.ai/tools/stack-pk2rv | **C** | VERIFIED as recorded in class C |
| V26 | Ramp valued approximately $44B after a $750M Series F; 92 of the top 100 CPA firms in Ramp's partner network | beancount.io, PR Newswire | **B** | VERIFIED as recorded in class B |

### 1.5 Per-seat pricing recorded in the log's consequences section

The log's section 8.3 records, in class B via the M2b-1 track and without re-fetching at source: Ramp Free $0 / Plus $15 per user (consistent with V24); BILL Essentials $49, Team $65, Corporate $89 per user; Brex Essentials $0 / Premium $12. These are recorded here as class B and are **not** restated as verified pricing. No pricing figure in this register is class A except where the log marks it so.

---

## 2. Claims Found NOT VERIFIED

Each of the following was checked and found absent, or was not checked at source. None may be cited as fact anywhere in SettleIQ's artifacts.

### U1 — Merge quote

* **Claim:** Merge docs quote — "Receive vendor payment-related information in your application, **do reconciliation in your application**, and submit that information back"
* **Source checked:** docs.merge.dev/merge-unified/use-cases/vendor-reconciliation (fetched)
* **Status:** **NOT VERIFIED.** The quoted sentence is **not present** on the page. The page instead reads: "your app can help your users keep their financial statements in balance, matching their payments to bills and reconciling the differences."
* **Reason:** the specific quoted sentence could not be located. The direction of the underlying conclusion is consistent — Merge is a data-unification layer and the consuming application performs matching — but the log directs that the quote be treated as unverified and the directional conclusion be classed **B**.

### U2 — Ramp card-reconciliation limitation sentence

* **Claim:** the exact Ramp sentence quoted by the M2b-1 track — "Ramp Card reconciliation compares Ramp activity with transactions and balances imported from the card liability account in your accounting system, **not from your linked funding bank account**"
* **Source checked:** Ramp help-center search results
* **Status:** **NOT VERIFIED.** The sentence was **not located**. It is directionally supported by V20 and V22 (Stack reconciles bank activity against the GL), but the specific quoted limitation is unverified.
* **Reason:** the exact wording could not be found at source. The log directs that it not be cited as verbatim until located.

### U3 — Brex sync and duplicate-payment limitations

* **Claim:** Brex — "transactions older than 90 days will not sync"; documented duplicate payments that "will not auto-match"
* **Source checked:** none
* **Status:** **NOT VERIFIED.** Not checked at source. Class **B** pending.
* **Reason:** no source check was performed. It remains an unverified claim with no basis for citation.

### Not established either way (class D)

The log records two matters as explicitly **not established**, rather than as gaps in either direction:

* **No source examined states** that Numeric, Ledge, or any other vendor **cannot** decompose a Stripe, Adyen, or Braintree settlement into charge → fee → refund → payout → bank deposit across multiple processors simultaneously. This is **D (unknown)**, not a proven gap.
* Numeric's verified transaction-level depth is NetSuite-only (V8); NetSuite's fee reconciliation is Versapay-only (V13). Whether that is a hard architectural boundary or a licensed-partner arrangement is **not established** by these sources.

---

## 3. Corrected Conclusions

Three earlier statements were contradicted or materially overstated by their own sources. Each is recorded here with what replaced it. These corrections are load-bearing: each one removed a claim that would otherwise have been available for competitive positioning.

### C1 — Category error in counting vendor exits

* **What was said earlier:** two standalone reconciliation companies "exited the category in under 18 months", counting Klarity.
* **What the source says:** Klarity was an **ASC 606 / contract-review revenue-recognition** vendor, renamed Within in August 2026, and divested its accounting platform to Cognida. That is a **different category** from payment/settlement reconciliation. Counting it was a category error.
* **What replaced it:** only **Numeral** (payment operations, acquired by Mambu in December 2024) is a genuine same-category exit. That is **one data point, not two.**
* **Consequence for SettleIQ:** a "consolidation or market-shakeout" narrative is not available. There is no basis for it.

### C2 — Withdrawn claim of conflicting denominators

* **What was said earlier:** Numeric has "two different denominators for the same product".
* **What the source says:** only **one** denominator is verified at the pricing page — "up to 95% of your **bank transactions**" (V1). The claimed 90%+ figure on the cash-matching product page was **not fetched** and remains unverified.
* **What replaced it:** a single verified denominator with unverified units. The log directs that the "two denominators" finding not be asserted until that page is checked.
* **Consequence for SettleIQ:** no claim about any vendor's measurement methodology being internally inconsistent may be made. This is precisely the discipline SETTLEIQ-REQ-013 inverts onto SettleIQ itself: SettleIQ publishes its own denominator definition rather than characterising anyone else's.

### C3 — Adjacent vendors reclassified

* **What was said earlier:** Klarity and Truewind were positioned as direct settlement-reconciliation competitors.
* **What the source says:** Klarity is revenue recognition; Truewind is an AI bookkeeping/coding overlay for accounting firms. Neither is a settlement-decomposition product.
* **What replaced it:** both are classed **adjacent**, not direct.
* **Consequence for SettleIQ:** the competitive set was never established, and no comparative analysis rests on it.

### The standing rule that produced these corrections

The log adopts one rule explicitly, and this register carries it forward as SettleIQ's own discipline:

> A vendor's failure to publish a measurement methodology does **not** prove its software lacks internal auditability. Claims about competitor *capability* require positive evidence that the capability is absent — not absence of evidence that it is present.

Applied to SettleIQ, the same rule runs in the other direction: SettleIQ does not assert that any vendor lacks a practice merely because SettleIQ cannot observe it. SETTLEIQ-REQ-013/014 require SettleIQ to demonstrate the measurement practice on itself, on data a third party can inspect — not to characterise anyone else's practice.

---

## 4. How This Evidence Is and Is Not Used

### 4.1 How it is used

This evidence informs two things and only two things:

1. **The problem framing.** It establishes that processor vendors document payout decomposition as the merchant's responsibility (Stripe for manual and instant payouts; Braintree stating its own settlement summary tools should not be used for reconciliation; Adyen paying net-of-costs and requiring gross-to-net bridging), and that third-party GL tooling does not supply the layer. That is the engineering problem stated in `02_PROBLEM_AND_USE_CASES.md` §2. It also supplies the Class A record that raw bank statement lines are not exposed via public API for regulatory reasons (V9, V10), which is a constraint on the integration path and appears as FM-P10 in `02` §6.
2. **The decision rationale.** It records why the commercial-differentiation frame was closed on 2026-10-27 and the employment-artifact frame adopted, and it supplies the evidence behind the five engineering decisions recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`.

### 4.2 How it is not used

* **It is not a source of engineering requirements.** No requirement in any SettleIQ specification derives from a market-research finding. Requirements derive from the domain problem and from the OWNER-defined frame, and they are owned and testable within this repository. A vendor's published capability is evidence about that vendor; it is not evidence about what SettleIQ must build.
* **It does not license any competitive claim.** The verified evidence establishes that auditability, explainability, human-approval gating, and confidence scoring are **documented capabilities** of funded products (Numeric V4–V7; Ramp Stack V18, V20; Ramp Accounting Agent V23; Xero JAX V11). Any artifact asserting that SettleIQ provides something incumbents lack is defective under SETTLEIQ-REQ-001 and must be corrected before it counts as deliverable evidence.
* **It does not establish a gap, a market, or a segment.** No market-size, market-gap, or underserved-segment claim is supported by anything in the log. The research that would support such a claim was not obtained.
* **It does not establish a scale target, an accuracy benchmark, or a performance expectation.** Nothing in the log describes the performance of any product, and no figure from it may be used as a target for SettleIQ's own benchmark.
* **Class B and C entries are not facts.** V24, V25, V26, the BILL and Brex pricing figures, and U3's directional reading are class B or C. They are recorded for completeness of the register and are not load-bearing for any requirement.

### 4.3 What the evidence supports, stated as a discipline rather than a claim

The verified record supports one statement about SettleIQ's own conduct: SettleIQ publishes its auto-match rate with an explicit, documented measurement methodology — denominator definition, population, time window, and treatment of human-confirmed matches — computed from instrumented counts by the system itself (SETTLEIQ-REQ-013, REQ-014). The verified record supports **no** accompanying statement about any named product. The practice is demonstrated on SettleIQ, on data a third party can inspect.

---

## 5. Research Phase Status

**The research phase is complete and closed.** It closed on 2026-10-27, when the OWNER selected the employment-artifact frame and the commercial-differentiation frame was abandoned. No research track is open for the purposes of SettleIQ's specifications.

### 5.1 Track status, as recorded in the verification log

| Track | Status |
|---|---|
| M1 — payment reconciliation market | Complete |
| M2a — enterprise reconciliation platforms | Complete |
| M2b-2 — AI-native close startups | Received; **verified** |
| M2b-3 — GL tools, connectors, mid-market gap | Received; **partially verified** — Xero and NetSuite verified; the Merge quote not |
| M2b-1 — spend management / AP-AR (Ramp, Brex, BILL, Airbase) | Received; **partially verified** |

Two tracks are recorded as **partially verified**, not complete. This register reproduces that status rather than upgrading it. The research phase is closed for the purpose of the frame decision; it is not closed in the sense that every claim raised within it has been verified, and §5.2 records what remains open.

### 5.2 Verification tasks recorded as open in the log

These were logged in the log's own "open verification tasks" section as tasks that must be closed before any positioning claim. They are reproduced here unchanged. They are open in the sense that the log never records them as closed; the frame decision made them unnecessary rather than resolving them.

| Task | Target | Why it mattered |
|---|---|---|
| Fetch the Numeric cash-matching product page | numeric.io/product/cash-matching | Settles the "two denominators" question (C2) and reveals whether processor-side settlement tracing is claimed |
| Fetch the Numeric integrations page | numeric.io/integrations | Determines which processors are natively supported and at what depth |
| Fetch the Ledge cash-application solution page | ledge.co/solutions/cash-application | Establishes whether 3-way ERP + bank + PSP matching is charge-level or payout-level |
| Fetch the Ledge pricing page | ledge.co/pricing | Verifies the "single platform fee / no implementation fee" structure claim |
| Locate the Merge quote or drop it | docs.merge.dev (search) | U1 — currently unverified |
| Verify the Synder manual-payout limitation | synder.com/help/stripe-per-payout-limitations-manual-payouts-and-top-ups-explained | Cited in M2b-3 as a documented failure mode; not yet checked at source |
| Verify the Webgility claim that it "posts the fee side, not the whole payout" | webgility.com | M2b-3 classed it C; needs source check |

**Standing position on these tasks:** they may not be closed by assertion, and no SettleIQ artifact may depend on their outcome. Because the frame is employment-artifact and not commercial, they do not block any specification in this repository. They remain recorded so that the register is not read as claiming more verification than was performed.

### 5.3 Standing constraints the log placed on the project

The log's standing constraints are reproduced here because they are the origin of the non-claims in SETTLEIQ-REQ-001. Until the open tasks above are closed and buyer contact exists, the log recorded:

1. No architecture decisions.
2. No language or framework selection.
3. No engine or algorithm specification.
4. No claim that incumbents lack auditable matching, charge-level decomposition, or explainability.
5. No claim that published pricing is a sufficient competitive advantage.
6. No statement that SettleIQ is commercially viable.

Items 1–3 have since been superseded by the OWNER's frame decision of 2026-10-27 and the five verified engineering decisions recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`. Items 4–6 remain binding and are restated as SETTLEIQ-REQ-001 in the master specification. This document does not revoke them.

### 5.4 Buyer and willingness-to-pay evidence

**No buyer validation exists.** No prospective customer, employer-as-customer, or buyer of any kind has been contacted, interviewed, surveyed, or otherwise engaged. **No willingness-to-pay evidence exists.** No pricing study, no experiment, no quote, and no indication of what anyone would pay for SettleIQ or for anything like it has been obtained. Any statement in any SettleIQ artifact that implies otherwise is a defect under SETTLEIQ-REQ-001(3).

---

## 6. Register Discipline

* Every claim SettleIQ relies on must appear in `docs/research/02_verification_log.md` with a primary source, or be marked **NOT VERIFIED**.
* A claim is not upgraded in class or in status by repetition, by restatement in a subordinate document, or by the passage of time.
* Intent and implementation are never presented in the same register (SETTLEIQ-REQ-004). This register contains evidence about other parties' published material; it contains no evidence about SettleIQ's own execution.
* Research remains evidence. It is never promoted to a requirement, and it never licenses a claim.

---

## 7. Explicit Statement of Status

The research recorded here is complete and closed as to frame. It is preserved as evidence with its failures of verification intact, including one unverified quote, one unverified limitation sentence, one unchecked claim, three corrected conclusions, and seven tasks the log itself left open. Nothing in this register describes implemented SettleIQ software.
