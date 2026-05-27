# Known Limitations

> **Purpose:** document the things this project deliberately does not
> handle so reviewers and future contributors can decide whether the
> reported behaviour applies to their own use case. The README keeps a
> short summary; this file is the long form.

Every limitation below is a *design choice*, not a bug. They were
taken on knowingly to keep the project focused on the mediated-debate
architecture the assignment asks for.

## L-01: Two fixed sides per session

- **Description:** the schema in `models.py` carries exactly one
  `pro_side` and one `con_side`. The host (`host_protocol.decide_sides`)
  assigns which agent defends which at runtime, but it always assigns
  two sides — never three or more.
- **Impact:** a free-for-all "everyone defend a different film" debate
  would require schema and orchestrator changes.
- **Workaround:** out of scope for the exercise. The orchestrator
  already runs N processes (parent + 2 children) under a supervisor;
  adding a third debater would mean extending `ChannelPair`, the
  `TURN_REQUEST` round-robin in `parent_worker`, and the rubric.

## L-02: English-only

- **Description:** every prompt, skill, doc, comment and the GUI text
  is in English. The original brief notes that a Hebrew session costs
  roughly 2.5× more tokens; we chose English consciously.
- **Impact:** running with Hebrew prompts would need new translations
  of the system / turn / verdict prompts in `agents/prompts.py` and
  `agents/judge_prompts.py`, plus retranslated skill files.
- **Workaround:** the prompts are parameterised; swapping
  `prompts.py` + `judge_prompts.py` for a Hebrew variant is the only
  required code change. The rest of the pipeline is language-agnostic.

## L-03: One LLM call per turn per side

- **Description:** each agent makes exactly one LLM call per ping.
  There is no "think, then answer" two-pass strategy, and no
  per-agent sub-agent fan-out behind the scenes.
- **Impact:** the model has to do the argument-building and the
  refutation in a single response, which is harder than a multi-stage
  pipeline (planner → drafter → critic).
- **Workaround:** the SDK layer (`sdk.llm_client.LlmClient`) is the
  single LLM entry point; you can wrap it with a multi-stage
  controller without touching agents. We chose the single-call
  approach to keep token cost predictable under the gatekeeper's
  budget.

## L-04: No live human participation

- **Description:** the debate runs end-to-end without any human in the
  loop. A run produces a transcript and a JSON verdict, and that's it.
- **Impact:** humans cannot interrupt to ask the debater to clarify
  or to challenge a citation.
- **Workaround:** out of scope. The transport layer (`debate/transport/`)
  is JSON-line-based and could in principle multiplex a "human" channel,
  but neither the orchestrator nor the rubric have hooks for it.

## L-05: Web sources are not validated for live availability

- **Description:** the schema requires real http/https URLs and the
  judge penalises hallucinated sources, but no component actually
  fetches the URL to confirm it exists.
- **Impact:** a debater could cite a real-looking but dead URL and
  the judge would not catch it; it relies on the model's training-
  data fidelity.
- **Workaround:** out of scope for the course exercise. A simple
  follow-up would be a `requests.head` check inside the parsing
  layer (`agents/json_parse.py`) and a "url-unreachable" penalty in
  the rubric. We didn't ship that because flaky network access would
  make the test suite non-hermetic.

## L-06: Demo config caps at 5 pings per side

- **Description:** `config/demo_setup.json` runs at `pings_per_side =
  5` and `max_words_per_turn = 180` to fit inside the free Gemini
  tier. The default `config/setup.json` runs at 10 pings / 280 words.
- **Impact:** the demo run never reaches the rubric's "if dropped for
  two consecutive turns, the claim is conceded" full strength,
  because only 5 turns per side go on the board.
- **Workaround:** switch the config: `make run` (uses `setup.json`,
  10 pings) versus `python -m debate.main --config
  config/demo_setup.json`. The README quotes both.

## L-07: Coverage skips OS- and network-specific code paths

- **Description:** the coverage scope (`pyproject.toml` ->
  `tool.coverage.run`) omits `transport/fifo.py` (Unix-only — uses
  `os.mkfifo`), `legacy/ping_runner.py` (reference single-process
  driver), `gui/*` (Tkinter event loop), and the multiprocess
  worker entry points (`orchestrator/*_worker.py`,
  `orchestrator/supervisor*.py`). Real Gemini / Anthropic API call
  sites in `sdk/*_client.py` are exercised via mocks rather than
  network calls.
- **Impact:** the 100% number is "100% of the in-scope code", which
  is the deterministic logic. The omitted parts are covered by the
  smoke test (`python -m debate.main --dry-run`) and the manual
  full-debate runs documented in the README.
- **Workaround:** to include Unix FIFOs in coverage, drop the omit
  line for `transport/fifo.py` and run the suite on Linux/macOS; the
  existing tests parametrise the transport choice.

## L-08: Verdict tie-break is deterministic but coarse

- **Description:** if the judge LLM returns equal scores, the verdict
  builder (`agents/verdict_builder.py`) bumps the stated winner's
  score by 1. The rubric's "tie-break by higher Clash, then fewer
  dropped claims" rule is enforced inside the prompt, not as a
  separate code path.
- **Impact:** if the model emits a tie with no Clash data attached,
  we fall through to "winner +1", which is conservative but not
  rubric-perfect.
- **Workaround:** would need a second JSON field
  (`clash_pro`, `clash_con`) and a code-side tie-break.
  Not done because the prompt-level rule was empirically enough
  across our test sessions.

## L-09: Skills are project-local Markdown only

- **Description:** the seven skills under `.claude/skills/` are
  loaded by the Claude CLI when it boots a child process. They are
  not used by the Gemini path — Gemini sees only the Python-side
  prompts in `agents/prompts.py` and `agents/judge_prompts.py`.
- **Impact:** the Parent's research-backed rubric is fully captured
  in the Python prompts (so Gemini gets it too), but smaller skill
  details (e.g. CWI-S argument structure for debaters) only land in
  the Claude CLI runs.
- **Workaround:** the skill files are short and could be inlined into
  the Python prompts if you need full parity with Gemini. We kept
  them in Markdown because they are easier to iterate on as text.
