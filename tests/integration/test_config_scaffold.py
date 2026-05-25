from __future__ import annotations

from debate.config import load_config
from debate.config.loader import project_root


def test_config_json_files_load_via_loader() -> None:
    cfg = load_config()
    assert cfg.debate.pings_per_side == 10
    assert cfg.llm.gemini_model == "gemini-2.5-flash"
    assert cfg.agents.cli_command == "claude"
    assert cfg.ipc.transport_type == "file_queue"
    assert cfg.logging.log_dir == "logs"
    assert cfg.gatekeeper.enabled is True
    assert cfg.gatekeeper.max_total_requests == 200
    assert cfg.gatekeeper.max_requests_per_agent == 80


def test_demo_config_json_load() -> None:
    root = project_root()
    cfg = load_config(root / "config" / "demo_setup.json")
    assert cfg.debate.pings_per_side == 5
    assert cfg.gatekeeper.max_total_requests == 80
    assert cfg.gatekeeper.max_requests_per_agent == 30
