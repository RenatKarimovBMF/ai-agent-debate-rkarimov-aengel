# ADR-010: Config version key validated at load

**Status:** Accepted
**Date:** 2026-05-27

## Context

Submission Guidelines V3 §8.1 require an explicit version stamp in
both code and configuration, plus a runtime check that the two are in
sync.

## Decision

`debate._version.__version__ = "1.00"` is the single source of truth.
`pyproject.toml`, `setup.json`, `demo_setup.json`, `rate_limits.json`,
and `demo_rate_limits.json` each carry a top-level `"version"` key
with the same value. `debate.config.loader._validate_config_version`
runs for both files inside `load_config`:

- Missing `"version"` key — hard `ValueError`.
- Mismatch against `EXPECTED_CONFIG_VERSION` — `logging.WARNING` and
  the load continues. Users get a clear message, but old configs
  still boot.

`--version` and the `App version` line in `--dry-run` make the active
version observable from the CLI.

## Consequences

**Positive:**

- Submitted artifacts can be diffed by version at a glance.
- A forgotten config bump is caught at startup, not in production.
- The version is propagated to logs and the CLI so a screenshot of
  any run shows it.

**Negative:**

- Every config file change must bump four `version` keys in lock-step
  if the schema breaks. Acceptable cost; the CHANGELOG also records
  it.

## Alternatives considered

- **Version in `pyproject.toml` only** — rejected; the brief asks for
  the version in the config files too.
- **Bake the version into the file name** (`setup.v1.json`) —
  rejected; would force every consumer to update path strings on every
  bump, which is too much churn.
- **Strict equality (hard-fail on mismatch)** — rejected for now;
  warning is friendlier during the per-session iteration that still
  happens before submission. We may tighten this to a hard fail in a
  later release.
