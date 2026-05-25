from __future__ import annotations

import json
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_config_json_scaffold_matches_toml_sections() -> None:
    root = _project_root()
    setup = json.loads((root / "config" / "setup.json").read_text(encoding="utf-8"))
    rate_limits = json.loads((root / "config" / "rate_limits.json").read_text(encoding="utf-8"))

    assert setup["debate"]["pings_per_side"] == 10
    assert setup["llm"]["gemini_model"] == "gemini-2.5-flash"
    assert setup["agents"]["cli_command"] == "claude"
    assert setup["ipc"]["transport_type"] == "file_queue"
    assert setup["logging"]["log_dir"] == "logs"

    assert rate_limits["enabled"] is True
    assert rate_limits["max_total_requests"] == 200
    assert rate_limits["max_requests_per_agent"] == 80


def test_demo_config_json_scaffold() -> None:
    root = _project_root()
    demo_setup = json.loads((root / "config" / "demo_setup.json").read_text(encoding="utf-8"))
    demo_limits = json.loads((root / "config" / "demo_rate_limits.json").read_text(encoding="utf-8"))

    assert demo_setup["debate"]["pings_per_side"] == 5
    assert demo_limits["max_total_requests"] == 80
    assert demo_limits["max_requests_per_agent"] == 30
