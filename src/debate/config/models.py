from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    anthropic_web_search: bool = False


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
    min_interval_ms: int = 0
    log_denials: bool = False


@dataclass(frozen=True)
class AppConfig:
    debate: DebateConfig
    llm: LlmConfig
    agents: AgentsConfig
    ipc: IpcConfig
    logging: LoggingConfig
    gatekeeper: GatekeeperConfig
    project_root: Path
