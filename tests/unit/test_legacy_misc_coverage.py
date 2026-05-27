"""Targeted branch coverage for assorted helpers without their own
dedicated coverage file: `legacy.helpers`, `legacy.setup`,
`models.message_from_dict`, `gatekeeper.denial_log`, and `Watchdog`.
"""

from __future__ import annotations

import logging
import time as _time

from debate.config import load_config
from debate.gatekeeper.denial_log import log_denial
from debate.legacy.helpers import short_text
from debate.legacy.setup import clear_ipc_queues
from debate.models import (
    AgentRole,
    DebateMessage,
    VerdictMessage,
    VerdictPayload,
    message_from_dict,
)
from debate.watchdog import Watchdog

from ._coverage_helpers import make_message


def test_short_text_truncates_in_legacy_helper():
    long = "word " * 400
    result = short_text(long, limit=20)
    assert result.endswith("...")
    assert len(result) <= 23


def test_short_text_keeps_short_input():
    assert short_text("hi there") == "hi there"


def test_clear_ipc_queues_removes_files(tmp_path):
    cfg = load_config()
    fifo_dir = tmp_path / cfg.ipc.fifo_dir
    fifo_dir.mkdir(parents=True, exist_ok=True)
    (fifo_dir / "stale.queue").write_text("stale", encoding="utf-8")
    (fifo_dir / ".gitkeep").write_text("", encoding="utf-8")

    cfg_with_root = cfg.__class__(
        debate=cfg.debate,
        llm=cfg.llm,
        agents=cfg.agents,
        ipc=cfg.ipc,
        logging=cfg.logging,
        gatekeeper=cfg.gatekeeper,
        project_root=tmp_path,
    )
    clear_ipc_queues(cfg_with_root)
    assert not (fifo_dir / "stale.queue").exists()
    assert (fifo_dir / ".gitkeep").exists()


def test_message_from_dict_handles_turn_and_verdict():
    turn = make_message()
    parsed_turn = message_from_dict(turn.model_dump(mode="json"))
    assert isinstance(parsed_turn, DebateMessage)

    verdict = VerdictMessage(
        session_id="s",
        payload=VerdictPayload(
            winner=AgentRole.PRO,
            pro_score=81,
            con_score=77,
            rationale="r",
            persuasion_notes="p",
        ),
    )
    parsed_verdict = message_from_dict(verdict.model_dump(mode="json"))
    assert isinstance(parsed_verdict, VerdictMessage)


def test_log_denial_emits_warning(caplog, monkeypatch):
    monkeypatch.setattr(logging.getLogger("debate"), "propagate", True)
    with caplog.at_level(logging.WARNING, logger="debate.gatekeeper"):
        log_denial(
            role=AgentRole.PRO,
            reason="budget",
            total_requests=5,
            per_agent={"pro": 3},
        )
    assert any("gatekeeper_denied" in record.message for record in caplog.records)


def test_watchdog_alive_then_restart_path():
    flag = {"alive": False, "restarts": 0}

    def is_alive() -> bool:
        flag["alive"] = not flag["alive"]
        return flag["alive"]

    def restart() -> None:
        flag["restarts"] += 1

    wd = Watchdog(interval_seconds=0.05, is_alive=is_alive, restart=restart)
    wd.start()
    _time.sleep(0.25)
    wd.stop()
    assert flag["restarts"] >= 1


def test_watchdog_restart_failure_is_logged(caplog, monkeypatch):
    monkeypatch.setattr(logging.getLogger("debate"), "propagate", True)

    def boom() -> None:
        raise RuntimeError("nope")

    wd = Watchdog(interval_seconds=0.05, is_alive=lambda: False, restart=boom)
    with caplog.at_level(logging.ERROR, logger="debate.watchdog"):
        wd.start()
        _time.sleep(0.2)
        wd.stop()
    assert any("Watchdog restart failed" in r.message for r in caplog.records)
