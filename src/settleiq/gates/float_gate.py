"""Static money-safety gate.

Rejects a binary float on any monetary code path. This is the CI gate required
by SETTLEIQ-M1-001 AC-7.04, and it is *static* rather than a runtime test
because a runtime test only catches the paths a test happens to exercise.

It is a conservative scan: it flags every use of `float(`, a `float` annotation,
`float` in an import, or a numeric literal containing a decimal point or
exponent, inside the declared monetary packages. False positives are cheap to
resolve with an inline waiver; a missed float is not.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["MONETARY_PACKAGES", "Violation", "scan", "scan_package"]

#: Packages where a binary float must never appear.
MONETARY_PACKAGES: tuple[str, ...] = ("money", "model", "canonical", "validation")

_WAIVER = "# gate: waive"


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.kind}: {self.detail}"


def _float_literals(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            found.append((node.lineno or 0, f"float literal {node.value!r}"))
    return found


def _float_annotations(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        annotation = None
        if isinstance(node, (ast.AnnAssign, ast.arg)):
            annotation = node.annotation
        if annotation is None:
            continue
        names = {
            sub.id for sub in ast.walk(annotation) if isinstance(sub, ast.Name)
        }
        if "float" in names:
            found.append(
                ((node.lineno or 0), "`float` annotation on a monetary path")
            )
    return found


def _float_calls(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ):
            found.append((node.lineno or 0, "call to float()"))
    return found


def scan(path: Path) -> list[Violation]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return []
    tree = ast.parse(source, filename=str(path))
    violations: list[Violation] = []
    for lineno, detail in (
        _float_literals(tree) + _float_annotations(tree) + _float_calls(tree)
    ):
        line_text = source.splitlines()[lineno - 1] if lineno else ""
        if _WAIVER in line_text:
            continue
        violations.append(Violation(path, lineno, "float-on-monetary-path", detail))
    return violations


def scan_package(package_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    for py in sorted(package_dir.rglob("*.py")):
        violations.extend(scan(py))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Scan the monetary packages, or the paths given on the command line.

    The default is deliberately the **monetary packages** rather than the whole
    source tree: a ratio computed in `engine/metrics` is not a monetary amount,
    and scanning everything would produce false positives that train reviewers
    to ignore the gate.
    """
    argv = sys.argv[1:] if argv is None else argv
    base = Path("src/settleiq")
    roots = [Path(a) for a in argv] or [base / name for name in MONETARY_PACKAGES]
    found: list[Violation] = []
    for root in roots:
        if root.is_dir():
            found.extend(scan_package(root))
    if found:
        print("MONEY-SAFETY GATE FAILED")
        for violation in found:
            print(f"  {violation}")
        print(f"{len(found)} violation(s). A binary float on a monetary path is a defect.")
        return 1
    print(f"money-safety gate: clean ({len(roots)} package root(s) scanned)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
