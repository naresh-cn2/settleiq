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
python -m pytest tests/        # 102 tests
```

`run` loads a deterministic synthetic dataset with seven **injected defects
whose expected classifications are recorded before the run**, reconciles it, and
asserts every one is produced. It exits `0` on success and `1` if any expectation
is not met, so it is usable as a CI gate.

Add `--json` for the machine-readable report, or `--database path.sqlite3` to
persist runs.

## Environment status — read this

Two constraints in the current build environment are recorded rather than hidden:

| Constraint | Effect | Consequence |
|---|---|---|
| **PostgreSQL and Docker are unavailable** | Q3 (Postgres) cannot be provisioned here | Persistence is implemented against **SQLite** behind the `Persistence` interface. Amounts are stored as **exact decimal text**, which is stricter than a `numeric` column: no scale rounding is possible at all. Postgres is a mechanical swap when available. |
| **Hypothesis's native extension is blocked** by an Application Control policy | Property-based testing via Hypothesis fails to import | Replaced with a seeded pure-Python generator. The seed is recorded in `settleiq/testing/generators.py`. |

## What is verified, and what is not

**Implemented and tested:** exact monetary arithmetic and the currency-exponent
policy; the canonical data model; deterministic run identity; fail-closed
ingestion validation; the frozen `SourceAdapter` interface; payout decomposition
with an explicit residual; the deterministic matching engine including
ambiguity, rule conflict, and amount/timing checks; the closed discrepancy
taxonomy with `UNKNOWN`; metrics with a stated methodology; persistence with
transaction integrity.

**Not implemented:** the hash-chained tamper-evident audit journal (the
specification's M5); the REST API (M6); the web dashboard (M7); the performance
benchmark (M8, and conditional); Docker deployment (M9). No code exists for these
and none is claimed.

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
