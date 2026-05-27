from __future__ import annotations

import json
from pathlib import Path

import pytest

from debate._version import EXPECTED_CONFIG_VERSION
from debate.config.loader import (
    _validate_config_version,
    load_config,
    project_root,
    resolve_rate_limits_path,
    resolve_setup_path,
)


def test_resolve_setup_path_defaults():
    root = project_root()
    assert resolve_setup_path(root, None) == root / "config" / "setup.json"


def test_resolve_rate_limits_demo_pair():
    setup = Path("config/demo_setup.json")
    assert resolve_rate_limits_path(setup).name == "demo_rate_limits.json"


def test_load_config_missing_setup(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="Setup config not found"):
        load_config(missing)


def test_validate_config_version_accepts_expected():
    _validate_config_version({"version": EXPECTED_CONFIG_VERSION}, Path("dummy"))


def test_validate_config_version_missing_key_raises():
    with pytest.raises(ValueError, match="missing required 'version' key"):
        _validate_config_version({}, Path("dummy"))


def test_validate_config_version_mismatch_warns(caplog):
    with caplog.at_level("WARNING", logger="debate.config"):
        _validate_config_version({"version": "0.42"}, Path("dummy"))
    assert any("version mismatch" in record.message.lower() for record in caplog.records)


def test_load_config_rejects_setup_without_version(tmp_path):
    setup = tmp_path / "setup.json"
    rate = tmp_path / "rate_limits.json"

    setup.write_text(
        json.dumps(
            {
                "debate": {
                    "topic": "t",
                    "pro_side": "p",
                    "con_side": "c",
                    "language": "en",
                    "pings_per_side": 1,
                    "max_words_per_turn": 10,
                    "request_timeout_seconds": 1,
                    "keepalive_interval_seconds": 1,
                },
                "llm": {"gemini_model": "m"},
                "agents": {"cli_command": "claude", "workdir": "."},
                "ipc": {
                    "fifo_dir": "fifo",
                    "transport_type": "file_queue",
                    "pro_to_parent": "a",
                    "con_to_parent": "b",
                    "parent_to_pro": "c",
                    "parent_to_con": "d",
                },
                "logging": {
                    "log_dir": "logs",
                    "max_files": 1,
                    "max_lines_per_file": 1,
                    "level": "INFO",
                },
            }
        ),
        encoding="utf-8",
    )
    rate.write_text(
        json.dumps(
            {
                "version": EXPECTED_CONFIG_VERSION,
                "enabled": False,
                "max_total_requests": 1,
                "max_requests_per_agent": 1,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required 'version' key"):
        load_config(setup)
