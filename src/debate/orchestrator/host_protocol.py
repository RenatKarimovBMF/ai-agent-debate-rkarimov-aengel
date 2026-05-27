from __future__ import annotations

import hashlib
import logging
import multiprocessing as mp
import os

from debate.config import AppConfig
from debate.models import AgentRole
from debate.orchestrator.commands import assignment
from debate.orchestrator.events import emit_event

log = logging.getLogger("debate.host")


SHARED_RULES = [
    "Speak only through the parent. Never address the opponent directly.",
    "One real cited source per turn (title + URL).",
    "Lies are allowed, but refuting a lie requires a real cited source in the same turn.",
    "Bare contradictions without a source do not count as refutations.",
    "Be respectful. No insults or profanity.",
    "Address the opponent's previous argument before extending your own case.",
]


def _swap_seeded_by_session(session_id: str) -> bool:
    """Deterministic coin flip: same session_id always produces the same
    assignment, so a run is replayable, but different sessions vary."""
    override = os.environ.get("DEBATE_PRO_ASSIGNMENT", "").strip().lower()
    if override == "option_a":
        return False
    if override == "option_b":
        return True

    digest = hashlib.sha256(session_id.encode("utf-8")).digest()
    return bool(digest[0] & 1)


def decide_sides(config: AppConfig, session_id: str) -> dict[AgentRole, str]:
    """Pick which corner defends which position. Returns role -> side."""
    option_a = config.debate.pro_side
    option_b = config.debate.con_side

    if _swap_seeded_by_session(session_id):
        return {AgentRole.PRO: option_b, AgentRole.CON: option_a}

    return {AgentRole.PRO: option_a, AgentRole.CON: option_b}


def send_assignments(
    *,
    config: AppConfig,
    session_id: str,
    parent_to_pro: mp.Queue,
    parent_to_con: mp.Queue,
    event_queue: mp.Queue,
) -> dict[AgentRole, str]:
    """Deliver the personalised opening briefing to each child via the
    orchestrator queues. Called once at session start, before pings."""
    sides = decide_sides(config, session_id)
    pro_side = sides[AgentRole.PRO]
    con_side = sides[AgentRole.CON]

    debate = config.debate
    emit_event(
        event_queue,
        f"PARENT (host): assigning sides — PRO defends '{pro_side}', "
        f"CON defends '{con_side}' (session-seeded, not hardcoded).",
        kind="host",
        data={"pro": pro_side, "con": con_side, "session_id": session_id},
    )

    parent_to_pro.put(
        assignment(
            role=AgentRole.PRO.value,
            topic=debate.topic,
            assigned_side=pro_side,
            opponent_side=con_side,
            pings=debate.pings_per_side,
            max_words=debate.max_words_per_turn,
            rules=SHARED_RULES,
        )
    )

    parent_to_con.put(
        assignment(
            role=AgentRole.CON.value,
            topic=debate.topic,
            assigned_side=con_side,
            opponent_side=pro_side,
            pings=debate.pings_per_side,
            max_words=debate.max_words_per_turn,
            rules=SHARED_RULES,
        )
    )

    return sides
