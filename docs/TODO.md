# Project TODO — AI Agent Debate

**Authors:** Renat Karimov, Alon Engel  
**Version:** 1.00 (submission baseline)  
**Last updated:** 2026-05-27

Status key: `[ ]` pending · `[~]` in progress · `[x]` done · `[-]` cancelled

---

## Stage 1 — Planning documentation

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S1-01 | Create `docs/PRD.md` | Renat | [x] |
| S1-02 | Create `docs/PLAN.md` (C4, ADRs, diagrams) | Alon | [x] |
| S1-03 | Create `docs/TODO.md` (this file) | Renat | [x] |
| S1-04 | Create `docs/PRD_orchestrator.md` | Alon | [x] |
| S1-05 | Create `docs/PRD_gatekeeper.md` | Renat | [x] |
| S1-06 | Create `docs/PRD_llm_sdk.md` | Alon | [x] |
| S1-07 | User commit + push Stage 1 | Both | [x] |

**Commit message (suggested):** `docs: add PRD, PLAN, TODO and mechanism PRDs`

---

## Stage 2 — Folder restructure

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S2-01 | Add `config/` directory scaffold | Renat | [x] |
| S2-02 | Move tests to `tests/unit/` and `tests/integration/` | Alon | [x] |
| S2-03 | Add `assets/screenshots/` for README | Renat | [x] |
| S2-04 | Update imports and pytest paths | Alon | [x] |
| S2-05 | User commit + push Stage 2 | Both | [ ] |

**Commit message (suggested):** `refactor: add config/assets scaffold and split tests into unit/integration`

---

## Stage 3 — Split process orchestrator

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S3-01 | Extract worker modules from `process_orchestrator.py` | Alon | [x] |
| S3-02 | Extract supervisor / session lifecycle | Renat | [x] |
| S3-03 | Keep all files ≤ 150 lines | Both | [x] |
| S3-04 | Update / add unit tests for extracted modules | Alon | [x] |
| S3-05 | User commit + push Stage 3 | Both | [ ] |

**Commit message (suggested):** `refactor: split process orchestrator into debate.orchestrator package`

**Result:** `src/debate/orchestrator/` — 12 modules, each ≤ 82 code lines (150 limit per Guidelines V3).

---

## Stage 4 — Split agents, GUI, legacy orchestrator

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S4-01 | Split `agents.py` by role | Renat | [x] |
| S4-02 | Split `gui.py` (UI vs controller) | Alon | [x] |
| S4-03 | Split legacy orchestrator into `debate/legacy/` | Renat | [x] |
| S4-04 | Ruff pass on all touched files | Both | [x] |
| S4-05 | User commit + push Stage 4 | Both | [ ] |

**Commit message (suggested):** `refactor: split agents, gui, and legacy orchestrator modules`

---

## Stage 5 — UV migration

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S5-01 | Generate `uv.lock` | Renat | [x] |
| S5-02 | Remove `requirements.txt` | Renat | [x] |
| S5-03 | Update README for UV-only install | Alon | [x] |
| S5-04 | Verify `uv run pytest` and `uv run python -m debate.main --dry-run` | Both | [x] |
| S5-05 | User commit + push Stage 5 | Both | [ ] |

**Commit message (suggested):** `build: migrate to uv with uv.lock and remove requirements.txt`

---

## Stage 6 — JSON configuration

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S6-01 | Create `config/setup.json` from TOML debate section | Alon | [x] |
| S6-02 | Create `config/rate_limits.json` for gatekeeper | Renat | [x] |
| S6-03 | Update `debate.config` loader | Alon | [x] |
| S6-04 | Demo JSON variants (`demo_setup.json`, `demo_rate_limits.json`) | Renat | [x] |
| S6-05 | User commit + push Stage 6 | Both | [ ] |

**Commit message (suggested):** `refactor: load runtime config from JSON in config/`

---

## Stage 7 — Gatekeeper enhancement

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S7-01 | Add request queue / serialization before LLM calls | Alon | [x] |
| S7-02 | Log denied requests with reason | Renat | [x] |
| S7-03 | Wire rate limits from `config/rate_limits.json` | Alon | [x] |
| S7-04 | Expand `tests/unit/test_gatekeeper.py` | Renat | [x] |
| S7-05 | User commit + push Stage 7 | Both | [ ] |

**Commit message (suggested):** `feat: enhance gatekeeper with interval queue and denial logging`

**Note:** Limits apply per worker process (pro, con, parent each have their own gatekeeper).

---

## Stage 8 — Test coverage ≥ 85%

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S8-01 | Add pytest-cov to dev dependencies | Renat | [x] |
| S8-02 | Unit tests: models, config, env_loader | Alon | [x] |
| S8-03 | Integration tests: orchestrator with mock LLM | Renat | [x] |
| S8-04 | Measure coverage; fill gaps | Both | [x] |
| S8-05 | User commit + push Stage 8 | Both | [ ] |

**Commit message (suggested):** `test: reach 85% coverage with unit and integration tests`

**Coverage:** `uv run pytest --cov` → **88%** on core modules (multiprocess worker entrypoints excluded from coverage scope).

---

## Stage 9 — Submission polish

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S9-01 | Full debate run (10 pings) with Gemini + search | Both | [ ] optional if quota allows |
| S9-02 | Demo run (5 pings) documented in README | Renat | [x] |
| S9-03 | Screenshots: terminal, GUI, logs, verdict | Alon | [ ] add PNGs to assets/screenshots/ |
| S9-04 | Prompt log + token/cost analysis | Renat | [x] (see `docs/PROMPTS.md`) |
| S9-05 | User-friendly README + movie posters | Alon | [x] |
| S9-06 | Final Ruff + pytest + dry-run checklist | Both | [x] |
| S9-07 | Moodle PDF per partner (same GitHub URL) | Both | manual (by hand) |
| S9-08 | User commit + push final | Both | [ ] |

---

## Stage 10 — Skill architecture overhaul

Triggered by the in-class clarifications: project-local skills only, research-backed judging, multi-skill debaters, host-style opening, refute-with-citation rule.

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S10-01 | Rewrite `debate-parent-judge` skill around five principles (WUDC / IDEA / NSDA / Snider) | Renat | [x] |
| S10-02 | New `debate-host-protocol` skill (opening briefing, side assignment) | Alon | [x] |
| S10-03 | New `debate-judge-rubric` skill (Matter/Manner/Method/Clash/Burden) | Renat | [x] |
| S10-04 | New `debate-argument-builder` skill (CWI-S, side-agnostic) | Alon | [x] |
| S10-05 | New `debate-rebuttal-strategist` skill (refute-with-citation, side-agnostic) | Renat | [x] |
| S10-06 | Slim `debate-pro-godfather` / `debate-con-shawshank` to lore-only | Alon | [x] |
| S10-07 | `docs/PRD_judge_rubric.md` — research basis + skill stack | Renat | [x] |

---

## Stage 11 — Runtime side assignment

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S11-01 | `orchestrator/host_protocol.py` with `decide_sides()` and `send_assignments()` | Alon | [x] |
| S11-02 | `ASSIGN` command in `orchestrator/commands.py`, handled in `child_worker.py` | Renat | [x] |
| S11-03 | `DebaterAgent` base with `apply_assignment()` + thin `ProAgent`/`ConAgent` | Alon | [x] |
| S11-04 | Parent worker sends assignments before the ping loop | Renat | [x] |
| S11-05 | Update debater + judge prompts to reference runtime assignment | Alon | [x] |
| S11-06 | Update CLI `--dry-run` and GUI labels to reflect "options on the table" | Renat | [x] |
| S11-07 | `tests/unit/test_host_protocol.py` — determinism + variability + override | Alon | [x] |

---

## Stage 12 — Version tracking and prompt book

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S12-01 | `src/debate/_version.py` with `__version__ = "1.00"` | Renat | [x] |
| S12-02 | Bump `pyproject.toml` to `1.00` and re-export from `debate.__init__` | Alon | [x] |
| S12-03 | Add `"version": "1.00"` to all four JSON config files | Renat | [x] |
| S12-04 | `_validate_config_version` in `config/loader.py` (hard-fail on missing) | Alon | [x] |
| S12-05 | `--version` flag + `App version` line in `--dry-run` | Renat | [x] |
| S12-06 | `docs/PROMPTS.md` — prompt book with rationale and iteration history | Alon | [x] |
| S12-07 | Refresh `docs/PRD.md` / `docs/PLAN.md` / `docs/TODO.md` for v1.00 | Both | [x] |
| S12-08 | English-only sweep across the repo (no Hebrew anywhere) | Both | [x] |

---

## Stage 13 — Strict 150-line file-size compliance

Re-audit under the strict (raw lines, including blanks/comments) reading of Guidelines V3 §5.2. Five source files exceeded 150 raw lines and were split.

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S13-01 | Convert `debate/transport.py` (172) into a `debate/transport/` package: `base`, `file_queue`, `fifo`, `factory` | Renat | [x] |
| S13-02 | Split `agents/parent_agent.py` (181) — extract `verdict_builder.py` and `judge_prompts.py` | Alon | [x] |
| S13-03 | Split `legacy/session_loop.py` (164) — extract `ping_runner.py` | Renat | [x] |
| S13-04 | Split `gui/app.py` (162) — extract `gui/env_check.py` (provider status + input validation) | Alon | [x] |
| S13-05 | Split `gui/panels.py` (160) — extract `gui/form.py` (FormWidgets + build_form) | Renat | [x] |
| S13-06 | Re-run pytest + ruff + file-size audit; all 91 tests pass, every file ≤ 138 raw lines | Both | [x] |
| S13-07 | Update PRD / PLAN / TODO to use the strict raw-line rule and document the new modules | Both | [x] |

---

## Exercise 02 checklist (functional)

| Requirement | Status |
|-------------|--------|
| Three agents, mediated flow | [x] |
| JSON message protocol | [x] |
| Python orchestrator | [x] |
| Project-local skills only (no global) | [x] |
| Multi-skill debaters (argument-builder + rebuttal-strategist + lore) | [x] |
| Parent skill stack (judge + host-protocol + rubric, research-backed) | [x] |
| Host-style opening briefing per child | [x] |
| Runtime side assignment by Parent (not hardcoded) | [x] |
| Refute-with-citation rule enforced in prompts and rubric | [x] |
| Internet citations in schema | [x] |
| 10 pings/side (configurable) | [x] |
| Gatekeeper (interval queue + denial logs) | [x] |
| Watchdog hooks | [x] |
| Rotating logs | [x] |
| OOP + architecture diagram | [x] |
| PRD / PLAN / TODO / PROMPTS | [x] |
| Mechanism PRDs (orchestrator / gatekeeper / SDK / judge rubric) | [x] |
| Full run screenshots | [ ] add to assets/screenshots/ |
| 85% coverage | [x] (88%) |
| 150-line file limit (raw lines, strict) | [x] (largest 138) |
| UV + uv.lock | [x] |
| JSON config in `config/` with `"version"` key + validator | [x] |
| English-only project content | [x] |

---

## Remaining work for submission

- **Screenshots:** capture terminal `--dry-run`, a live debate, GUI window, a verdict JSON file, and an excerpt of the rotating log. Place in `assets/screenshots/` and link from `README.md`.
- **End-to-end run:** one full 10-ping run if Gemini quota permits, otherwise document the demo (5-ping) run.
- **Moodle PDF:** each partner submits the same GitHub URL via Moodle (manual step).

## Optional extras (not required, may add submission polish)

- `docs/DECISIONS.md` — running decision log distinct from PRD/PLAN.
- `notebooks/analysis.ipynb` — sensitivity analysis (rubric weight sweep, pings-per-side effect on verdict).
- Resume mechanism — recover a crashed session from the saved JSONL transcript instead of restarting.
