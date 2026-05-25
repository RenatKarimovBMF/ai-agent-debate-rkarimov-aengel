from __future__ import annotations

from debate.config import load_config
from debate.env_loader import ensure_env_loaded, gemini_key_hint, project_root
from debate.logging_setup import RotatingJsonlHandler, setup_logging


def test_project_root_exists():
    root = project_root()
    assert (root / "pyproject.toml").is_file()


def test_ensure_env_loaded(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test-key-value\n", encoding="utf-8")
    monkeypatch.setattr("debate.env_loader.project_root", lambda: tmp_path)

    path = ensure_env_loaded()
    assert path == env_file


def test_gemini_key_hint_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert "NOT loaded" in gemini_key_hint()


def test_setup_logging_and_json_handler(tmp_path):
    from dataclasses import replace

    config = load_config()
    logging_cfg = replace(
        config.logging,
        log_dir=str(tmp_path / "logs"),
        max_lines_per_file=2,
    )

    logger = setup_logging(logging_cfg)
    logger.info("line-one", extra={"extra_data": {"k": "v"}})
    logger.info("line-two")
    logger.info("line-three")

    files = list((tmp_path / "logs").glob("*.jsonl"))
    assert files

    handler = next(h for h in logger.handlers if isinstance(h, RotatingJsonlHandler))
    handler.close()
