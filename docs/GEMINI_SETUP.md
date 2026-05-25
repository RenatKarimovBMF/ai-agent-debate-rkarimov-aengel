# Free Gemini API setup (recommended)

## Step 1 — Get a free API key

1. Open **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key (starts with `AIza...`)

No credit card is required for the free tier in most regions.

## Step 2 — Add to `.env`

In the project folder:

```powershell
copy .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=AIzaSy...your-key-here
LLM_PROVIDER=gemini
```

Leave `ANTHROPIC_API_KEY` empty unless you also want Anthropic later.

## Step 3 — Install dependencies

```powershell
uv sync --extra dev
```

If `uv` is not on PATH: `python -m uv sync --extra dev`

## Step 4 — Run

```powershell
uv run python -m debate.main --dry-run
uv run python -m debate.gui
```

The app will use **Gemini 2.0 Flash** with **Google Search** for real citations (homework requirement).

## Save money

In `config.toml` use:

```toml
pings_per_side = 5
```

Allowed by the assignment — note it in README.

## Error: `API key expired`

Google says the key in `.env` is no longer valid.

1. Go to **https://aistudio.google.com/apikey**
2. **Create API key** (new one)
3. Replace the line in `.env`: `GEMINI_API_KEY=AIza...` (new value)
4. **New terminal** → `uv run python -m debate.test_gemini`

Do not reuse an old copied key from chat or email.

## Error 429 `RESOURCE_EXHAUSTED` (quota 0)

Often means:

1. **Wrong model** — we now use `gemini-2.5-flash` first (not `2.0-flash`).
2. **Google Search** needs billing in some regions — set `use_google_search = false` in `config.toml`.
3. **Region** — free tier may be unavailable (quota shows `limit: 0`). Try a new key, VPN, or ask the lecturer.
4. **Test one call** before full debate:

```powershell
uv run python -m debate.test_gemini
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GEMINI_API_KEY not set` | Create `.env` from `.env.example` |
| `google-genai` missing | `uv sync --extra dev` |
| Rate limit / quota | Wait 1–2 min; run `test_gemini`; use 5 pings |
| Region blocked | New key at AI Studio; see lecturer |
