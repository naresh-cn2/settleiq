"""Source adapters.

**No adapter is implemented at M1.** The interface is frozen first
(SETTLEIQ-M1-001 AC-6.01), and a test asserts that this package contains no
adapter implementation. M2 writes the first adapter against it.
"""

from __future__ import annotations

from .interface import (
    ADAPTER_INTERFACE_VERSION,
    NormalizedBatch,
    SourceAdapter,
    SourceAdapterError,
    money,
    rejects_float_in_payload,
    to_decimal,
)

__all__ = [
    "ADAPTER_INTERFACE_VERSION",
    "NormalizedBatch",
    "SourceAdapter",
    "SourceAdapterError",
    "money",
    "rejects_float_in_payload",
    "to_decimal",
]
