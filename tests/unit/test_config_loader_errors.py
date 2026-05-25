from __future__ import annotations

from pathlib import Path

import pytest

from debate.config.loader import (
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
