# SettleIQ — Open-source financial reconciliation engine

Show HN: SettleIQ — Open-source payment reconciliation engine with exact decimal arithmetic, discrepancy detection, and hash-chained audit journal.

We built SettleIQ because reconciling payments shouldn't require expensive enterprise software or manual spreadsheets.

**What it does:**
- Exact decimal arithmetic (no float errors in financial calculations)
- Constituent-level payout decomposition (charges → fees → refunds → net payout)
- 7 types of discrepancy detection (NET_GROSS_BREAK, AMOUNT_BREAK, TIMING_BREAK, PHANTOM_PROCESSOR, PHANTOM_BANK, AMBIGUOUS_MATCH, UNKNOWN)
- Visual transaction traces — see the complete money journey
- Evidence-backed investigation hypotheses with confidence scores
- Hash-chained audit journal (SHA-256, tamper-evident)
- JSON and CSV export
- Full REST API for developers

**Try it:** https://settleiq-zeta.vercel.app (click "Explore Public Demo" — no signup required)

**GitHub:** https://github.com/naresh-cn2/settleiq

**Pricing:** Free tier available. Paid plans from $49/month.

**Tech stack:** FastAPI, React 18, TypeScript, SQLite/PostgreSQL, deterministic HMAC-SHA256 demo tokens.

We're launching publicly and want feedback:
- What reconciliation problems do you face?
- Would you use a tool like this?
- What features are missing?

Open an issue on GitHub or comment here.

#settleiq #reconciliation #fintech #opensource #saas #showhn