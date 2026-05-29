# Contributing

This file answers the Software Submission Guidelines V3 §2.1
"Contribution Guidelines" requirement. The project is a course
assignment, but the workflow below is the one we'd recommend to anyone
extending the debate orchestrator.

## Team

Submitted as a pair. The work was done jointly: we paired on the
PRD/PLAN/TODO, split the orchestrator/SDK implementation work between
us on feature branches, and reviewed each other's pull requests before
merging.

| Role | Name |
| --- | --- |
| Student 1 | Renat Karimov |
| Student 2 | Alon Engel |

Repository: <https://github.com/alonengel/ai-agent-debate-rkarimov-aengel>.

## How we collaborate

- **Pair sessions, then async work.** Big design decisions (PRD,
  PLAN, ADRs, the skills overhaul, the runtime side-assignment
  protocol) are discussed face to face; smaller stretches of
  implementation happen async on feature branches off `main`.
- **Commit-per-small-change.** Every commit is a single logical step
  with a descriptive Conventional-Commits-style subject line
  (`feat:`, `refactor:`, `docs:`, `test:`, etc.). We never lump
  unrelated changes.
- **PR review before merge.** Each branch goes through a Pull Request
  on GitHub; the merge button is only pressed after the suite is
  green and the partner has reviewed.

## Setting up a dev environment

```
git clone https://github.com/alonengel/ai-agent-debate-rkarimov-aengel debate
cd debate
uv sync --extra dev
```

`uv sync` installs every runtime + dev dependency from
`pyproject.toml` into `.venv/`. There is no separate
`requirements.txt`; `uv.lock` pins exact versions for reproducibility.

Copy `.env.example` to `.env` and fill in at least one of
`GEMINI_API_KEY` or `ANTHROPIC_API_KEY` before running a real debate.

## Quality gates (run them before pushing)

```
uv run ruff check src tests scripts  # zero violations
uv run pytest --cov                  # 193 tests, fail_under = 100% on in-scope code
uv run python -m debate.main --dry-run --config config/setup.json
                                     # the CLI must still load
make cap                             # every .py file under src/tests/scripts <= 150 lines
```

The same checks are wrapped behind `make check` (see `Makefile`). A
pre-commit hook config (`.pre-commit-config.yaml`) runs ruff and the
line-cap check locally on every `git commit` after a one-time
`uv run pre-commit install`.

## Code style

- **Every Python source file <= 150 raw lines.** Hard rule from
  Guidelines V3 §5.2. If a file approaches the limit, split it (see
  ADR-006). The `scripts/check_line_cap.py` script enforces it.
- **Project-local skills only.** All Claude skills live under
  `.claude/skills/` — never global. See ADR-008.
- **Single SDK entry point for LLMs.** No business logic talks to
  `google.genai` or `anthropic` directly; everything goes through
  `sdk.llm_client.LlmClient`. See ADR-003.
- **No hardcoded debate parameters.** Topic, sides, ping count, and
  rate limits live in `config/*.json` with a top-level `"version"`
  key validated at load time. See ADR-010.
- **Refute-with-citation.** Debaters may lie, but contradicting an
  opponent's factual claim requires a real cited source in the same
  turn (rubric clause in `.claude/skills/debate-judge-rubric`).
- **Docstrings explain "why", not "what".** Public functions and
  modules need one; obvious narration goes in the code itself.

## Adding a new feature

1. Open / update the relevant document in `docs/`:
   - A new mechanism (gatekeeper variant, transport, etc.)? Add a
     `docs/PRD_<area>.md`.
   - A new architectural decision? Add it to `docs/PLAN.md` (or a
     standalone ADR file, see `docs/adr/`).
   - A new LLM prompt? Update `docs/PROMPTS.md` in the same commit.
2. Implement under `src/debate/<area>/`. If the change crosses
   process boundaries, add a command to `orchestrator/commands.py`.
3. Add tests under `tests/unit/` (and `tests/integration/` if it
   spans modules). Aim for both success and error branches.
4. Update `README.md` if the change is user-visible.
5. Run the four quality gates above. Push. Open a PR.

## Reporting issues

Open a GitHub issue with:

- A minimal reproduction (config + command + observed output).
- The package version (`uv run python -m debate.main --version`).
- The active LLM provider as reported by `--dry-run`.
- Whether the latest run on `main` passes the quality gates.
