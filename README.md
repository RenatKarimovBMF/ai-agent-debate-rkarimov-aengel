# AI Agent Debate — Exercise 02

**Course:** Intelligent Agents (Haifa University)  
**Authors:** Renat Karimov, Alon Engel  
**Topic:** Which is the greater film — **The Godfather** (1972) or **The Shawshank Redemption** (1994)?

## Debate sides

| Role | Agent | Position |
|------|--------|----------|
| Pro | `ProAgent` / skill `debate-pro-godfather` | The Godfather is the greater film |
| Con | `ConAgent` / skill `debate-con-shawshank` | The Shawshank Redemption is the greater film |
| Parent | `ParentAgent` / skill `debate-parent-judge` | Host + judge (persuasion only, **no tie**) |

## Free Gemini setup (start here)

1. Get a key: **https://aistudio.google.com/apikey** (free, no credit card in most regions)
2. `copy .env.example .env` and set `GEMINI_API_KEY=AIza...` and `LLM_PROVIDER=gemini`
3. `pip install -r requirements.txt`
4. `python -m debate.main --dry-run` → should print `LLM provider: gemini`

Full guide: [docs/GEMINI_SETUP.md](docs/GEMINI_SETUP.md)

## Requirements checklist

- [x] Three agents (parent, pro, con) — mediated flow only
- [x] JSON message protocol (`debate.models`)
- [x] Python orchestrator (`debate.main`)
- [x] Separate skills per side (contradiction)
- [x] Internet citations required in each turn schema
- [x] 10 pings per side (configurable in `config.toml`)
- [x] Gatekeeper, watchdog hooks, rotating JSONL logs
- [x] OOP + architecture diagram (`docs/architecture.md`)
- [x] Tests (`pytest`), Ruff, `config.toml`, `.env.example`
- [ ] Full run screenshots + sample session log (add after first live run)
- [ ] GitHub public repo + Moodle PDF per partner (see Submission)

## Optional GUI (creativity / screenshots)

The assignment **requires** terminal or SDK operation for grading, but **allows** an optional GUI plus screenshots (Exercise 02 §8.6).

```powershell
$env:PYTHONPATH = "src"
python -m debate.gui
# or
python -m debate.main --gui
```

The window lets you set **Side A vs Side B** and the **debate question**, then runs the same orchestrator as the terminal. Default values are Godfather vs Shawshank. Add screenshots of the GUI to `docs/screenshots/` for the README.

**You must still demonstrate** `python -m debate.main` from the terminal for the grader.

## Quick start (UV)

```powershell
cd "c:\Users\Ренат\Desktop\Haifa Un\6 is Final\Ai\ai-agent-debate-karimov-engel"
copy .env.example .env
# Edit .env — set ANTHROPIC_API_KEY

pip install -r requirements.txt
```

Or with UV:

```powershell
uv venv
uv pip install -e ".[dev]"

uv run pytest
uv run python -m debate.main --dry-run
uv run python -m debate.main
```

Without UV:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
$env:PYTHONPATH = "src"
python -m debate.main --dry-run
```

## Budget note

If API budget is tight, set in `config.toml`:

```toml
pings_per_side = 5
```

Document that here — **no grade penalty** per course instructions.

## Full mode and budget demo mode

The default `config.toml` uses `pings_per_side = 10`, which matches the full exercise requirement.

Because the system uses real LLM calls with web grounding, a full debate can require many API calls:

- 10 Pro turns
- 10 Con turns
- 1 Parent/Judge verdict
- possible JSON repair calls
- possible retry calls after rate limits

On free Gemini quota this can trigger HTTP 429 rate-limit errors.

For demonstration under a limited free API quota, the repository also includes `config.demo.toml`, which uses `pings_per_side = 5`. This follows the assignment note allowing a reduction from 10 to 5 pings when budget is limited.

Run full mode:

```bash
python -m debate.main

## Project layout

```
ai-agent-debate-karimov-engel/
├── config.toml              # All parameters (no hardcoding)
├── .env.example
├── .claude/skills/          # pro / con / parent skills
├── .claude/commands/        # optional CLI command
├── src/debate/              # orchestrator, agents, IPC, gatekeeper
├── src/sdk/                 # Claude CLI / API wrapper
├── docs/architecture.md     # class diagram + flow
├── tests/
├── fifo/                    # IPC queues (runtime)
└── logs/                    # JSONL logs + verdict_*.json
```

## Message flow

```
Pro  →  Parent  →  Con  →  Parent  →  Pro  →  …  (10 rounds)
                ↓
         verdict_*.json (winner by persuasion)
```

Children never communicate directly.

## Claude skills (manual stage 1–2)

Install skills from `.claude/skills/` in Claude Code, or copy to `~/.claude/skills/`.

Suggested manual test:

1. Terminal A — parent skill  
2. Terminal B — pro skill  
3. Terminal C — con skill  
4. Paste JSON turns through parent only  

Then run stage 3: `python -m debate.main`.

## Submission (pairs)

| Who | Moodle | GitHub |
|-----|--------|--------|
| Renat Karimov | Upload PDF with **your** repo link | Push code; share with lecturer or **public** repo |
| Alon Engel | Upload PDF with **your** repo link | Same codebase; **different** Moodle PDF each |

Do **not** submit only one partner’s repo link on Moodle.  
Do **not** commit `.env` — only `.env.example`.

## Pair workflow

1. One shared GitHub repo (both push)  
2. Run full debate once; save screenshots to `docs/screenshots/`  
3. Copy sample `logs/debate_000.jsonl` excerpt into README  
4. Each partner submits own Moodle PDF pointing to the same GitHub URL  

## Lint

```powershell
uv run ruff check src tests
uv run ruff format src tests
```

## License

Academic project — Haifa University, Exercise 02.
