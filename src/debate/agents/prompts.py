from __future__ import annotations


def debater_prompt(
    role: str,
    topic: str,
    own_side: str,
    opponent_side: str,
    max_words: int,
) -> str:
    return f"""You are the {role} debater in a formal AI-agent debate.
Topic: {topic}
Your side: {own_side}
Opponent side: {opponent_side}

Rules:
- Be respectful and politically appropriate.
- Stay under {max_words} words per turn.
- Defend your assigned side.
- Do not switch sides.
- Do not concede the whole debate.
- Directly answer the opponent's previous argument when one is provided.
- Use at least one credible web source per turn.
- Each citation must include a real title and a real http/https URL.
- Output ONLY valid JSON.
- Do not write markdown.
- Do not write explanation outside the JSON.

Important JSON rules:
- Output exactly one JSON object.
- Do not wrap the JSON in markdown.
- Do not use triple backticks.
- Escape every quote inside strings.
- Do not put raw newlines inside JSON strings.
- The "citations" array must contain at least one source.
- URLs must start with http:// or https://.

Required JSON schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}
"""


def turn_prompt(
    ping: int,
    own_side: str,
    opponent_side: str,
    opponent_text: str | None,
) -> str:
    if opponent_text:
        opponent_part = f"Opponent ({opponent_side}) last said:\n{opponent_text}"
    else:
        opponent_part = "This is the opening statement. Start with your strongest framing."

    return f"""
Ping {ping}. Argue for {own_side}.

{opponent_part}

Return ONLY the required JSON object.
Do not use markdown.
Do not add text before or after the JSON.

Required schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}
"""
