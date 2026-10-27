# SettleIQ — Documentation Index

SettleIQ is a payment settlement reconciliation and discrepancy investigation engine, built as a **demonstrated engineering artifact for employment evidence**. It is not positioned as a commercial product and makes no claim about competitors.

## Canonical documents

| Document | Status | Purpose |
|---|---|---|
| [`specifications/SETTLEIQ-MASTER-SPEC.md`](./specifications/SETTLEIQ-MASTER-SPEC.md) | PROPOSED — specification only, no implementation claimed | Governing frame, scope, requirements, milestones, risks |
| [`research/02_verification_log.md`](./research/02_verification_log.md) | Active — append-only discipline | Primary-source verification of every claim used in SettleIQ artifacts |

## Reading order

1. `02_verification_log.md` §1–2 first. It records which claims were checked against original sources, which were not, and one prior conclusion that its own source contradicted. Several findings in this repository are marked **not verified** and must not be cited as fact.
2. `SETTLEIQ-MASTER-SPEC.md` §1.2 explains why the frame is employment-artifact and not commercial.
3. `SETTLEIQ-MASTER-SPEC.md` §1.3 lists the binding non-claims.

## Standing rules for contributors and agents

* A claim is not a fact until it appears in the verification log with a primary source. Mark it `NOT VERIFIED` otherwise.
* Intent and implementation are never presented in the same register. A specification states intent; a test result states implementation.
* Digests and hashes are computed by the system and verified on read. A hand-written or patterned digest is treated as fabricated evidence.
* No monetary value is ever a binary float.
* Do not add a competitive-claim document, a pricing recommendation, or a market-gap analysis. Those frames were closed on 2026-10-27 (CHG-2026-10-27-003) and would violate `SETTLEIQ-REQ-001`.

## Current state

Research phase complete (all 8 tracks resolved and verified). Governing specification authored and awaiting OWNER ratification of five open questions recorded in §9. **No implementation exists. Nothing is built.**
