from __future__ import annotations

import logging

from debate.agent_base import BaseAgent
from debate.agents.json_parse import extract_json

logger = logging.getLogger("debate.agents")


def validate_verdict_dict(data: dict) -> None:
    winner = str(data.get("winner", "")).strip().lower()
    if winner not in {"pro", "con"}:
        raise ValueError('Verdict winner must be exactly "pro" or "con"')

    pro_score = float(data["pro_score"])
    con_score = float(data["con_score"])

    if not (0 <= pro_score <= 100):
        raise ValueError("pro_score must be between 0 and 100")

    if not (0 <= con_score <= 100):
        raise ValueError("con_score must be between 0 and 100")

    if pro_score == con_score:
        raise ValueError("Verdict scores cannot be equal")

    if winner == "pro" and pro_score <= con_score:
        raise ValueError("If winner is pro, pro_score must be higher")

    if winner == "con" and con_score <= pro_score:
        raise ValueError("If winner is con, con_score must be higher")

    if not str(data.get("rationale", "")).strip():
        raise ValueError("rationale cannot be empty")

    if not str(data.get("persuasion_notes", "")).strip():
        raise ValueError("persuasion_notes cannot be empty")


def invoke_and_parse_verdict_with_retry(agent: BaseAgent, prompt: str) -> dict:
    raw = agent.invoke_llm(prompt)

    try:
        data = extract_json(raw)
        validate_verdict_dict(data)
        return data
    except Exception as first_error:
        logger.warning(
            "Invalid verdict JSON from %s. Asking model to repair. Error: %s",
            agent.role.value,
            first_error,
        )

        repair_prompt = f"""
Your previous answer was not valid JSON or did not match the required schema.

Error:
{first_error}

Original invalid answer:
{raw}

Rewrite it as ONLY one valid JSON object.
Do not use markdown.
Do not add text before or after the JSON.
Do not use triple backticks.
Escape every quote inside strings.
Do not put raw newlines inside JSON strings.

Required schema:
{{"winner": "pro", "pro_score": 81, "con_score": 77, "rationale": "...", "persuasion_notes": "..."}}

Rules:
- "winner" must be exactly "pro" or "con".
- "pro_score" and "con_score" must be numbers from 0 to 100.
- Scores must be different.
- No tie is allowed.
- The winner must have the higher score.
"""

        repaired_raw = agent.invoke_llm(repair_prompt)

        try:
            data = extract_json(repaired_raw)
            validate_verdict_dict(data)
            return data
        except Exception as second_error:
            logger.exception(
                "Verdict JSON repair failed. Using fallback verdict. Error: %s",
                second_error,
            )

            return {
                "winner": "pro",
                "pro_score": 81,
                "con_score": 79,
                "rationale": (
                    "Fallback verdict used because the judge returned malformed JSON twice. "
                    "The system completed safely and still obeyed the no-tie rule."
                ),
                "persuasion_notes": (
                    "The fallback preserves system robustness. "
                    "The saved transcript can still be inspected manually."
                ),
            }
