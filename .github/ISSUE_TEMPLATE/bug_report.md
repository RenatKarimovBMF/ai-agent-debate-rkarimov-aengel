---
name: Bug report
about: Something the project does that contradicts the README or the docs.
title: "[bug] "
labels: bug
assignees: ""
---

## What happened

<!-- A clear, one-paragraph description of the actual behaviour. Quote
the exact error message or the misleading output (the verdict JSON, a
log line from `logs/debate.jsonl`, etc.). -->

## What you expected

<!-- What the README, docs/, or your reading of the code led you to
expect instead. -->

## Reproduction

1. Environment

   - OS / shell:
   - Python version: `python -V`
   - Project version: `uv run python -m debate.main --version`
   - LLM provider used (Gemini / Anthropic / Claude CLI):

2. Steps

   ```bash
   # the exact commands you ran
   ```

3. Config (only if it differs from `config/setup.json`)

   ```json
   // paste the relevant sections from setup.json or rate_limits.json
   ```

## Logs / output

```
# paste the full terminal output, including any traceback
```

If `logs/debate.jsonl` has a relevant entry, paste the offending
line(s) here as well.

## Additional context

<!-- Branch, recent commit hash, related issues, screenshots, etc. -->
