# Configuration

JSON configuration scaffold for Guidelines V3 compliance.

| File | Purpose |
|------|---------|
| `setup.json` | Debate, LLM, agents, IPC, and logging settings (mirrors `config.toml`) |
| `demo_setup.json` | Budget-friendly demo settings (mirrors `config.demo.toml`) |
| `rate_limits.json` | Gatekeeper limits (mirrors `[gatekeeper]` in `config.toml`) |
| `demo_rate_limits.json` | Tighter limits for demo runs |

**Runtime note:** The application still loads `config.toml` / `config.demo.toml` at the project root. Stage 6 will switch the loader to these JSON files.

Keep TOML and JSON values in sync until the migration is complete.
