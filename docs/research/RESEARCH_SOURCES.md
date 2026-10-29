# SettleIQ — Research Sources & Primary References

**Document ID:** SETTLEIQ-RES-006  
**Status:** ACTIVE  

---

## 1. Commercial Product Sources

1. **BlackLine Account Reconciliations & Transaction Matching:**
   - URL: `https://www.blackline.com/products/financial-close/account-reconciliations/`
   - Key Reference: Transaction matching rule precedence, segregation of duties, exception workflow.
2. **Modern Treasury Ledger & Reconciliation Guide:**
   - URL: `https://www.moderntreasury.com/learn/financial-ledger-and-reconciliation`
   - Key Reference: Double-entry money movement, bank statement ingestion, immutable records.
3. **Numeric Automated Reconciliations:**
   - URL: `https://www.numeric.io/blog/reconciliation-automation`
   - Key Reference: Explaining matches, audit trails for SOX 302/404, human override tracking.
4. **Oracle NetSuite Pay Settlement & Fee Reconciliation:**
   - URL: `https://docs.oracle.com/en/cloud/saas/netsuite/`
   - Key Reference: Separate treatment of fee reconciliation vs. gross cash movements.

---

## 2. Regulatory & Standards References

1. **Sarbanes-Oxley Act (SOX) Section 404:** Management assessment of internal controls over financial reporting, requiring tamper-resistant verification of financial adjustments.
2. **ISO 4217 Currency Codes:** Decimal exponent specification defining minor unit precision across world currencies (0 digits for JPY/KRW, 2 digits for USD/EUR/GBP, 3 digits for BHD/KWD).
3. **IEEE 754-2008 Floating-Point Arithmetic Standard:** Standard outlining binary floating-point representation limits, explaining the mathematical necessity of `decimal.Decimal` in financial systems.

