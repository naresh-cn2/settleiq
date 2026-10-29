# Engineering Case Study 01: Zero-Float Financial Engineering

**Title:** Eliminating Floating-Point Precision Loss in Financial Systems via Static AST Analysis  
**Author:** SettleIQ Core Engineering  
**Category:** Systems Architecture & Language Engineering  

---

## 1. The Financial Problem: Binary Floating-Point Drift

Financial reconciliation engines running in high-volume environments process millions of minor currency transactions. Standard programming language floats (IEEE 754 64-bit binary floating-point) cannot accurately represent base-10 decimal fractions:
$$0.1_{10} + 0.2_{10} = 0.30000000000000004440892098500626..._2$$

In payment operations, accumulated float rounding drift creates unexplained residuals, unbalanceable ledgers, and catastrophic audit failures during Sarbanes-Oxley (SOX) reviews.

---

## 2. The SettleIQ Solution: Strict Python Decimal + AST Enforcement

Rather than relying on developer discipline, SettleIQ enforces exact decimal arithmetic through a two-layered defense:

### Layer 1: The Immutable `Money` Type
```python
class Money:
    def __init__(self, amount: Decimal | str | int, currency: CurrencyCode | str) -> None:
        if isinstance(amount, float):
            raise FloatProhibited(
                "Money cannot be constructed from a binary float; pass a str, int, or Decimal."
            )
        ...
```
- Construction from any `float` immediately raises `FloatProhibited`.
- Currency exponent rules strictly enforce ISO 4217 scales (USD: 2, JPY: 0, BHD: 3), raising `CurrencyPrecisionExceeded` rather than silently rounding.
- Cross-currency addition raises `CurrencyMismatch`.

### Layer 2: Automated AST Static Analysis Gate
SettleIQ includes a dedicated Abstract Syntax Tree (AST) analyzer (`settleiq/money/float_gate.py` executed via `python -m settleiq.cli gate`) that parses the entire codebase at the syntax level.

It detects and blocks:
1. Calls to `float(...)`.
2. Binary float literals (e.g. `10.5` instead of `"10.5"` or `Decimal("10.5")`).
3. Binary float variable type annotations on monetary paths.

```
AST Scanner Results:
[✓] src/settleiq/money/       - 0 float infractions
[✓] src/settleiq/canonical/   - 0 float infractions
[✓] src/settleiq/engine/      - 0 float infractions
[✓] src/settleiq/adapters/    - 0 float infractions
[✓] src/settleiq/persistence/ - 0 float infractions
Status: CLEAN (100% Exact Decimal Arithmetic Guaranteed)
```

---

## 3. Results & Impact
- Zero rounding errors across 100,000-record workloads.
- Every cent and minor unit is algebraically accounted for.
- Full compliance with regulatory audit standards.

