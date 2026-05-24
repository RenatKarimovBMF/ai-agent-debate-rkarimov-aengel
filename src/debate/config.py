from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass(frozen=True)
class DebateConfig:
    topic: str
    pro_side: str
    con_side: str
    language: str
    pings_per_side: int
    max_words_per_turn: int
    request_timeout_seconds: int
    keepalive_interval_seconds: int


@dataclass(frozen=True)
class LlmConfig:
    gemini_model: str
    gemini_model_fallbacks: tuple[str, ...]
    use_google_search: bool


@dataclass(frozen=True)
class AgentsConfig:
    cli_command: str
    workdir: str


@dataclass(frozen=True)
class IpcConfig:
    fifo_dir: str
    pro_to_parent: str
    con_to_parent: str
    parent_to_pro: str
    parent_to_con: str
    transport_type: str = "file_queue"


@dataclass(frozen=True)
class LoggingConfig:
    log_dir: str
    max_files: int
    max_lines_per_file: int
    level: str


@dataclass(frozen=True)
class GatekeeperConfig:
    enabled: bool
    max_total_requests: int
    max_requests_per_agent: int


@dataclass(frozen=True)
class AppConfig:
    debate: DebateConfig
    llm: LlmConfig
    agents: AgentsConfig
    ipc: IpcConfig
    logging: LoggingConfig
    gatekeeper: GatekeeperConfig
    project_root: Path


def load_config(path: Path | None = None) -> AppConfig:
    root = Path(__file__).resolve().parents[2]
    config_path = path or (root / "config.toml")
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))

    debate = DebateConfig(**raw["debate"])

    llm_raw = raw["llm"]
    fallbacks = llm_raw.get("gemini_model_fallbacks", [])
    llm = LlmConfig(
        gemini_model=llm_raw["gemini_model"],
        gemini_model_fallbacks=tuple(fallbacks),
        use_google_search=bool(llm_raw.get("use_google_search", False)),
    )

    agents = AgentsConfig(**raw["agents"])
    ipc = IpcConfig(**raw["ipc"])
    logging_cfg = LoggingConfig(**raw["logging"])
    gatekeeper = GatekeeperConfig(**raw["gatekeeper"])

    return AppConfig(
        debate=debate,
        llm=llm,
        agents=agents,
        ipc=ipc,
        logging=logging_cfg,
        gatekeeper=gatekeeper,
        project_root=root,
    )


def with_custom_debate(
    config: AppConfig,
    *,
    pro_side: str,
    con_side: str,
    topic: str,
) -> AppConfig:
    """Apply runtime topic overrides without editing config.toml."""
    debate = replace(
        config.debate,
        pro_side=pro_side.strip(),
        con_side=con_side.strip(),
        topic=topic.strip(),
    )
    return replace(config, debate=debate)