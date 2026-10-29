"""Canonical serialization.

Every collection that reaches a digest is sorted by a declared key before
serialization. No wall clock, PID, sequence counter, random value, or memory
address may appear in a preimage (SETTLEIQ-M1-001 AC-4.04).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

__all__ = ["canonical_bytes", "canonical_scalar", "digest", "sort_key"]


def sort_key(value: Any) -> str:
    """A total, stable ordering key for any canonical value.

    Decimal is rendered in fixed-point notation so that "10.0" and "10.00"
    sort adjacently rather than lexically apart.
    """
    t = type(value)
    if t is str:
        return f"s:{value}"
    if t is Decimal:
        return f"d:{format(value, 'f')}"
    if t is bool:
        return f"b:{value}"
    if t is int:
        return f"i:{value}"
    return f"o:{value!r}"


def canonical_scalar(value: Any) -> str:
    """Render one scalar canonically.

    Floats are rejected: a float reaching a digest would make the preimage
    platform-dependent and irreproducible.
    """
    t = type(value)
    if t is str:
        return value
    if t is Decimal:
        return format(value, "f")
    if t is bool:
        return "true" if value else "false"
    if t is int:
        return str(value)
    if value is None:
        return ""
    if isinstance(value, float):
        raise TypeError("binary floats must not enter a canonical serialization")
    return str(value)


def _render(value: Any) -> str:
    t = type(value)
    if t is dict:
        keys = value.keys()
        # Fast path: when all dictionary keys are strings (standard in canonical records),
        # lexical string sorting is identical to sort_key which prefixes 's:' to all strings.
        if all(type(k) is str for k in keys):
            return "{" + ";".join(f"{k}={_render(value[k])}" for k in sorted(keys)) + "}"
        parts = [f"{canonical_scalar(k)}={_render(value[k])}" for k in sorted(keys, key=sort_key)]
        return "{" + ";".join(parts) + "}"
    if t in (list, tuple):
        ordered = sorted(value, key=sort_key)
        return "[" + ",".join(_render(item) for item in ordered) + "]"
    return canonical_scalar(value)


def canonical_bytes(value: Any) -> bytes:
    """Serialize to canonical bytes, UTF-8, no trailing newline."""
    return _render(value).encode("utf-8")


def digest(value: Any) -> str:
    """SHA-256 over the canonical serialization, lowercase hex."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sorted_by(items: Iterable[Any], key: Any) -> list[Any]:
    """Sort with an explicit, declared key. Never rely on insertion order."""
    return sorted(items, key=key)
