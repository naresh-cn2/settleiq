# Engineering Case Study 02: Cryptographic Audit Ledger

**Title:** Designing a Tamper-Evident Hash-Chained Audit Journal for Financial Compliance  
**Author:** SettleIQ Core Engineering  
**Category:** Cryptographic Integrity & Regulatory Compliance  

---

## 1. The Challenge: Silent Database Modifications

In standard relational database architectures, audit logs are stored as mutable rows with simple `created_at` timestamps. An insider with administrative access (or SQL injection vulnerability) can modify historical amounts, update resolution statuses, or delete embarrassing breaks without leaving a forensic trace.

For Sarbanes-Oxley (SOX 404) compliance and SOC 1 trust, financial institutions require verifiable proof that historical accounting decisions have not been altered.

---

## 2. The SettleIQ Solution: Merkle-Chained Event Ledger

SettleIQ implements an append-only, SHA-256 cryptographic hash-chained audit journal (`src/settleiq/journal/chain.py`):

```
+--------------------------------------------------------------------------------+
| Genesis Entry                                                                  |
| Prev Digest: 0000000000000000000000000000000000000000000000000000000000000000   |
| Payload: {"kind": "RunRecorded", "run_id": "run_01", ...}                      |
| Entry Digest: SHA256(Prev Digest || Canonical(Payload))                        |
+---------------------------------------+----------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------+
| Entry 2: Discrepancy Resolved                                                  |
| Prev Digest: [Digest of Genesis Entry]                                         |
| Payload: {"kind": "DiscrepancyResolved", "action": "WRITEOFF", ...}            |
| Entry Digest: SHA256(Prev Digest || Canonical(Payload))                        |
+---------------------------------------+----------------------------------------+
```

### Deterministic Preimage Serialization
A cryptographic digest is only reproducible if serialization is strictly deterministic:
- Dict keys are sorted alphabetically.
- Numbers are formatted in fixed-point decimal notation.
- **Ambient clock values are excluded from the digest preimage:** The timestamp is stored as inspectable payload content, but the hash preimage relies solely on deterministic business inputs.

---

## 3. Automated Tamper Suite Verification

The integrity of the chain is verified automatically (`tests/integration/test_journal_integrity.py`):
1. **Payload Modification (`PAYLOAD_MODIFIED`):** Modifying any field in an existing record alters its computed digest and invalidates all successor hashes.
2. **Digest Mutation (`DIGEST_MODIFIED`):** Tampering with a stored hash breaks the link with the next entry.
3. **Entry Deletion (`ENTRY_DELETED`):** Deleting a row from the middle causes a sequence mismatch and previous-digest break.
4. **Reordering (`ENTRY_REORDERED`):** Swapping two rows invalidates both hashes.

