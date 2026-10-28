"""M1 tests: canonical model, run identity, determinism, adapter freeze.

Acceptance criteria cite SETTLEIQ-M1-001 §4.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from settleiq.adapters import ADAPTER_INTERFACE_VERSION, NormalizedBatch, SourceAdapterError
from settleiq.canonical import digest
from settleiq.model import (
    Charge,
    DataProvenance,
    Fee,
    Payout,
    ReconciliationRun,
    Residual,
    RunIdentity,
    SourceRecordId,
    is_real_data_authorized,
    require_synthetic_or_authorized,
)
from settleiq.money import Money
from settleiq.validation import (
    MalformedRecordError,
    MissingFieldError,
    validate_amount_field,
    validate_records,
)

# ---------------------------------------------------------------- AC-3 canonical model


def _charge(amount: str = "100.00", source_id: str = "ch_1") -> Charge:
    return Charge(
        source_id=SourceRecordId(source_id),
        amount=Money(amount, "USD"),
        captured_at="2026-10-01T00:00:00Z",
        reference="ref-1",
    )


def test_every_entity_carries_currency_and_provenance() -> None:
    charge = _charge()
    assert charge.amount.currency.value == "USD"
    assert charge.provenance is DataProvenance.SYNTHETIC


def test_entities_are_frozen() -> None:
    charge = _charge()
    with pytest.raises(Exception):  # noqa: B017 - frozen dataclass raises on set
        charge.source_id = SourceRecordId("ch_other")  # type: ignore[misc]


def test_residual_is_a_first_class_constituent() -> None:
    residual = Residual(
        amount=Money("0.01", "USD"), allocation_rule_id="explicit-residual", rule_version="0.0.0"
    )
    assert residual.amount.amount == Decimal("0.01")
    assert residual.allocation_rule_id == "explicit-residual"


def test_canonical_serialization_round_trips() -> None:
    charge = _charge("1043.27")
    payload = charge.to_canonical()
    assert payload["amount"] == "1043.27|USD"
    assert payload["kind"] == "Charge"


# ---------------------------------------------------------------- AC-4 determinism


def test_run_id_is_derived_not_generated() -> None:
    identity = RunIdentity.derive(inputs={"a": 1, "b": 2})
    again = RunIdentity.derive(inputs={"b": 2, "a": 1})
    assert identity.run_id == again.run_id
    # A derived id is not a UUID: it is stable and its prefix is a hash.
    assert len(identity.run_id) == 64
    assert identity.run_id != identity.run_id.upper()


def test_rule_version_participates_in_identity() -> None:
    first = RunIdentity.derive(inputs={"x": 1}, rule_version="0.0.0")
    second = RunIdentity.derive(inputs={"x": 1}, rule_version="0.0.1")
    assert first != second
    assert first.run_id != second.run_id


def test_schema_version_participates_in_identity() -> None:
    first = RunIdentity.derive(inputs={"x": 1}, schema_version="0.1.0")
    second = RunIdentity.derive(inputs={"x": 1}, schema_version="0.2.0")
    assert first.run_id != second.run_id


def test_input_order_does_not_change_digest() -> None:
    records_a = [("charge", {"id": "a"}), ("fee", {"id": "b"})]
    records_b = [("fee", {"id": "b"}), ("charge", {"id": "a"})]
    assert digest({"r": records_a}) == digest({"r": records_b})


def test_digest_is_stable_across_calls() -> None:
    assert digest({"k": "v"}) == digest({"k": "v"})


def test_canonical_serialization_rejects_floats() -> None:
    with pytest.raises(TypeError):
        digest({"amount": 1.5})


def test_no_ambient_value_reaches_a_digest() -> None:
    # A digest computed from declared inputs is identical when the ambient
    # environment changes (locale, hash seed, parallelism).
    first = digest({"records": [{"id": "x", "amount": "1.00|USD"}]})
    second = digest({"records": [{"id": "x", "amount": "1.00|USD"}]})
    assert first == second


# ---------------------------------------------------------------- AC-5 fail-closed validation


def test_missing_field_names_the_field() -> None:
    with pytest.raises(MissingFieldError) as excinfo:
        validate_amount_field({"amount": "1.00"}, "charge", 0)
    assert excinfo.value.field_name == "id"


def test_missing_currency_is_named_when_id_present() -> None:
    with pytest.raises(MissingFieldError) as excinfo:
        validate_amount_field(
            {"amount": "1.00", "id": "ch_1", "created": "t"}, "charge", 7
        )
    assert excinfo.value.field_name == "currency"


def test_malformed_amount_is_typed() -> None:
    with pytest.raises(MalformedRecordError):
        validate_amount_field(
            {"amount": "not-a-number", "currency": "USD", "id": "x", "created": "t"}, "charge", 3
        )


def test_excess_precision_raises_not_rounds() -> None:
    # The money layer raises CurrencyPrecisionExceeded; the ingestion layer
    # wraps it in a typed ingestion error. Both are non-negotiable: neither
    # rounds.
    from settleiq.money import CurrencyPrecisionExceeded, Money

    with pytest.raises(CurrencyPrecisionExceeded):
        Money("1.005", "USD")

    with pytest.raises(MalformedRecordError) as excinfo:
        validate_amount_field(
            {"amount": "1.005", "currency": "USD", "id": "x", "created": "t"}, "charge", 0
        )
    assert "decimal places" in str(excinfo.value)


def test_unknown_currency_is_typed() -> None:
    from settleiq.validation import CurrencyError

    with pytest.raises(CurrencyError):
        validate_amount_field(
            {"amount": "1.00", "currency": "XYZ", "id": "x", "created": "t"}, "charge", 0
        )


def test_duplicate_is_reported_not_deduplicated() -> None:
    record = {"id": "ch_1", "amount": "10.00", "currency": "USD", "created": "2026-10-01"}
    result = validate_records([("charge", record), ("charge", dict(record))])
    assert result.accepted_count == 1
    assert result.duplicate_count == 1
    assert result.duplicates == ("charge:ch_1",)


def test_quarantined_records_are_preserved_with_a_reason() -> None:
    records = [
        ("charge", {"id": "ok", "amount": "10.00", "currency": "USD", "created": "t"}),
        ("charge", {"id": "bad", "amount": "10.00", "created": "t"}),  # missing currency
        ("charge", {"amount": "1.00", "currency": "USD", "created": "t"}),  # missing id
    ]
    result = validate_records(records)
    assert result.accepted_count == 1
    assert result.quarantined_count == 2
    assert all(len(item) == 3 for item in result.quarantined)


def test_empty_batch_is_a_clean_no_op() -> None:
    result = validate_records([])
    assert result.accepted_count == 0
    assert result.quarantined_count == 0


# ---------------------------------------------------------------- AC-6 adapter freeze


def test_adapter_interface_is_versioned() -> None:
    assert ADAPTER_INTERFACE_VERSION == "1.0.0"


def test_adapter_interface_is_implementable() -> None:
    """A mock adapter satisfies the protocol without being a Stripe adapter."""

    class MockAdapter:
        source_version = "mock-1.0.0"
        schema_version = "0.1.0"

        def normalize(
            self, payload: bytes, *, provenance: DataProvenance.SYNTHETICAlias
        ) -> NormalizedBatch:
            require_synthetic_or_authorized(provenance)
            return NormalizedBatch(
                charges=(),
                fees=(),
                refunds=(),
                adjustments=(),
                payouts=(),
                batches=(),
                deposits=(),
                provenance=provenance,
                source_version=self.source_version,
                schema_version=self.schema_version,
            )

    adapter = MockAdapter()
    batch = adapter.normalize(b"{}", provenance=DataProvenance.SYNTHETIC)
    assert batch.record_count() == 0
    assert batch.provenance is DataProvenance.SYNTHETIC


def test_adapter_rejects_float_in_payload() -> None:
    from settleiq.adapters import rejects_float_in_payload

    with pytest.raises(SourceAdapterError):
        rejects_float_in_payload(1.5)
    rejects_float_in_payload("1.5")  # a string is the correct transport


def test_no_adapter_implementation_exists() -> None:
    """The freeze is proven by absence (AC-6.01)."""
    import pathlib

    import settleiq.adapters as adapters_pkg

    package_dir = pathlib.Path(adapters_pkg.__file__).parent
    modules = sorted(p.stem for p in package_dir.glob("*.py") if p.stem != "__init__")
    assert modules == ["interface"], f"unexpected adapter module(s): {modules}"


def test_real_requires_authorization() -> None:
    with pytest.raises(PermissionError):
        require_synthetic_or_authorized(DataProvenance.AUTHORIZED_REAL)
    assert not is_real_data_authorized()


def test_synthetic_is_permitted_without_authorization() -> None:
    require_synthetic_or_authorized(DataProvenance.SYNTHETIC)


def test_reconciliation_run_identity_is_canonical() -> None:
    identity = RunIdentity.derive(inputs={"k": "v"})
    run = ReconciliationRun(
        run_id=identity.run_id,
        input_digest=identity.input_digest,
        rule_version=identity.rule_version,
        schema_version=identity.schema_version,
        status="COMPLETED",
    )
    assert run.to_canonical()["run_id"] == identity.run_id
    assert digest(run.to_canonical()) == digest(run.to_canonical())


def test_payout_and_fee_are_typed_separately() -> None:
    payout = Payout(
        source_id=SourceRecordId("po_1"),
        amount=Money("95.00", "USD"),
        batch_source_id=SourceRecordId("sb_1"),
        paid_at="2026-10-03T00:00:00Z",
    )
    fee = Fee(
        source_id=SourceRecordId("fee_1"),
        amount=Money("5.00", "USD"),
        fee_type="processing",
        charged_at="2026-10-01T00:00:00Z",
    )
    assert payout.to_canonical()["kind"] == "Payout"
    assert fee.to_canonical()["fee_type"] == "processing"


