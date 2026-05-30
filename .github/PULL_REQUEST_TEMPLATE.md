# Pull Request

## Summary

<!-- 1-3 bullets: what changed and why. Link the relevant docs/ ADR if
the design itself moved (PRD.md / PLAN.md / docs/adr/). -->

-

## Type of change

- [ ] feat: new behaviour visible from the CLI / GUI / SDK
- [ ] fix: bug fix (please describe the failure mode)
- [ ] refactor: no behaviour change
- [ ] docs: docs / comments only
- [ ] test: tests only
- [ ] chore: tooling / CI / dependencies / packaging
- [ ] skills: changes to `.claude/skills/` only

## Local quality gates

Run before opening the PR:

```bash
uv run ruff check src tests scripts
uv run mypy src
uv run pytest --cov
uv run python scripts/check_line_cap.py
```

- [ ] `ruff check` is clean.
- [ ] `mypy src` is clean.
- [ ] `pytest --cov` exits 0; coverage stays at 100% (omit list empty).
- [ ] Every `.py` file under `src/`, `tests/`, `scripts/` is at most
      150 raw lines (PRD NFR-01).
- [ ] No Hebrew text was introduced (NFR-10).

## Documentation

- [ ] README updated if a CLI flag, GUI control, or visible artifact
      changed.
- [ ] PRD / PLAN / TODO updated if the design moved.
- [ ] `CHANGELOG.md` `[Unreleased]` updated with the change.
- [ ] A new ADR was added under `docs/adr/` if an architectural
      decision was taken.

## Notes for reviewer

<!-- Anything reviewers should look at first. Screenshots from a live
debate, the verdict JSON, log excerpts, or "I'd like a second opinion
on X" pointers go here. -->
