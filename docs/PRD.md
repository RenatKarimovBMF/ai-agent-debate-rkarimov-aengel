# Product Requirements Document — AI Agent Debate

**Project:** Exercise 02 — Intelligent Agents (Haifa University)  
**Version:** 1.00 (submission baseline)  
**Authors:** Renat Karimov, Alon Engel  
**Last updated:** 2026-05-27

---

## 1. Overview

Build a **mediated multi-agent debate system** in Python where three LLM-powered agents argue a fixed topic under strict orchestration rules. The system must demonstrate agent coordination, structured IPC, API budget control, and professional software engineering practices.

**Debate topic (default):** Which is the greater film — *The Godfather* (1972) or *The Shawshank Redemption* (1994)?

| Role | Agent class | Position |
|------|-------------|----------|
| Pro | `ProAgent` | Whichever side the Parent assigns at runtime |
| Con | `ConAgent` | The remaining side after Parent's assignment |
| Parent | `ParentAgent` | Host and judge (persuasion only; **no tie**) |

Sides are no longer hardcoded to a class — the Parent assigns them at the start of each session via the host-protocol skill (see FR-27 below).

---

## 2. Goals

1. Satisfy all functional requirements of Exercise 02 (§8) and the additional in-class clarifications (research-backed judging, multi-skill debaters, project-local skills, runtime side assignment, refute-with-citation, prompt log, version tracking).
2. Meet Software Submission Guidelines V3 (planning docs, SDK layer, tests, Ruff, coverage, version key in config).
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
| US-07 | Student | Separate skills per agent role | Each agent has distinct prompts and behavior |
| US-08 | Grader | Read PRD / PLAN / TODO / PROMPTS | I can assess planning and prompt design before code |
| US-09 | Grader | See sides change across runs | I can verify the Parent really assigns sides at runtime |
| US-10 | Grader | See a citation behind every refutation of a factual claim | I can verify the refute-with-citation rule is enforced |
| US-11 | Grader | See a version key in every config file | I can confirm config and code are in sync |

---

## 4. Functional requirements

### 4.1 Agents and roles

- **FR-01:** Exactly three agents in the public interface: Parent (judge/host), Pro, Con. Internal helper skills are allowed under the Parent.
- **FR-02:** Pro and Con must **never** communicate directly; all messages pass through Parent.
- **FR-03:** Each agent has dedicated project-local skills under `.claude/skills/` (no global skills). Debaters share two generic skills (`debate-argument-builder`, `debate-rebuttal-strategist`) and one side-specific lore skill (`debate-pro-godfather` or `debate-con-shawshank`).
- **FR-04:** Parent delivers a final **verdict** with winner, scores, and rationale (no tie allowed). Verdict reasoning must reference at least one of the five judging principles from `.claude/skills/debate-parent-judge`.

### 4.2 Debate flow

- **FR-05:** Default **10 pings per side** (configurable; 5 allowed with README justification, used by the demo config).
- **FR-06:** Turn order: Parent requests Pro → Pro responds → Parent relays to Con → Con responds → Parent relays to Pro → repeat.
- **FR-07:** Each turn includes structured text and **citations** (title + URL).
- **FR-08:** Session ends with verdict written to `logs/verdict_<session_id>.json`.

### 4.3 Message protocol

- **FR-09:** All IPC uses **JSON** (`DebateMessage`, `VerdictMessage` in `debate.models`).
- **FR-10:** Message types: `turn`, `relay`, `verdict`, `keepalive`, `error`, `assign`.
- **FR-11:** Schema version field (`version: "1.0"`) on all messages.

### 4.4 Orchestration

- **FR-12:** Python orchestrator (not CLI-only) controls the full debate lifecycle.
- **FR-13:** **Multiprocess architecture:** supervisor + three worker processes (Parent, Pro, Con) using `multiprocessing.Queue` (Windows-safe `spawn`).
- **FR-14:** Legacy single-process `DebateOrchestrator` retained for tests/reference.

### 4.5 LLM access

- **FR-15:** All LLM calls go through the **SDK layer** (`sdk.llm_client.LlmClient`).
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
- **FR-29:** Every JSON config file declares a top-level `"version": "1.00"` key. The loader hard-fails when the key is missing and warns on mismatch against `debate._version.__version__`.

### 4.8 Entry points

- **FR-24:** `python -m debate.main` — primary CLI entry. Supports `--version`, `--dry-run`, `--gui`, and topic overrides.
- **FR-25:** `python -m debate.gui` — optional GUI (same orchestrator).
- **FR-26:** `python -m debate.test_gemini` — single-call API smoke test.

### 4.9 Skills, judging, and debate rules

- **FR-27:** **Runtime side assignment.** The Parent picks which class defends which side at session start using `debate.orchestrator.host_protocol.decide_sides`, which is deterministic per `session_id` but varies across sessions. Side strings travel to children in an `ASSIGN` command before any turn request.
- **FR-28:** **Refute-with-citation rule.** Both debaters are permitted to lie as a test of persuasion skill. However, a debater who alleges that a factual claim by the opponent is false must include a real cited source in the same turn. A bare contradiction does not count as a refutation and is penalised in the judge's Clash score (see `.claude/skills/debate-judge-rubric`).
- **FR-30:** **Research-backed judging.** The Parent's rubric and the five judging principles are documented in `docs/PRD_judge_rubric.md` and `.claude/skills/debate-judge-rubric`, drawing on WUDC, IDEA, NSDA and Alfred Snider's published criteria.
- **FR-31:** **Personalised host opening.** At session start the Parent delivers an individual briefing to each child (boxing-referee protocol: side, opponent, word cap, refute-with-citation rule, signal to start). See `.claude/skills/debate-host-protocol`.

---

## 5. Non-functional requirements

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-01 | Code file length | ≤ 150 raw lines per file (Guidelines V3 §5.2; strict count) | met (largest: `config/loader.py` at 138) |
| NFR-02 | Test coverage | ≥ 85% | met (100% on in-scope code; 185 unit tests; coverage gate `fail_under = 100`) |
| NFR-03 | Linting | Zero Ruff errors | met |
| NFR-04 | Package manager | `uv` + `uv.lock` (no `requirements.txt`) | met |
| NFR-05 | OOP design | Clear separation: models, agents, orchestrator, SDK, transport | met |
| NFR-06 | TDD | Unit tests in `tests/unit/`, integration in `tests/integration/` | met (185 unit tests at v1.00) |
| NFR-07 | Documentation | PRD, PLAN, TODO, PROMPTS, mechanism PRDs, architecture diagram, README | met |
| NFR-08 | Cost transparency | Prompt log (`docs/PROMPTS.md`) + token/cost notes in README | met |
| NFR-09 | Version tracking | `__version__` in code + `"version"` in every JSON config, validated on load | met |
| NFR-10 | English-only project content | All code, comments, prompts and docs in English | met |

---

## 6. Out of scope

- Real-time human participation in the debate.
- Direct Pro↔Con messaging channel.
- Committing API keys or `.env` to the repository.
- Cloud deployment or web hosting (local execution only).
- Hebrew-language UI or prompts (cost optimisation; the system is English-only).

---

## 7. Success criteria

1. Full debate completes with 10 pings/side (or 5 with documented demo mode).
2. Verdict JSON produced; logs show mediated JSON message flow.
3. Each turn includes at least one citation when search grounding is enabled.
4. Across two independent runs, the side assigned to PRO can differ — proving the assignment is runtime, not hardcoded.
5. The verdict's `persuasion_notes` references at least one of the five judging principles.
6. `pytest` passes; Ruff clean; coverage ≥ 85%.
7. Public GitHub repo + Moodle PDF per partner with same link.
8. README contains setup (UV), screenshots, and cost/token notes.

---

## 8. References

- Exercise 02 PDF — `main-v4-Agents-Subagents-Commands.pdf`
- Software Submission Guidelines V3 — `software_submission_guidelines-V3.pdf`
- Prior feedback — `Detailed_Feedback_Report_252586.pdf`
- Mechanism PRDs: `PRD_orchestrator.md`, `PRD_gatekeeper.md`, `PRD_llm_sdk.md`, `PRD_judge_rubric.md`
- Prompt book: `PROMPTS.md`
- Skills (project-local): `.claude/skills/debate-parent-judge`, `debate-host-protocol`, `debate-judge-rubric`, `debate-argument-builder`, `debate-rebuttal-strategist`, `debate-pro-godfather`, `debate-con-shawshank`
