# Claude CLI setup (recommended)

Running the debate through the **Claude CLI** uses your **Claude Pro/Max
subscription** instead of a pay-per-call API key — the highest-fidelity
option and the one used for the worked example in `examples/`. The auto
priority is `claude_cli → anthropic → gemini`, so once the CLI is
installed and logged in it is selected automatically.

## Step 1 — Install the Claude Code CLI

Requires Node.js (`node --version` to check; install from
https://nodejs.org if missing). Then:

```powershell
npm install -g @anthropic-ai/claude-code
claude --version
```

## Step 2 — Log in with your subscription

Run the CLI once interactively:

```powershell
claude
```

On first launch, choose **"Claude account with subscription"** (the
Pro/Max option, *not* the API-key option) and complete the browser
login. This bills against your subscription, with no per-call charge.
Type `/exit` when done.

## Step 3 — Point the project at it

```powershell
copy .env.example .env
```

Edit `.env` (no API key needed):

```env
LLM_PROVIDER=claude_cli
```

If `claude` is not on your PATH, set `CLAUDE_CLI_PATH` to its full path.

## Step 4 — Install dependencies and run

```powershell
uv sync --extra dev
uv run python -m debate.main --dry-run      # should print: LLM provider: claude_cli
uv run python -m debate.main --config config/setup.json
```

## Usage and limits

There is **no per-call charge** — usage counts against Claude's rolling
limits. A full 10-ping debate (21 calls) used roughly **under 10% of the
5-hour window** and **~1% of the weekly allowance** on a Claude Pro plan,
so you can run many debates per month. If you hit a limit, wait for the
window to reset or run the 5-ping demo (`config/demo_setup.json`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `'claude' is not recognized` | Install the CLI (Step 1); open a new terminal so PATH refreshes |
| `--dry-run` shows a different provider | Set `LLM_PROVIDER=claude_cli` in `.env`, or check `claude --version` works |
| Auth / login errors | Re-run `claude` and pick the subscription login; confirm with `claude -p "say OK"` |
| Windows `WinError 2` | Update to the current code — the client resolves the `claude.cmd` shim via `shutil.which` |
