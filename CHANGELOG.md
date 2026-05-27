# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Per submission guideline §8.1, the major version is bumped on breaking
restructures; minor versions bring backwards-compatible additions;
patches are bug fixes.

## [Unreleased]

### Added

- **GitHub project boilerplate.** `LICENSE` (MIT, Renat Karimov and
  Alon Engel, 2026); `.github/workflows/ci.yml` running ruff, the
  150-line cap, and `pytest tests/unit --cov` on Python 3.11 / 3.12 /
  3.13 on every push and PR to `main`; `.github/PULL_REQUEST_TEMPLATE.md`
  with the local-gate checklist; `.github/ISSUE_TEMPLATE/{bug_report,idea}.md`
  for structured triage; README badges (Python, tests, coverage, ruff,
  line cap, license).
- **Wider line-cap enforcement.** `scripts/check_line_cap.py` now walks
  `src/`, `tests/`, **and** `scripts/`, so the 150-line rule cannot be
  silently broken by a new test file or helper script.

### Changed

- **Quality-gate scope aligned across CI / Makefile / docs.** Ruff,
  the line-cap script, and `pytest --cov` now all walk
  `src/ tests/ scripts/` (Makefile `lint`/`format`, pre-commit, CI
  workflow). The CI step that ran only `tests/unit` now runs the full
  suite — the two integration tests under `tests/integration/` are
  config-scaffold tests and never touch Gemini or Anthropic.
- **Documentation counts refreshed.** README badge, `CONTRIBUTING.md`
  gate snippet, and PR-template checklist updated to the actual figures
  (187 tests; `fail_under = 100`).

## [1.00] — 2026-05-27

The submission baseline. Stage 10–13 work folded in: research-backed
judging, runtime side assignment, refute-with-citation rule, version
tracking, and the strict 150-line file cap.

### Added

- **Skills overhaul (Stage 10).** Parent now uses a research-backed
  stack of three skills: `debate-parent-judge` (philosophy + five
  judging principles drawn from WUDC, IDEA, NSDA, and Alfred Snider),
  `debate-host-protocol` (boxing-referee opening + side assignment),
  and `debate-judge-rubric` (Matter 30 / Manner 15 / Method 15 /
  Clash 25 / Burden 15 = 100). Debaters now share two side-agnostic
  playbook skills (`debate-argument-builder`, `debate-rebuttal-strategist`)
  with the per-side knowledge slimmed to lore-only skills
  (`debate-pro-godfather`, `debate-con-shawshank`). All skills are
  project-local under `.claude/skills/`. See `docs/PRD_judge_rubric.md`.
- **Runtime side assignment (Stage 11).** The Parent decides which
  agent defends which side at session start via
  `debate.orchestrator.host_protocol.decide_sides`, deterministic per
  `session_id` but varying across sessions. Sides travel to children
  in a new `ASSIGN` command (`orchestrator/commands.py`) before any
  turn request. The new `DebaterAgent` base centralises
  `apply_assignment` and the resolved-side fallback; `ProAgent` and
  `ConAgent` are thin role markers.
- **Refute-with-citation rule.** Debater system prompt, turn prompt,
  and judge rubric all enforce that contradicting a factual claim
  without a cited source is not a refutation and is penalised in the
  Clash score.
- **Personalised host opening.** `host_opening_address` helper
  delivers an individual briefing to each child at session start (per
  the boxing-referee protocol).
- **Version tracking (Stage 12).** `src/debate/_version.py` is the
  single source of truth; `pyproject.toml`, `config/setup.json`,
  `config/demo_setup.json`, `config/rate_limits.json` and
  `config/demo_rate_limits.json` all carry `"version": "1.00"`. The
  loader hard-fails on a missing version key and warns on mismatch.
  New `--version` CLI flag; `--dry-run` prints `App version`.
- **Prompt book (`docs/PROMPTS.md`).** Catalogues every LLM-facing
  prompt with purpose, audience, rationale per block, lessons
  learned, and an iteration history.
- **Strict 150-line cap audit (Stage 13).** Five files split:
  `transport.py` → `transport/` package; `parent_agent.py` →
  `parent_agent.py` + `verdict_builder.py` + `judge_prompts.py`;
  `legacy/session_loop.py` → `session_loop.py` + `ping_runner.py`;
  `gui/app.py` → `app.py` + `env_check.py`; `gui/panels.py` →
  `panels.py` + `form.py`. Largest file is now 138 raw lines.
- **Repo hygiene boilerplate.** `AUTHORS.md`, `CONTRIBUTING.md`,
  `CHANGELOG.md`, `Makefile`, `.pre-commit-config.yaml`,
  `scripts/check_line_cap.py`, `docs/KNOWN_LIMITATIONS.md`, and
  per-ADR files under `docs/adr/`.

### Changed

- `DebaterAgent.apply_assignment` propagates the host's assignment
  into the system prompt; debater prompts no longer assume hardcoded
  PRO/CON sides.
- Debater turn prompt restates the JSON schema every ping (the model
  drifts otherwise) and reinforces the refute-with-citation rule.
- Judge verdict prompt now requires `persuasion_notes` to reference
  at least one of the five judging principles.
- GUI labels and `--dry-run` output say "options on the table"
  instead of pretending the sides are fixed.
- Coverage harness updated to exclude only OS-/network-specific code
  (`legacy/ping_runner.py`, `transport/fifo.py`, real-API call sites
  in the SDK).

### Fixed

- The verdict builder reliably enforces the no-tie invariant: equal
  scores are bumped, and a stated winner whose score is not strictly
  the higher one gets corrected before serialisation.
- All Hebrew strings removed from the repository (English-only).

## [0.9] — 2026-05-21

Pre-submission baseline. Stage 1–9 of `docs/TODO.md`.

### Added

- PRD, PLAN, TODO, mechanism PRDs (orchestrator, gatekeeper, SDK).
- Multi-process orchestrator with parent/pro/con workers.
- LLM SDK layer with Gemini + Anthropic + Claude CLI providers.
- Gatekeeper with interval queue and denial logging.
- Rotating JSONL logs and watchdog.
- Tkinter GUI launcher.
- `uv` + `uv.lock` for dependency management.
- JSON config in `config/` (no more TOML).
- 88% test coverage with 88 unit tests and integration tests.
