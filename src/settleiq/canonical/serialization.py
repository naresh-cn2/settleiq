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
    if isinstance(value, Decimal):
        return f"d:{format(value, 'f')}"
    if isinstance(value, bool):
        return f"b:{value}"
    if isinstance(value, int):
        return f"i:{value}"
    if isinstance(value, str):
        return f"s:{value}"
    return f"o:{value!r}"


def canonical_scalar(value: Any) -> str:
    """Render one scalar canonically.

    Floats are rejected: a float reaching a digest would make the preimage
    platform-dependent and irreproducible.
    """
    if isinstance(value, float):
        raise TypeError("binary floats must not enter a canonical serialization")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _render(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key in sorted(value, key=sort_key):
            parts.append(f"{canonical_scalar(key)}={_render(value[key])}")
        return "{" + ";".join(parts) + "}"
    if isinstance(value, (list, tuple)):
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
