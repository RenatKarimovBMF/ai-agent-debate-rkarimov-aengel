# ADR-006: 150-line cap per source file

**Status:** Accepted
**Date:** 2026-05-27

## Context

Guidelines V3 §5.2 sets a hard limit of 150 lines per source file.
The PDF makes it clear that exceeding the limit means splitting — not
compressing the code into a denser style. Earlier in the project we
read the rule as "non-blank, non-comment lines"; the strict reading
is raw lines, including blanks and comments.

Before Stage 13 five files exceeded 150 raw lines:
`debate/transport.py` (172), `agents/parent_agent.py` (181),
`legacy/session_loop.py` (164), `gui/app.py` (162),
`gui/panels.py` (160).

## Decision

Treat 150 as a *hard* limit enforced by `scripts/check_line_cap.py`,
which counts raw lines and exits non-zero on any offender. The script
runs under the local quality gate (`make cap` / `make check`) and
inside the pre-commit hook (`.pre-commit-config.yaml`).

When a file approaches the cap, split it using one of:

- Extract helper functions to a sibling module (e.g.
  `verdict_builder.py`, `judge_prompts.py`).
- Convert the file into a package with topical sub-modules (e.g.
  `transport/` with `base.py`, `file_queue.py`, `fifo.py`, `factory.py`).
- Split read-vs-write halves into two files.
- Hoist long prompt strings into a dedicated `*_prompts.py` module.

## Consequences

**Positive:**

- Forces real separation of concerns. Splitting `parent_agent.py`
  separated the judge's *behaviour* (the agent class) from its
  *content* (the prompts) and the *post-processing* (the verdict
  builder); each piece is individually testable.
- Catches IDE auto-formatting from silently growing a file past the
  cap, because the pre-commit hook fails fast.

**Negative:**

- More files for very small helpers. Acceptable cost for keeping the
  cap inviolable.

## Alternatives considered

- **150 lines excluding blanks and comments** — used in our first
  read of the rule; abandoned in Stage 13 because the PDF is
  explicit about raw lines.
- **Higher cap (200, 250)** — not allowed by the guideline.
- **Configuring a Ruff rule for `too-many-lines`** — Ruff does not
  ship that rule; the standalone script is cheaper than another
  linter.
