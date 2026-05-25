# Product Requirements Document — AI Agent Debate

**Project:** Exercise 02 — Intelligent Agents (Haifa University)  
**Version:** 1.00 (planning baseline)  
**Authors:** Renat Karimov, Alon Engel  
**Last updated:** 2026-05-21

---

## 1. Overview

Build a **mediated multi-agent debate system** in Python where three LLM-powered agents argue a fixed topic under strict orchestration rules. The system must demonstrate agent coordination, structured IPC, API budget control, and professional software engineering practices.

**Debate topic (default):** Which is the greater film — *The Godfather* (1972) or *The Shawshank Redemption* (1994)?

| Role | Agent | Position |
|------|-------|----------|
| Pro | `ProAgent` | The Godfather is the greater film |
| Con | `ConAgent` | The Shawshank Redemption is the greater film |
| Parent | `ParentAgent` | Host and judge (persuasion only; **no tie**) |

---

## 2. Goals

1. Satisfy all functional requirements of Exercise 02 (§8).
2. Meet Software Submission Guidelines V3 (planning docs, SDK layer, tests, Ruff, coverage).
3. Run end-to-end on Windows (primary dev) and remain portable to Linux/macOS.
4. Support **free-tier Gemini** for development and demo; allow Anthropic API / Claude CLI for production runs.
5. Produce auditable logs, a final verdict JSON, and README evidence (screenshots, cost notes).

---

## 3. User stories

| ID | As a… | I want… | So that… |
|----|-------|---------|----------|
| US-01 | Grader | Run `python -m debate.main` from terminal | I can verify CLI orchestration without GUI |
| US-02 | Grader | See JSON messages between agents | I can confirm mediated flow (no direct Pro↔Con) |
| US-03 | Grader | See internet citations in each turn | Agents ground claims in external sources |
| US-04 | Student | Limit API calls via gatekeeper | I stay within budget during development |
| US-05 | Student | Use demo config (5 pings) | I can test cheaply and document budget limits |
| US-06 | Student | Optional GUI for topic input | I can demo creatively with screenshots |
| US-07 | Student | Separate skills per agent | Each side has distinct prompts and behavior |
| US-08 | Grader | Read PRD / PLAN / TODO | I can assess planning and architecture before code |

---

## 4. Functional requirements

### 4.1 Agents and roles

- **FR-01:** Exactly three agents: Parent (judge/host), Pro, Con.
- **FR-02:** Pro and Con must **never** communicate directly; all messages pass through Parent.
- **FR-03:** Each agent has a dedicated Claude skill under `.claude/skills/` with contradictory positions.
- **FR-04:** Parent delivers a final **verdict** with winner, scores, and rationale (no tie allowed).

### 4.2 Debate flow

- **FR-05:** Default **10 pings per side** (configurable; 5 allowed with README justification).
- **FR-06:** Turn order: Parent requests Pro → Pro responds → Parent relays to Con → Con responds → Parent relays to Pro → repeat.
- **FR-07:** Each turn includes structured text and **citations** (title + URL).
- **FR-08:** Session ends with verdict written to `logs/verdict_<session_id>.json`.

### 4.3 Message protocol

- **FR-09:** All IPC uses **JSON** (`DebateMessage`, `VerdictMessage` in `debate.models`).
- **FR-10:** Message types: `turn`, `relay`, `verdict`, `keepalive`, `error`.
- **FR-11:** Schema version field (`version: "1.0"`) on all messages.

### 4.4 Orchestration

- **FR-12:** Python orchestrator (not CLI-only) controls the full debate lifecycle.
- **FR-13:** **Multiprocess architecture:** supervisor + three worker processes (Parent, Pro, Con) using `multiprocessing.Queue` (Windows-safe `spawn`).
- **FR-14:** Legacy single-process `DebateOrchestrator` retained for tests/reference until refactor completes.

### 4.5 LLM access

- **FR-15:** All LLM calls go through **SDK layer** (`sdk.llm_client.LlmClient`).
- **FR-16:** Provider priority (auto): Gemini → Anthropic API → Claude CLI.
- **FR-17:** Gemini supports optional **Google Search grounding** for citations (`use_google_search` in config).
- **FR-18:** Secrets only in `.env`; repository ships `.env.example` only.

### 4.6 Gatekeeper and reliability

- **FR-19:** Gatekeeper enforces global and per-agent request limits before each LLM call.
- **FR-20:** Watchdog / timeout handling for hung LLM or IPC operations.
- **FR-21:** Rotating structured logs (JSONL) under `logs/`.

### 4.7 Configuration

- **FR-22:** Debate parameters in `config/setup.json` and gatekeeper limits in `config/rate_limits.json`.
- **FR-23:** No hardcoded debate topic, ping count, or side names in application logic.

### 4.8 Entry points

- **FR-24:** `python -m debate.main` — primary CLI entry.
- **FR-25:** `python -m debate.gui` — optional GUI (same orchestrator).
- **FR-26:** `python -m debate.test_gemini` — single-call API smoke test.

---

## 5. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Code file length | ≤ 150 lines per file (excluding blanks/comments) |
| NFR-02 | Test coverage | ≥ 85% |
| NFR-03 | Linting | Zero Ruff errors |
| NFR-04 | Package manager | `uv` + `uv.lock` (no `requirements.txt` in final submission) |
| NFR-05 | OOP design | Clear separation: models, agents, orchestrator, SDK, transport |
| NFR-06 | TDD | Unit tests in `tests/unit/`, integration in `tests/integration/` |
| NFR-07 | Documentation | PRD, PLAN, TODO, mechanism PRDs, architecture diagram, README |
| NFR-08 | Cost transparency | Prompt log + token/cost analysis in README or `docs/` |
| NFR-09 | Version tracking | Semantic doc version (1.00) aligned with submission |

---

## 6. Out of scope

- Real-time human participation in the debate.
- Direct Pro↔Con messaging channel.
- Committing API keys or `.env` to the repository.
- Cloud deployment or web hosting (local execution only).

---

## 7. Success criteria

1. Full debate completes with 10 pings/side (or 5 with documented demo mode).
2. Verdict JSON produced; logs show mediated JSON message flow.
3. Each turn includes at least one citation when search grounding is enabled.
4. `pytest` passes; Ruff clean; coverage ≥ 85% after remodel stages complete.
5. Public GitHub repo + Moodle PDF per partner with same link.
6. README contains setup (UV), screenshots, and cost/token notes.

---

## 8. References

- Exercise 02 PDF — `main-v4-Agents-Subagents-Commands.pdf`
- Software Submission Guidelines V3 — `software_submission_guidelines-V3.pdf`
- Prior feedback — `Detailed_Feedback_Report_252586.pdf`
- Mechanism PRDs: `PRD_orchestrator.md`, `PRD_gatekeeper.md`, `PRD_llm_sdk.md`
