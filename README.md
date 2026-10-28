# SettleIQ

A payment settlement reconciliation and discrepancy investigation engine, built
as a **demonstrated engineering artifact for employment evidence**.

SettleIQ is an independent project. It is not governed by any other repository,
and it makes no claim about competitors, no market-gap claim, and no
commercial-viability claim. See `docs/specifications/SETTLEIQ-MASTER-SPEC.md`.

## What it does

Given a set of payment records — charges, fees, refunds, adjustments, payouts and
bank deposits — SettleIQ:

1. validates them, quarantining malformed records with a typed reason rather
   than discarding them;
2. decomposes each payout into its constituents and verifies the composition
   closes exactly;
3. matches at **constituent level**, never by comparing payout totals;
4. classifies what does not resolve into a **named** discrepancy type, never a
   generic "mismatch";
5. records evidence for every decision;
6. reports its auto-match rate with an explicit, code-defined methodology.

Money is `decimal.Decimal` everywhere. A binary float on a monetary path is a
defect, and a static gate enforces it.

## Reproduce this in one command

```bash
pip install -e .
python -m settleiq.cli run     # the full demonstration
python -m settleiq.cli gate    # the money-safety static gate
python -m pytest tests/        # 126 tests across unit, property, and integration
```

`run` loads a deterministic synthetic dataset with seven **injected defects
whose expected classifications are recorded before the run**, reconciles it, and
asserts every one is produced. It exits `0` on success and `1` if any expectation
is not met, so it is usable as a CI gate.

Add `--json` for the machine-readable report, or `--database path.sqlite3` to
persist runs.

To run the web dashboard and REST API:
```bash
uvicorn settleiq.api.app:app --reload --port 8000
```
Open `http://localhost:8000/` in a browser to view the interactive dashboard.

## Environment status — read this

Two constraints in the current build environment are recorded rather than hidden:

| Constraint | Effect | Consequence |
|---|---|---|
| **PostgreSQL and Docker are unavailable** | Q3 (Postgres) cannot be provisioned here | Persistence is implemented against **SQLite** behind the `Persistence` interface. Amounts are stored as **exact decimal text**, which is stricter than a `numeric` column: no scale rounding is possible at all. Postgres is a mechanical swap when available. |
| **Hypothesis's native extension is blocked** by an Application Control policy | Property-based testing via Hypothesis fails to import | Replaced with a seeded pure-Python generator. The seed is recorded in `settleiq/testing/generators.py`. |

## What is verified, and what is not

**Implemented and verified:**
* Exact monetary arithmetic and currency-exponent policy (`M1`).
* Canonical data model and deterministic run identity (`M1`).
* Fail-closed ingestion validation with typed quarantine reasons (`M1`).
* Frozen `SourceAdapter` interface (`M2`).
* Payout decomposition with explicit residual calculation (`M3`).
* Deterministic matching engine and closed discrepancy taxonomy (`M4`).
* Append-only hash-chained audit journal with verified tamper detection (`M5`).
* SQLite persistence with transactional atomicity across database and journal (`M5`).
* REST API with idempotent run execution, metrics with published methodology, and genuine discrepancy resolution with audit event logging (`M6`).
* Five-view React web dashboard compiled and delivered by FastAPI (`M7`).
* 126 automated tests passing across unit, property, and integration suites.

**Outstanding / remaining work:**
* PostgreSQL migration and dialect handling (Phase 2).
* Concrete Stripe source adapter implementation (Phase 5).
* Docker containerized deployment (`M9`).
* Large-scale performance validation benchmark (`M8`).

## Documentation

| Document | Purpose |
|---|---|
| `docs/specifications/SETTLEIQ-MASTER-SPEC.md` | Governing specification |
| `docs/specifications/16_DECISION_REGISTER_AND_RESOLUTIONS.md` | Decision baseline and resolution of every open engineering question |
| `docs/specifications/13_ROADMAP_AND_ACCEPTANCE.md` | Milestones and release gates |
| `docs/specifications/15_RISKS_AND_NON_GOALS.md` | Risk register and explicit non-goals |
| `docs/README.md` | Full documentation index |

## Safety

SettleIQ uses synthetic data only. It does not connect to live financial
accounts, hold credentials, or move money. Real data would require an explicit
authorization that has not been granted.
