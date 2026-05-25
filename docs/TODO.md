# Project TODO — AI Agent Debate

**Authors:** Renat Karimov, Alon Engel  
**Version:** 1.00  
**Last updated:** 2026-05-21

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
| S3-01 | Extract worker modules from `process_orchestrator.py` | Alon | [ ] |
| S3-02 | Extract supervisor / session lifecycle | Renat | [ ] |
| S3-03 | Keep all files ≤ 150 lines | Both | [ ] |
| S3-04 | Update / add unit tests for extracted modules | Alon | [ ] |
| S3-05 | User commit + push Stage 3 | Both | [ ] |

**Files over limit today:** `process_orchestrator.py` (~519 lines)

---

## Stage 4 — Split agents, GUI, legacy orchestrator

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S4-01 | Split `agents.py` by role | Renat | [ ] |
| S4-02 | Split `gui.py` (UI vs controller) | Alon | [ ] |
| S4-03 | Split or slim `orchestrator.py` (legacy) | Renat | [ ] |
| S4-04 | Ruff pass on all touched files | Both | [ ] |
| S4-05 | User commit + push Stage 4 | Both | [ ] |

**Files over limit today:** `agents.py` (~454), `gui.py` (~288), `orchestrator.py` (~218)

---

## Stage 5 — UV migration

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S5-01 | Generate `uv.lock` | Renat | [ ] |
| S5-02 | Remove `requirements.txt` | Renat | [ ] |
| S5-03 | Update README for UV-only install | Alon | [ ] |
| S5-04 | Verify `uv run pytest` and `uv run python -m debate.main --dry-run` | Both | [ ] |
| S5-05 | User commit + push Stage 5 | Both | [ ] |

---

## Stage 6 — JSON configuration

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S6-01 | Create `config/setup.json` from TOML debate section | Alon | [ ] |
| S6-02 | Create `config/rate_limits.json` for gatekeeper | Renat | [ ] |
| S6-03 | Update `debate.config` loader | Alon | [ ] |
| S6-04 | Keep `config.demo.toml` or add demo JSON variant | Renat | [ ] |
| S6-05 | User commit + push Stage 6 | Both | [ ] |

---

## Stage 7 — Gatekeeper enhancement

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S7-01 | Add request queue / serialization before LLM calls | Alon | [ ] |
| S7-02 | Log denied requests with reason | Renat | [ ] |
| S7-03 | Wire rate limits from `config/rate_limits.json` | Alon | [ ] |
| S7-04 | Expand `tests/unit/test_gatekeeper.py` | Renat | [ ] |
| S7-05 | User commit + push Stage 7 | Both | [ ] |

---

## Stage 8 — Test coverage ≥ 85%

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S8-01 | Add pytest-cov to dev dependencies | Renat | [ ] |
| S8-02 | Unit tests: models, config, env_loader | Alon | [ ] |
| S8-03 | Integration tests: orchestrator with mock LLM | Renat | [ ] |
| S8-04 | Measure coverage; fill gaps | Both | [ ] |
| S8-05 | User commit + push Stage 8 | Both | [ ] |

---

## Stage 9 — Submission polish

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S9-01 | Full debate run (10 pings) with Gemini + search | Both | [ ] |
| S9-02 | Demo run (5 pings) documented in README | Renat | [ ] |
| S9-03 | Screenshots: terminal, GUI, logs, verdict | Alon | [ ] |
| S9-04 | Prompt log + token/cost analysis | Renat | [ ] |
| S9-05 | Fix README (paths, broken fences, repo name) | Alon | [ ] |
| S9-06 | Final Ruff + pytest + dry-run checklist | Both | [ ] |
| S9-07 | Moodle PDF per partner (same GitHub URL) | Both | [ ] |
| S9-08 | User commit + push final | Both | [ ] |

---

## Exercise 02 checklist (functional)

| Requirement | Status |
|-------------|--------|
| Three agents, mediated flow | [x] |
| JSON message protocol | [x] |
| Python orchestrator | [x] |
| Separate skills (Pro / Con / Parent) | [x] |
| Internet citations in schema | [x] |
| 10 pings/side (configurable) | [x] |
| Gatekeeper | [x] (enhance Stage 7) |
| Watchdog hooks | [x] |
| Rotating logs | [x] |
| OOP + architecture diagram | [x] |
| PRD / PLAN / TODO | [x] (Stage 1) |
| Full run screenshots | [ ] |
| 85% coverage | [ ] |
| 150-line file limit | [ ] |
| UV + uv.lock | [ ] |

---

## How to commit each stage (local)

```powershell
cd "<your-repo-path>"
git status
git add docs/
git commit -m "docs: add PRD, PLAN, TODO and mechanism PRDs"
git push
```

Or use VS Code **Source Control** → stage files → commit message → **Sync/Push**.
