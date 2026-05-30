# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Per submission guideline §8.1, the major version is bumped on breaking
restructures; minor versions bring backwards-compatible additions;
patches are bug fixes.

## [1.10] — 2026-05-30

First iteration past the `1.00` submission baseline: Windows Claude CLI
support, a Claude-first provider priority, a full worked example, and
repo/CI hygiene.

### Added

- **Cross-provider skill parity.** `debate/skills.py` reads the project
  skills under `.claude/skills/` and appends the role-appropriate ones to
  the system prompt for the providers that don't load them natively —
  **Gemini and the Anthropic API** (`_INJECTED_PROVIDERS`). The Claude
  CLI already loads them, so it is skipped. `.claude/skills/` stays the
  single source of truth (no duplication). See KNOWN_LIMITATIONS L-09.
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

### Added

- **Full transcript persistence.** At the end of a debate the Parent
  writes the complete, untruncated transcript (every turn + sources) to
  `logs/transcript_<session>.md` (gitignored, like the verdict). The
  console previously abbreviated long turns; the Parent's in-memory
  history and the verdict prompt always saw the full text, but it was
  not persisted in full until now.
- **Type-check gate (mypy).** `uv run mypy src` runs clean on the core
  and is wired into CI, the Makefile (`make typecheck` / `make check`),
  CONTRIBUTING, and the PR template. The Tk GUI is scoped out
  (`[[tool.mypy.overrides]]`) since Tk stubs are noisy and low-value;
  the optional, platform-specific `os.mkfifo` and `mp.Process` lines
  carry targeted `# type: ignore` comments.
- **CI runs headless GUI tests under Xvfb.** The workflow installs
  `xvfb` and runs `pytest` via `xvfb-run -a`, so the real-Tk GUI tests
  (which need a display) pass on the headless `ubuntu-latest` runner
  while coverage stays at a genuine 100%.

### Changed

- **Coverage is now genuinely 100% — the `omit` list is empty.** Every
  previously-excluded runtime module is covered by real in-process tests:
  the orchestrator workers, supervisor, process pool, watchdog, the legacy
  reference orchestrator, `transport/fifo.py` (Unix `os.mkfifo`/`select`
  monkeypatched), the GUI, and `main.py` — plus an end-to-end debate test
  with a fake LLM. Tests do not spawn real OS processes or call live APIs
  (those remain simulated; see KNOWN_LIMITATIONS L-07). 266 tests total.
  The manual Gemini check script moved to `scripts/manual_gemini_check.py`
  (out of the coverage source tree).

### Fixed

- **Claude CLI output encoding on Windows.** `ClaudeAgentClient` now runs
  the CLI subprocess with `encoding="utf-8"` (and `errors="replace"`),
  so the model's UTF-8 output (em-dashes, quotes, etc.) is decoded
  correctly instead of being mangled by the Windows locale codepage
  (cp1252). Previously those characters were corrupted in the transcript
  and in the text the judge scored.
- **Project-root resolution when run as an installed package.**
  `project_root()` (in both `config/loader.py` and `env_loader.py`) now
  prefers the working directory — or an ancestor — that actually
  contains `pyproject.toml` and `config/setup.json`, via a shared
  `find_project_root` helper. Previously a file-relative path resolved
  into `.venv/Lib` when `uv run python -m debate.main` executed the
  installed copy, so verdicts were written to `.venv/Lib/logs/` instead
  of the repo's `logs/`. Verdicts and config now resolve next to the
  project as the README documents.
- **Claude CLI provider on Windows.** `ClaudeAgentClient` now resolves
  the CLI through `shutil.which` (so the npm `claude.cmd` / `claude.ps1`
  shim is found, where the bare name failed under `CreateProcess`), and
  invokes it with the system prompt via `--system-prompt-file` and the
  user prompt via stdin. Passing multi-line prompts as CLI arguments
  silently broke the Windows batch shim; a temp file path plus stdin is
  safe on every platform. This makes the `claude_cli` provider work
  end-to-end on Windows.

### Added

- **Worked example folders.** `examples/` holds two full, unedited 10-ping
  sessions, each with a write-up (`README.md`), transcript (`transcript.md`),
  and verdict (`verdict.json`): `godfather-vs-shawshank/` (the default
  topic, `57cf02c2`, The Godfather wins 84–76) and `abortion-legality/`
  (a custom `--topic` run, `c1255aa1`, PRO wins 84–80) which demonstrates
  the engine is topic-agnostic. An index `examples/README.md` lists both.

### Changed

- **Console no longer truncates debate turns.** The live `PRO says:` /
  `CON says:` lines now print each turn in full instead of cutting at
  ~700 characters mid-sentence. (The judge and the opponent always
  received the full text; only the on-screen log was abbreviated.)
- **Debater skills are now fully generic (no hardcoded topic lore).**
  Removed the two film-specific lore skills (`debate-pro-godfather`,
  `debate-con-shawshank`) and replaced them with one side-agnostic,
  topic-agnostic `debate-evidence` skill that teaches sourcing/citation
  rather than supplying facts. Debaters now use three generic skills and
  source their own evidence at runtime, so any `--topic` works without
  authoring new skills. See ADR-008 (updated).
- **Provider auto-priority reordered to `claude_cli → anthropic → gemini`.**
  When `LLM_PROVIDER=auto`, the SDK now prefers the Claude CLI (a
  Claude Pro/Max subscription, detected via `ClaudeAgentClient.available()`)
  for higher-fidelity turns, then the Anthropic API, then the free
  Gemini tier as a fallback. Previously Gemini was tried first. Force a
  specific provider with `LLM_PROVIDER=gemini|anthropic|claude_cli`.
- **Runtime verdicts are no longer tracked.** `logs/verdict_*.json` is
  now gitignored (alongside the existing `logs/*.log` and `*.jsonl`
  rules) and the previously committed `logs/verdict_18607637.json` was
  untracked. Curated example verdicts live in `assets/`
  (`assets/sample-verdict.json`, `examples/*/verdict.json`);
  `logs/` holds only local runtime output plus its `.gitkeep`.
- **Opening-statement framing is motion-agnostic.** `turn_prompt` no
  longer assumes a "which is greater" comparison; it asks the debater to
  define the standard for winning (comparison *or* proposition), so the
  engine is generic for any `--topic`. `docs/PROMPTS.md` updated to
  match.
- **Quality-gate scope aligned across CI / Makefile / docs.** Ruff,
  the line-cap script, and `pytest --cov` now all walk
  `src/ tests/ scripts/` (Makefile `lint`/`format`, pre-commit, CI
  workflow). The CI step that ran only `tests/unit` now runs the full
  suite — the two integration tests under `tests/integration/` are
  config-scaffold tests and never touch Gemini or Anthropic.
- **Documentation counts refreshed.** README badge, `CONTRIBUTING.md`
  gate snippet, and PR-template checklist updated to the actual figures
  (266 tests; `fail_under = 100`).

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
  Clash 25 / Burden 15 = 100). Debaters share three generic,
  topic-agnostic skills (`debate-argument-builder`,
  `debate-rebuttal-strategist`, `debate-evidence`) — no skill hardcodes
  topic facts; debaters source their own evidence at runtime. All skills
  are project-local under `.claude/skills/`. See `docs/PRD_judge_rubric.md`
  and ADR-008.
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
