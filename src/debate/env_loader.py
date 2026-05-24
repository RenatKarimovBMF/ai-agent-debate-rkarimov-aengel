"""Load .env from project root (works regardless of terminal cwd)."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_env_loaded() -> Path:
    """Always load the project .env file; override stale shell variables."""
    env_path = project_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=True)
    else:
        load_dotenv(override=True)
    return env_path


def gemini_key_hint() -> str:
    from sdk.llm_client import _env_key

    key = _env_key("GEMINI_API_KEY")
    if not key:
        return "Gemini key: NOT loaded — add GEMINI_API_KEY to .env"
    return f"Gemini key: loaded ({key[:8]}…{key[-4:]})"
