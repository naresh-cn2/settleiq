"""Executable quality gates.

A gate that is documented but not run is not a gate. Each module here is invoked
from CI and is also exercised by the test suite, so a gate that silently stops
working fails the build.
"""

from __future__ import annotations

from .float_gate import MONETARY_PACKAGES, Violation, main, scan, scan_package

__all__ = ["MONETARY_PACKAGES", "Violation", "main", "scan", "scan_package"]
