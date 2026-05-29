# AI Agent Debate

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-193%20passing-brightgreen.svg)](#tests)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/badge/lint-ruff%20clean-brightgreen.svg)](https://docs.astral.sh/ruff/)
[![Line cap](https://img.shields.io/badge/file%20size-%E2%89%A4%20150%20lines-brightgreen.svg)](scripts/check_line_cap.py)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Intelligent Agents — Exercise 02** · Haifa University  
**Renat Karimov** & **Alon Engel**

<p align="center">
  <img src="assets/posters/godfather.jpg" width="220" alt="The Godfather (1972) poster"/>
  &nbsp;&nbsp;&nbsp;
  <img src="assets/posters/shawshank.jpg" width="220" alt="The Shawshank Redemption (1994) poster"/>
</p>

<p align="center">
  <strong>Which is the greater film?</strong><br/>
  Three AI agents argue it out — with live web citations — and a judge picks a winner. No ties.
</p>

<p align="center">
  <a href="https://github.com/RenatKarimovBMF/ai-agent-debate-rkarimov-aengel">GitHub repository</a>
</p>

---

## What you get

| Agent | Role | Job |
|-------|------|-----|
| **Pro** | Debater | Defends whichever side the Parent assigns at session start |
| **Con** | Debater | Defends the opposing side |
| **Parent / Judge** | Host | Assigns the sides, relays every message, declares a winner |

The two sides come from config (default: *The Godfather* vs *The Shawshank Redemption*), but **the Parent decides which agent defends which side at runtime** — seeded by the session id, so it varies across runs and is never hardcoded.

Agents never talk to each other directly — every turn goes through the **Parent**, like a moderated panel.

```
Pro  →  Parent  →  Con  →  Parent  →  Pro  →  …  (10 rounds by default)
                              ↓
                    verdict saved to logs/
```

---

## Quick start (about 5 minutes)

### 1. Choose an LLM provider

The debate needs one LLM. The app auto-selects in priority order `claude_cli → anthropic → gemini`, or you can force one with `LLM_PROVIDER`:

| Provider | Cost | Setup | `LLM_PROVIDER` |
|----------|------|-------|----------------|
| **Claude CLI** (recommended) | Uses your Claude Pro/Max login — no per-call cost | `npm i -g @anthropic-ai/claude-code`, then run `claude` once to log in | `claude_cli` |
| **Anthropic API** | Pay-as-you-go | Key from [console.anthropic.com](https://console.anthropic.com) → `ANTHROPIC_API_KEY` | `anthropic` |
| **Google Gemini** | Free tier (Flash only, ~250 req/day) | Key from [AI Studio](https://aistudio.google.com/apikey) → `GEMINI_API_KEY` | `gemini` |

We recommend **Claude** — a Pro/Max subscription gives high-quality, detailed turns at no per-call cost (the worked example in [examples/](examples/) used it; setup: [docs/CLAUDE_SETUP.md](docs/CLAUDE_SETUP.md)). The **Gemini free tier works and costs nothing, but it is noticeably less accurate and less detailed**, so it is not recommended for a representative run.

### 2. Clone and configure

```powershell
git clone https://github.com/RenatKarimovBMF/ai-agent-debate-rkarimov-aengel.git
cd ai-agent-debate-rkarimov-aengel
copy .env.example .env
```

Edit `.env` for your chosen provider — e.g. Gemini:

```env
GEMINI_API_KEY=AIza...
LLM_PROVIDER=gemini
```

…or Claude via the CLI (no API key, after `claude` login):

```env
LLM_PROVIDER=claude_cli
```

Gemini-specific detail: [docs/GEMINI_SETUP.md](docs/GEMINI_SETUP.md)

### 3. Install dependencies (UV)

```powershell
# Install uv if needed: https://docs.astral.sh/uv/
uv sync --extra dev
```

If `uv` is not on PATH: `python -m uv sync --extra dev`

### 4. Run

```powershell
# Sanity check (no API calls)
uv run python -m debate.main --dry-run

# Start the debate
uv run python -m debate.main
```

**Budget-friendly demo** (5 pings per side instead of 10):

```powershell
uv run python -m debate.main --config config/demo_setup.json
```

---

## Sample run

A complete, unedited **10-ping** session (`57cf02c2`) on the Claude provider — ~7m45s end-to-end, 21 LLM calls. The Parent assigned PRO to *Shawshank* and CON to *The Godfather* at runtime (the reverse of the config defaults), and **The Godfather (CON) won 84–76**.

**Terminal excerpt:**

```
SESSION: 57cf02c2
TOPIC: Which is the greater film: The Godfather (1972) or The Shawshank Redemption (1994)?
OPTIONS ON THE TABLE: The Godfather | The Shawshank Redemption
PINGS PER SIDE: 10
PARENT (host): assigning sides — PRO defends 'The Shawshank Redemption',
               CON defends 'The Godfather' (session-seeded, not hardcoded).

PING 1/10 — PARENT asks PRO to argue
PRO says: Let me frame the standard. "Greater" film cannot mean merely
          "most influential within one genre"… By that standard, The
          Shawshank Redemption wins decisively…
PRO sources: https://www.imdb.com/chart/top/

PING 1/10 — PARENT asks CON to respond
CON says: My opponent's standard collapses on inspection… popularity is
          not greatness… AFI ranks The Godfather at No. 2…
CON sources: https://www.afi.com/afis-100-years-100-movies-10th-anniversary-edition/

… (pings 2–10; the round turns on ping 8's refute-with-citation) …

PARENT/JUDGE: Debate finished. Judge is choosing a winner…
FINAL VERDICT: CON wins
PRO score: 76.0
CON score: 84.0
Verdict saved to: logs/verdict_57cf02c2.json
```

**Judge summary:** CON won the framing war by attacking the warrant behind PRO's IMDb ranking and stacking professional-consensus evidence (AFI #2, the 1972 Oscar sweep, the National Film Registry, Sight & Sound). The round turned on ping 8: PRO alleged a factual error and cited a non-existent AFI ranking; CON refuted it with a source in the same turn, so under the **refute-with-citation rule** the allegation rebounded against PRO. No tie — 84 to 76.

**The full session is documented in [examples/](examples/):** the [write-up](examples/README.md), the [turn-by-turn transcript](examples/transcript_57cf02c2.md), and the [verdict JSON](examples/verdict_57cf02c2.json). (`assets/sample-verdict.json` is a minimal schema sample.)

---

## Optional GUI

Want screenshots for the submission? Launch the Tkinter window:

```powershell
uv run python -m debate.gui
# or
uv run python -m debate.main --gui
```

Set **Side A vs Side B** and the question, then run — same orchestrator as the terminal.

> **For grading:** you still need to show `python -m debate.main` from the terminal.

---

## Screenshots

Add PNG captures to `assets/screenshots/` for the README and Moodle PDF:

| File | What to capture |
|------|-----------------|
| `terminal-dry-run.png` | Output of `--dry-run` |
| `terminal-debate.png` | Live debate (ping lines + sources) |
| `gui-debate.png` | Optional GUI window |
| `verdict-output.png` | Final scores / verdict JSON |

See [assets/screenshots/README.md](assets/screenshots/README.md).

---

## API usage & cost

| Mode | LLM calls | Notes |
|------|-----------|-------|
| Demo (`demo_setup.json`) | ~11 | 5 Pro + 5 Con + 1 verdict (+ occasional JSON repair) |
| Full (`setup.json`) | ~21 | 10 Pro + 10 Con + 1 verdict |

**Measured — full run, session `57cf02c2` (`claude_cli`):** exactly **21 LLM calls** (20 debate turns + 1 verdict), **0 JSON-repair retries**, **~7m45s** wall-clock — roughly **16–35s per turn** (one LLM call at a time, serialized through the Parent). See [examples/](examples/).

**Token estimate (Gemini 2.5 Flash + search):** roughly **15k–25k tokens** for demo, **35k–55k** for full — depends on turn length and grounding. (The CLI providers don't report token counts; this is a Gemini-only estimate.)

**Cost & limits.** You can run the project on a paid subscription or for free; the provider is auto-selected (`claude_cli → anthropic → gemini`):

- **Claude Pro/Max subscription (recommended).** A **Claude Pro** plan ($20/month) via `claude_cli` has **no per-call charge** — usage counts against Claude's rolling limits. In our full 10-ping run we used **under 10% of the 5-hour window** and **~1% of the weekly allowance**, so you can comfortably run many debates per month.
- **Free tier (Gemini).** Free at [AI Studio](https://aistudio.google.com/) — **$0**, but with real caveats. The free tier serves **Flash models only** (`gemini-2.5-flash` and lighter fallbacks — the fast, low-cost Gemini, *not* the more capable Pro tier) and caps you at roughly **250 requests/day** with tight rate limits (HTTP 429). Because of the Flash model, a free run is **noticeably less accurate and less detailed** than Claude, and the daily cap can interrupt a full debate. We recommend it only when a subscription isn't an option.

If you hit a limit: wait and retry, or use `config/demo_setup.json` (5 pings). The course allows reducing 10 → 5 pings — **no grade penalty**.

Gatekeeper settings in `config/rate_limits.json` throttle requests (`min_interval_ms`, `max_total_requests`).

---

## For graders & reviewers

| Requirement | Status |
|-------------|--------|
| Three agents, mediated flow | Done |
| JSON message protocol | `debate.models` |
| Python orchestrator | `python -m debate.main` |
| Separate skills (Pro / Con / Parent) | `.claude/skills/` |
| Internet citations in schema | Each turn includes URLs |
| 10 pings/side (configurable) | `config/setup.json` |
| Gatekeeper + watchdog + JSONL logs | `debate/gatekeeper/`, `logs/` |
| OOP + architecture diagram | [docs/architecture.md](docs/architecture.md) |
| PRD / PLAN / TODO | [docs/](docs/) |
| ADRs (per architectural decision) | [docs/adr/](docs/adr/) |
| Prompt book (every LLM-facing prompt) | [docs/PROMPTS.md](docs/PROMPTS.md) |
| Tests + 100% coverage on in-scope code | 193 tests · `uv run pytest --cov` |
| Strict 150-line cap per `.py` file | `uv run python scripts/check_line_cap.py` |
| CI (ruff + cap + tests on Python 3.11 / 3.12 / 3.13) | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| Version tracking (code + config in lock-step) | `__version__` + `version` key validated at load |
| UV + `uv.lock`, JSON config | `config/setup.json` |

**Quality checks (the same gate CI runs):**

```powershell
uv run python scripts/check_line_cap.py    # every .py <= 150 raw lines
uv run ruff check src tests scripts        # zero violations
uv run pytest --cov                        # 193 tests, fail_under = 100%
```

Or `make check` for all three in one go.

**Docs:** [PRD](docs/PRD.md) · [PLAN](docs/PLAN.md) · [Architecture](docs/architecture.md) · [Claude setup](docs/CLAUDE_SETUP.md) · [Gemini setup](docs/GEMINI_SETUP.md) · [Prompts](docs/PROMPTS.md) · [Known limitations](docs/KNOWN_LIMITATIONS.md) · [Changelog](CHANGELOG.md) · [ADRs](docs/adr/)

---

## Project layout

```
ai-agent-debate-rkarimov-aengel/
├── config/                 setup.json, rate_limits.json (+ demo variants, version-stamped)
├── src/debate/             orchestrator, agents, gatekeeper, transport, GUI, watchdog
├── src/sdk/                Gemini / Anthropic / Claude-CLI LLM clients
├── tests/unit/             191 targeted unit tests (each *_coverage.py < 150 lines)
├── tests/integration/      2 config-scaffold tests
├── scripts/                check_line_cap.py (150-line gate)
├── docs/                   PRD, PLAN, TODO, PROMPTS, KNOWN_LIMITATIONS, architecture
├── docs/adr/               10 architectural decision records + index
├── examples/               worked 10-ping debate: write-up, transcript, verdict
├── .claude/skills/         project-local agent skills (debaters + parent/judge)
├── .github/                CI workflow + PR/issue templates
├── assets/posters/         README movie art
├── assets/screenshots/     submission captures
├── logs/                   JSONL logs + verdict_*.json (local, gitignored)
├── AUTHORS.md              team
├── CHANGELOG.md            Keep-a-Changelog (v1.00 baseline)
├── CONTRIBUTING.md         dev workflow + quality gates
├── LICENSE                 MIT
├── Makefile                uv wrappers (install / test / lint / cap / check / run / gui)
├── .pre-commit-config.yaml ruff + line-cap on every commit
├── pyproject.toml          dependencies + coverage gate (fail_under = 100)
└── uv.lock                 pinned dependency graph
```

---

## Submission (pairs)

| Partner | Moodle | GitHub |
|---------|--------|--------|
| Renat Karimov | PDF with repo link | This repo |
| Alon Engel | PDF with repo link | Same repo, separate PDF |

Each partner uploads their **own** Moodle PDF pointing to the **same** public GitHub URL.  
Do **not** commit `.env` — only `.env.example`.

---

## Poster credits

Posters in `assets/posters/` are used for educational illustration (Wikipedia film articles).  
*The Godfather* © Paramount Pictures · *The Shawshank Redemption* © Columbia Pictures.

---

## License

Released under the [MIT License](LICENSE).
Academic project for Haifa University, Intelligent Agents course, Exercise 02.
