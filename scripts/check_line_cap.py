"""Enforce the Guidelines V3 §5.2 file-size cap.

Usage:
    uv run python scripts/check_line_cap.py [LIMIT]

Default LIMIT is 150 raw lines (including blanks and comments). Exits
non-zero and prints offenders if any .py file under `src/`, `tests/`,
or `scripts/` is over the cap. Designed to be cheap enough to run
from a pre-commit hook on every staged commit and from CI on every
push.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOTS = ("src", "tests", "scripts")


def count_lines(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def collect_offenders(limit: int) -> list[tuple[Path, int]]:
    offenders: list[tuple[Path, int]] = []
    for root in ROOTS:
        base = Path(root)
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            n = count_lines(path)
            if n > limit:
                offenders.append((path, n))
    return offenders


def main(argv: list[str]) -> int:
    limit = int(argv[1]) if len(argv) > 1 else 150
    offenders = collect_offenders(limit)
    scope = "/".join(ROOTS)

    if not offenders:
        print(f"check_line_cap: OK - every .py file under {scope}/ is <= {limit} raw lines.")
        return 0

    print(f"check_line_cap: FAIL - {len(offenders)} file(s) over {limit} lines:", file=sys.stderr)
    for path, n in sorted(offenders, key=lambda x: -x[1]):
        print(f"  {n:4d}  {path.as_posix()}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
