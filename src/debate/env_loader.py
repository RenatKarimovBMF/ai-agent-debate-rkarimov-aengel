"""Load .env from project root (works regardless of terminal cwd)."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def find_project_root(fallback: Path) -> Path:
    """Return the directory that holds the project files.

    Prefer the working directory (or an ancestor) that contains both
    `pyproject.toml` and `config/setup.json`, so logs and verdicts land
    next to `config/` even when the package runs from an installed copy
    in site-packages (where a file-relative path resolves into
    `.venv/Lib`). Falls back to `fallback` when no marker is found.
    """
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        has_pyproject = (candidate / "pyproject.toml").is_file()
        has_config = (candidate / "config" / "setup.json").is_file()
        if has_pyproject and has_config:
            return candidate
    return fallback


def project_root() -> Path:
    return find_project_root(Path(__file__).resolve().parents[2])


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
