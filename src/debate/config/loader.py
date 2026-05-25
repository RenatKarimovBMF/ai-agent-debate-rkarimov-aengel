from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from debate.config.models import (
    AgentsConfig,
    AppConfig,
    DebateConfig,
    GatekeeperConfig,
    IpcConfig,
    LlmConfig,
    LoggingConfig,
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_setup_path(root: Path, path: Path | None) -> Path:
    if path is None:
        return root / "config" / "setup.json"

    if path.is_dir():
        return path / "setup.json"

    return path


def resolve_rate_limits_path(setup_path: Path) -> Path:
    config_dir = setup_path.parent

    if setup_path.name == "demo_setup.json":
        return config_dir / "demo_rate_limits.json"

    return config_dir / "rate_limits.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_app_config(
    setup: dict[str, Any],
    rate_limits: dict[str, Any],
    root: Path,
) -> AppConfig:
    llm_raw = setup["llm"]
    fallbacks = llm_raw.get("gemini_model_fallbacks", [])

    return AppConfig(
        debate=DebateConfig(**setup["debate"]),
        llm=LlmConfig(
            gemini_model=llm_raw["gemini_model"],
            gemini_model_fallbacks=tuple(fallbacks),
            use_google_search=bool(llm_raw.get("use_google_search", False)),
        ),
        agents=AgentsConfig(**setup["agents"]),
        ipc=IpcConfig(**setup["ipc"]),
        logging=LoggingConfig(**setup["logging"]),
        gatekeeper=GatekeeperConfig(
            enabled=bool(rate_limits["enabled"]),
            max_total_requests=int(rate_limits["max_total_requests"]),
            max_requests_per_agent=int(rate_limits["max_requests_per_agent"]),
            min_interval_ms=int(rate_limits.get("min_interval_ms", 0)),
            log_denials=bool(rate_limits.get("log_denials", False)),
        ),
        project_root=root,
    )


def load_config(path: Path | None = None) -> AppConfig:
    root = project_root()
    setup_path = resolve_setup_path(root, path)
    rate_path = resolve_rate_limits_path(setup_path)

    if not setup_path.is_file():
        raise FileNotFoundError(f"Setup config not found: {setup_path}")

    if not rate_path.is_file():
        raise FileNotFoundError(f"Rate limits config not found: {rate_path}")

    setup = _read_json(setup_path)
    rate_limits = _read_json(rate_path)
    return _build_app_config(setup, rate_limits, root)


def with_custom_debate(
    config: AppConfig,
    *,
    pro_side: str,
    con_side: str,
    topic: str,
) -> AppConfig:
    """Apply runtime topic overrides without editing config files."""
    debate = replace(
        config.debate,
        pro_side=pro_side.strip(),
        con_side=con_side.strip(),
        topic=topic.strip(),
    )
    return replace(config, debate=debate)
