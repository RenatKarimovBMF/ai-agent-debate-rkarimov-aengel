# Prompt Book — AI Agent Debate v1.00

This document is the single source of truth for every LLM-facing prompt
in the project. The course guidelines (§7.4 of the software-submission
spec) require us to publish the prompts we use, justify them, and track
how they evolved. Keep this file in sync with the code: when a prompt
changes, update the matching section here in the same commit.

## How prompts flow through the system

1. **Skills (Markdown)** in `.claude/skills/` are the long-form
   playbooks. They describe *what* each agent is, what rules it follows,
   and the rubric the judge uses. They are loaded by the Claude CLI when
   it boots a child process.
2. **System prompts (Python)** in `src/debate/agents/prompts.py` and
   `src/debate/agents/parent_agent.py` are the short, machine-checked
   contracts. They restate the rules in the form the LLM must obey to
   produce valid JSON we can parse.
3. **Turn prompts (Python)** are issued every ping. They carry the
   opponent's last utterance and re-enforce the JSON output contract,
   which the model otherwise tends to drop after a few turns.

Every prompt below is written so the model can stay in role even if the
skill file is stripped from its context window — defence-in-depth, not
just decoration.

## 1. Debater system prompt

- **Code**: `debater_prompt()` in `src/debate/agents/prompts.py`
- **Audience**: PRO and CON child agents at session start, before any
  turn is requested.
- **Skill files it pairs with**:
  `.claude/skills/debate-argument-builder/SKILL.md` (positive case
  scaffolding), `.claude/skills/debate-rebuttal-strategist/SKILL.md`
  (refutation rules), and one of the two lore skills
  (`debate-pro-godfather` or `debate-con-shawshank`) depending on the
  side the host assigns.

### Why each block is there

- **`Your assigned side` / `Opponent's assigned side`** — repeats the
  assignment the host sent in the `ASSIGN` command. The model would
  otherwise lean on `pro_side`/`con_side` from `setup.json` and lock to
  the same side every run, which contradicts the dynamic-assignment
  requirement.
- **No-concede / no-side-switch** — early experiments showed Claude
  drifting into "actually I see the other side" centrism after about
  ping 6. Phrasing it as a single negative rule kept turns adversarial.
- **Refutation-with-citation** — the central rule from the exercise
  spec. Lying is allowed *as content*, but accusing the opponent of
  lying without a citation gets penalised by the judge. Keeping the
  rule in both the skill file *and* the system prompt is intentional
  redundancy: the JSON parser cannot catch a bare "that's false", but
  the prompt makes the model self-police.
- **JSON output rules** — the model used to wrap output in triple
  backticks roughly 30 % of the time. Listing the negative cases
  (`Do not wrap...`, `Do not use triple backticks...`) eliminated
  almost all of those failures in our test runs.

### Lessons learned

- Single-paragraph system prompts under-perform on Gemini's small
  models — bulleting the rules raised parse success noticeably.
- Asking for "valid JSON" is too weak; we now show the literal schema
  so the model has a target to imitate.

## 2. Debater turn prompt

- **Code**: `turn_prompt()` in `src/debate/agents/prompts.py`
- **Audience**: PRO and CON child agents, once per ping.

### Why each block is there

- **Ping number** — the model uses it to pace itself (e.g. avoid
  spending its strongest argument on ping 1 when there are 10 pings).
- **`This is the opening statement` branch** — opening turns have no
  opponent text to react to, so we explicitly tell the model to define
  its value standard for "greater" first. Without this, the opening
  turns were 60 % filler.
- **Repeat the JSON schema** — Claude (and especially Gemini Flash)
  forget the JSON contract by ping 5 or 6 if you do not repeat it. Two
  lines of repetition saved us many retries.

### Lessons learned

- Telling the model "start with a direct rebuttal" is far more
  effective than "address the opponent's arguments". The verb matters.
- We tried sending the opponent's *citations* in the prompt as well,
  but Claude started parroting them as its own. We now send only the
  opponent's text, never their URLs.

## 3. Host opening address

- **Code**: `host_opening_address()` in `src/debate/agents/prompts.py`
- **Audience**: PRO and CON children, exactly once per session, before
  any turn.
- **Skill file**: `.claude/skills/debate-host-protocol/SKILL.md`

The host briefing is modelled on a boxing referee's pre-fight talk
(per the course brief). It is short on purpose — its job is to
*hand the child its assignment* and the rules of engagement. Anything
longer dilutes the system prompt.

### Why each line is there

- **`{role} corner`** — labels the agent (PRO or CON) so the assignment
  is unambiguous in transcripts.
- **`Your side` / `Opponent's side`** — the runtime assignment from
  `host_protocol.decide_sides`. This is the only place these strings
  enter the model's context for that session.
- **`Word cap per turn`** — gives the model a hard ceiling; over-runs
  are penalised in the Manner section of the rubric.
- **`You speak only through me`** — re-states the mediated-debate
  invariant so the model never tries to address the opponent directly,
  which would break the transport layer.
- **`Touch gloves`** — explicit start signal, so the model does not
  pre-emptively launch into a turn before ping 1 arrives.

## 4. Parent / Judge system prompt

- **Code**: `ParentAgent.system_prompt()` in
  `src/debate/agents/parent_agent.py`
- **Audience**: the judge LLM whenever the orchestrator boots a parent
  worker.
- **Skill files it pairs with**:
  `.claude/skills/debate-parent-judge/SKILL.md` (philosophy),
  `.claude/skills/debate-judge-rubric/SKILL.md` (rubric),
  `.claude/skills/debate-host-protocol/SKILL.md` (host duties).

### Why each block is there

- **`PRO defends: {pro_side}` / `CON defends: {con_side}`** — the
  runtime assignment again. The judge MUST see the same assignment the
  debaters received, otherwise the verdict's rationale references the
  wrong side.
- **`The sides were assigned by you at runtime — they are not facts
  about the world`** — without this line, smaller models default to
  "Godfather is obviously better, so PRO wins". This sentence forces
  them to judge persuasion, not popularity.
- **Five judging principles** — paraphrased from the rubric skill so
  the rules survive even if the skill file is not loaded into context.
- **`No tie. Scores must differ`** — hard rule from the exercise brief.
  We re-state it in the JSON section so the parser-facing contract is
  also explicit.

### Lessons learned

- We initially asked for a `winner` field only; Gemini occasionally
  responded with prose alongside the JSON. Adding `pro_score` and
  `con_score` (and the strict-inequality rule) anchored the model to a
  JSON-shaped answer.

## 5. Verdict prompt

- **Code**: `ParentAgent.render_verdict()` in
  `src/debate/agents/parent_agent.py`
- **Audience**: the parent LLM, once, at end of session.

This is the prompt the judge sees with the full transcript stitched in.
It is intentionally longer than the per-turn prompts because the verdict
is a one-shot decision with no retries on content (only on JSON shape).

### Why each block is there

- **Rubric reminder (Matter 30 / Manner 15 / Method 15 / Clash 25 /
  Burden 15)** — explicit weights stop the model from inventing its own
  ad-hoc scoring scheme. Sum-to-100 makes the result comparable across
  runs.
- **Five principles, repeated** — yes, they are also in the system
  prompt. Repeating them next to the transcript ensures the model
  applies them while looking at the evidence, not just at session
  start.
- **Tie-breaking instruction** — must be explicit, otherwise the model
  emits equal scores about 1-in-8 times and we have to repair the
  verdict downstream.
- **`persuasion_notes must reference at least one of the five
  principles above`** — gives the judge a forcing function to actually
  *use* the principles in its rationale, which makes the verdict
  auditable.

### Lessons learned

- Sending the last 80 history items keeps the prompt under Gemini
  Flash's window even for long debates. Earlier we sent all turns and
  saw token-budget errors.
- We added the tie-break-by-clash rule after a real session produced
  81 vs 81; the post-hoc repair (`_build_verdict_message`) catches the
  remaining edge cases in code.

## 6. JSON output contract

Every prompt that expects a structured response shares the same
JSON-shape clauses:

```
- Output exactly one JSON object.
- Do not wrap the JSON in markdown.
- Do not use triple backticks.
- Escape every quote inside strings.
- Do not put raw newlines inside JSON strings.
```

The schemas:

- **Debater turn**:
  `{"text": "...", "citations": [{"title": "...", "url": "https://..."}]}`
- **Judge verdict**:
  `{"winner": "pro" | "con", "pro_score": <0-100>, "con_score": <0-100>, "rationale": "...", "persuasion_notes": "..."}`

The schemas are parsed by `debate.parsing` (debaters) and
`debate.agents.verdict_llm` (judge). When a model emits invalid JSON,
the SDK retries up to N times before raising a `LlmError`, which the
orchestrator escalates to the watchdog.

## 7. Iteration history (selected)

| Date (commit) | Prompt | Change | Why |
|---|---|---|---|
| init | debater_prompt | hard-coded PRO/CON strings | first draft, sides were also hard-coded |
| skills overhaul | debater_prompt | switched to `own_side`/`opponent_side` placeholders | sides now assigned at runtime |
| refutation rule | debater_prompt + turn_prompt | added "refute with citation" clause | exercise rule: refuting a falsehood requires a cited source |
| judge upgrade | parent_agent.system_prompt | added five judging principles + rubric reference | grounding judge in research-backed methodology |
| verdict tuning | render_verdict | added "persuasion_notes must reference one of the five principles" | force auditable rationale |

## 8. Adding or changing a prompt

1. Edit the prompt in `src/debate/agents/*.py`.
2. Update the matching section in this file.
3. Add or update a unit test in `tests/unit/` that asserts the prompt
   still contains the load-bearing keywords (e.g. the citation rule).
4. Bump the version in `_version.py` and the four JSON config files
   when the change is user-visible.
