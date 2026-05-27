# ADR-004: Configuration externalisation (JSON in `config/`)

**Status:** Accepted
**Date:** 2026-05-21

## Context

Earlier feedback flagged configuration portability. Hardcoding the
debate topic, side names, ping count, or rate limits inside Python
files would make the project non-reusable.

## Decision

All tunables live in `config/setup.json` (debate / LLM / IPC /
logging) and `config/rate_limits.json` (gatekeeper). The loader in
`debate/config/loader.py` is the single deserialiser; agents and the
orchestrator consume the resulting dataclasses. A demo pair
(`config/demo_setup.json` + `config/demo_rate_limits.json`) ships
side-by-side so the grader can run a small session cheaply.

## Consequences

**Positive:**

- Swapping the debate topic ("Beatles vs Rolling Stones") needs no
  code change.
- The CLI `--config` flag and the GUI both consume the same loader,
  so the dry-run/live paths cannot diverge.
- Per-environment overrides are a copy of a JSON file, not a code
  branch.

**Negative:**

- Two JSON files instead of one TOML; partially redundant for very
  small projects. Acceptable cost.

## Alternatives considered

- **Single TOML** — used in earlier stages; migrated to JSON in
  Stage 6 because JSON is friendlier to the Pydantic-based loader and
  is the format the brief showed in examples.
- **`.env` for everything** — rejected; secrets only belong in `.env`,
  structural tunables belong in committed config.
