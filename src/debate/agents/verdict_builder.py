from __future__ import annotations

from debate.models import AgentRole, VerdictMessage, VerdictPayload


def _build_verdict_message(session_id: str, data: dict) -> VerdictMessage:
    """Validate the judge's JSON output and enforce the no-tie invariant.

    The LLM occasionally returns equal scores or a winner whose score is
    not strictly the higher one. We clamp scores into [0, 100] and bump
    the winner just enough to guarantee the rubric's strict-inequality
    rule before constructing the message.
    """
    winner = AgentRole(data["winner"])
    if winner not in (AgentRole.PRO, AgentRole.CON):
        raise ValueError("Judge must pick pro or con")

    pro_score = max(0.0, min(100.0, float(data["pro_score"])))
    con_score = max(0.0, min(100.0, float(data["con_score"])))

    if pro_score == con_score:
        if winner == AgentRole.PRO:
            pro_score = min(100.0, pro_score + 1.0)
        else:
            con_score = min(100.0, con_score + 1.0)

    if winner == AgentRole.PRO and pro_score <= con_score:
        pro_score = min(100.0, con_score + 1.0)

    if winner == AgentRole.CON and con_score <= pro_score:
        con_score = min(100.0, pro_score + 1.0)

    return VerdictMessage(
        session_id=session_id,
        payload=VerdictPayload(
            winner=winner,
            pro_score=pro_score,
            con_score=con_score,
            rationale=str(data["rationale"]),
            persuasion_notes=str(data["persuasion_notes"]),
        ),
    )
