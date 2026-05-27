"""Targeted branch coverage for `debate.config.loader` and `debate.env_loader`.

Covers directory-vs-file resolution, missing rate-limit files, and the
key-hint helpers used by the CLI dry-run path.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from debate.config.loader import (
    load_config as loader_load_config,
)
from debate.config.loader import (
    resolve_setup_path,
)
from debate.env_loader import ensure_env_loaded, gemini_key_hint


def test_resolve_setup_path_with_directory(tmp_path: Path):
    target = tmp_path / "config"
    target.mkdir()
    result = resolve_setup_path(tmp_path, target)
    assert result == target / "setup.json"


def test_load_config_missing_rate_limits_raises(tmp_path: Path):
    setup = tmp_path / "setup.json"
    setup.write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Rate limits config not found"):
        loader_load_config(setup)


def test_ensure_env_loaded_without_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "debate.env_loader.project_root", lambda: tmp_path / "nowhere"
    )
    with patch("debate.env_loader.load_dotenv") as mock_load:
        env_path = ensure_env_loaded()
    mock_load.assert_called_once_with(override=True)
    assert env_path.name == ".env"


def test_gemini_key_hint_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    hint = gemini_key_hint()
    assert "NOT loaded" in hint


def test_gemini_key_hint_with_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    hint = gemini_key_hint()
    assert "loaded" in hint and "..." not in hint
