"""Deterministic synthetic dataset generator.

Produces a Stripe-shaped record set with **injected defects whose expected
discrepancy classification is recorded in the manifest**. A generator that
cannot state what it injected cannot support an asserted expectation.

Records are linked through a settlement-batch reference, which is the same
linkage a processor provides: a batch groups the charges, fees, refunds, and
adjustments that a payout settles.

Every record is `SYNTHETIC`. Nothing here connects to a live account.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Final

from settleiq.canonical.serialization import digest
from settleiq.model.provenance import DataProvenance

__all__ = [
    "GENERATOR_ID",
    "GENERATOR_VERSION",
    "SEED",
    "DefectSpec",
    "GeneratedDataset",
    "generate",
]

GENERATOR_ID: Final[str] = "settleiq.fixtures.generator"
GENERATOR_VERSION: Final[str] = "1.0.0"
SEED: Final[int] = 20261028


@dataclass(frozen=True)
class DefectSpec:
    """A defect injected into the dataset, with its expected classification."""

    defect_id: str
    kind: str
    expected_discrepancy: str
    detail: str


@dataclass
class GeneratedDataset:
    """A generated dataset plus its manifest."""

    records: list[tuple[str, dict[str, object]]]
    defects: list[DefectSpec]
    manifest: dict[str, object] = field(default_factory=dict)

    @property
    def input_digest(self) -> str:
        return self.manifest["input_digest"]

    def to_json(self) -> str:
        return json.dumps({"manifest": self.manifest, "records": self.records}, indent=2)


def _charge(idx: int, amount: str, batch: str, reference: str = "") -> dict[str, object]:
    return {
        "id": f"ch_{idx}",
        "amount": amount,
        "currency": "USD",
        "created": "2026-10-01",
        "batch": batch,
        "reference": reference or f"ref-{batch}",
    }


def _fee(idx: int, amount: str, batch: str, fee_type: str = "processing") -> dict[str, object]:
    return {
        "id": f"fee_{idx}",
        "amount": amount,
        "currency": "USD",
        "type": fee_type,
        "created": "2026-10-01",
        "batch": batch,
    }


def _refund(idx: int, amount: str, batch: str, charge: str) -> dict[str, object]:
    return {
        "id": f"re_{idx}",
        "amount": amount,
        "currency": "USD",
        "charge": charge,
        "created": "2026-10-01",
        "batch": batch,
    }


def _payout(idx: int, amount: str, arrival: str, batch: str) -> dict[str, object]:
    return {
        "id": f"po_{idx}",
        "amount": amount,
        "currency": "USD",
        "arrival_date": arrival,
        "batch": batch,
    }


def _deposit(idx: int, amount: str, posted: str, batch: str) -> dict[str, object]:
    return {
        "id": f"bd_{idx}",
        "amount": amount,
        "currency": "USD",
        "posted": posted,
        "narration": f"STRIPE PAYOUT {batch}",
        "bank_account_last3": "123",
    }


def generate(*, clean: bool = False) -> GeneratedDataset:
    """Generate a deterministic dataset.

    When ``clean`` is False (the default) the dataset contains six injected
    defects, each with a recorded expected classification. Every value derives
    from a fixed seed, so the dataset is byte-identical on every run.
    """
    records: list[tuple[str, dict[str, object]]] = []
    defects: list[DefectSpec] = []

    # --- clean baseline: batch sb_1
    # gross 175.00 - processing 3.50 - cross_border 1.75 = net 169.75
    records += [
        ("charge", _charge(1, "100.00", "sb_1")),
        ("charge", _charge(2, "50.00", "sb_1")),
        ("charge", _charge(3, "25.00", "sb_1")),
        ("fee", _fee(1, "3.50", "sb_1", "processing")),
        ("fee", _fee(2, "1.75", "sb_1", "cross_border")),
        ("payout", _payout(1, "169.75", "2026-10-03", "sb_1")),
        ("deposit", _deposit(1, "169.75", "2026-10-04", "sb_1")),
    ]

    if clean:
        defects = []
    else:
        # DEFECT 1 — a charge on the processor side belonging to a batch with no
        # payout. The charge is real; the payout is absent.
        records.append(("charge", _charge(4, "40.00", "sb_orphan")))
        defects.append(
            DefectSpec(
                "D1", "PHANTOM", "PHANTOM_PROCESSOR",
                "charge ch_4 is in batch sb_orphan, which has no payout",
            )
        )

        # DEFECT 2 — a bank deposit whose reference matches no payout.
        records.append(("deposit", _deposit(2, "250.00", "2026-10-05", "UNKNOWN")))
        defects.append(
            DefectSpec(
                "D2", "LOST", "PHANTOM_BANK",
                "deposit bd_2 has a reference that matches no payout",
            )
        )

        # DEFECT 3 — the batch nets 80.00 but the bank received 78.50.
        records += [
            ("charge", _charge(5, "80.00", "sb_2")),
            ("payout", _payout(2, "80.00", "2026-10-06", "sb_2")),
            ("deposit", _deposit(3, "78.50", "2026-10-07", "sb_2")),
        ]
        defects.append(
            DefectSpec(
                "D3", "AMOUNT", "AMOUNT_BREAK",
                "payout po_2 nets 80.00 but deposit bd_3 posted 78.50",
            )
        )

        # DEFECT 4 — a fee deducted on the processor side that the batch
        # composition does not account for: the decomposition fails to close.
        records += [
            ("charge", _charge(6, "60.00", "sb_3")),
            ("fee", _fee(3, "4.00", "sb_3", "processing")),
            ("payout", _payout(3, "60.00", "2026-10-08", "sb_3")),
            ("deposit", _deposit(4, "60.00", "2026-10-09", "sb_3")),
        ]
        defects.append(
            DefectSpec(
                "D4", "FEE", "NET_GROSS_BREAK",
                "batch sb_3 grosses 60.00 with a 4.00 fee but the payout nets "
                "60.00; the composition does not close",
            )
        )

        # DEFECT 5 — the batch closes correctly but the bank posted it 12 days
        # later than the declared settlement window permits.
        records += [
            ("charge", _charge(9, "169.75", "sbLATE")),
            ("payout", _payout(4, "169.75", "2026-10-08", "sbLATE")),
            ("deposit", _deposit(5, "169.75", "2026-10-20", "sbLATE")),
        ]
        defects.append(
            DefectSpec(
                "D5", "TIMING", "TIMING_BREAK",
                "payout po_4 paid 2026-10-08 but deposit bd_5 posted 2026-10-20",
            )
        )

        # DEFECT 6 — two payouts carrying the same settlement reference: an
        # unresolvable ambiguity, not a tie-break.
        records += [
            ("charge", _charge(7, "13.37", "sb_amb")),
            ("payout", _payout(5, "13.37", "2026-10-10", "sb_amb")),
            ("payout", _payout(6, "13.37", "2026-10-10", "sb_amb")),
            ("deposit", _deposit(6, "13.37", "2026-10-11", "sb_amb")),
        ]
        defects.append(
            DefectSpec(
                "D6", "AMBIGUOUS", "AMBIGUOUS_MATCH",
                "two payouts share reference sb_amb, so deposit bd_6 has two "
                "equally valid candidates; the engine must not choose",
            )
        )

        # DEFECT 7 — a record kind the model does not model. The engine must
        # classify it UNKNOWN rather than force it into the nearest type, and
        # the UNKNOWN outcome must be countable.
        records.append(
            (
                "dispute",
                {
                    "id": "dp_1",
                    "amount": "7.00",
                    "currency": "USD",
                    "created": "2026-10-02",
                    "batch": "sb_1",
                    "reason": "cardholder_dispute",
                },
            )
        )
        defects.append(
            DefectSpec(
                "D7", "UNMODELLED", "UNKNOWN",
                "record dp_1 is a dispute, a kind the model does not model",
            )
        )

    canonical_records = [{"kind": kind, "record": record} for kind, record in records]
    manifest = {
        "generator_id": GENERATOR_ID,
        "generator_version": GENERATOR_VERSION,
        "seed": SEED,
        "provenance": DataProvenance.SYNTHETIC.value,
        "record_count": len(records),
        "defects": [
            {
                "defect_id": d.defect_id,
                "kind": d.kind,
                "expected_discrepancy": d.expected_discrepancy,
                "detail": d.detail,
            }
            for d in defects
        ],
    }
    manifest["input_digest"] = digest({"manifest": manifest, "records": canonical_records})
    return GeneratedDataset(records=records, defects=defects, manifest=manifest)
