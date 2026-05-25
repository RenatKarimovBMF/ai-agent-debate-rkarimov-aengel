# Configuration

All runtime settings live in JSON under `config/` (Guidelines V3).

| File | Purpose |
|------|---------|
| `setup.json` | Debate, LLM, agents, IPC, and logging |
| `demo_setup.json` | Budget-friendly demo (5 pings) |
| `rate_limits.json` | Gatekeeper limits for full runs |
| `demo_rate_limits.json` | Tighter gatekeeper limits for demo runs |

Gatekeeper fields in `rate_limits.json`:

| Field | Description |
|-------|-------------|
| `enabled` | Master on/off switch |
| `max_total_requests` | Per-process global cap |
| `max_requests_per_agent` | Per-process cap per role |
| `min_interval_ms` | Minimum wait between LLM calls (0 = no wait) |
| `log_denials` | Log structured warnings when a call is denied |

## Loading

Default (full mode):

```powershell
uv run python -m debate.main
```

Loads `config/setup.json` + `config/rate_limits.json`.

Demo mode:

```powershell
uv run python -m debate.main --config config/demo_setup.json
```

Loads `config/demo_setup.json` + `config/demo_rate_limits.json` automatically.

## Editing

- **10 pings / full budget:** edit `setup.json` and `rate_limits.json`
- **5 pings / demo:** edit `demo_setup.json` and `demo_rate_limits.json`

No hardcoded debate parameters in Python source files.
