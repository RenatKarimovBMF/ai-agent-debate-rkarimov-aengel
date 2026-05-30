"""Quick one-call Gemini test. Run: uv run python scripts/manual_gemini_check.py

Manual API-check script (not library code, not covered by the test
suite). It calls the real Gemini API, so it is kept out of the coverage
``source`` tree and excluded from automated runs.
"""

from __future__ import annotations

import sys

from debate.config import load_config
from debate.env_loader import ensure_env_loaded
from sdk.gemini_client import GeminiAgentClient


def main() -> int:
    ensure_env_loaded()
    cfg = load_config()
    print(f"Primary model: {cfg.llm.gemini_model}")
    print(f"Fallbacks: {cfg.llm.gemini_model_fallbacks}")
    print(f"Google Search: {cfg.llm.use_google_search}")

    client = GeminiAgentClient(
        model=cfg.llm.gemini_model,
        fallback_models=cfg.llm.gemini_model_fallbacks,
        use_google_search=cfg.llm.use_google_search,
    )
    try:
        r = client.prompt(
            "You are a helpful assistant.",
            'Reply with JSON only: {"status": "ok", "message": "Gemini works"}',
        )
        print("SUCCESS:")
        print(r.text[:500])
        return 0
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
