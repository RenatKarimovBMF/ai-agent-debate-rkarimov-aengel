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
Your assigned side: {own_side}
Opponent's assigned side: {opponent_side}

The host (PARENT) assigned the sides at the start of this session. You did
not pick your side. Defend the side you were assigned.

Rules of engagement:
- Be respectful and politically appropriate. No insults or profanity.
- Stay under {max_words} words per turn.
- Defend your assigned side. Do not switch sides.
- Do not concede the whole debate. You may concede a minor point if it
  strengthens your overall case.
- Address the opponent's previous argument before extending your own case.
- Use at least one credible web source per turn. Each citation must
  include a real title and a real http/https URL.
- Lies are permitted in this format — both sides may stretch the truth.
- However, if you accuse the opponent of being wrong on a factual claim,
  you MUST cite a real source that supports your refutation in the SAME
  turn. A bare "that is false" without a source does NOT count as a
  refutation and will be penalised by the judge.
- Never fabricate URLs. The judge penalises hallucinated sources harder
  than missing ones; if unsure, attack the warrant (the reasoning)
  instead of alleging a falsehood.

Output rules:
- Output ONLY valid JSON.
- Do not write markdown.
- Do not write any prose outside the JSON.

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
        opponent_part = (
            f"Opponent ({opponent_side}) last said:\n{opponent_text}\n\n"
            "Begin your turn with a direct rebuttal of the opponent's "
            "strongest claim before extending your own case. If you "
            "accuse the opponent of factual error, include a real "
            "citation that backs your refutation."
        )
    else:
        opponent_part = (
            "This is the opening statement. Start by framing what "
            "'greater' means under your value standard, then deliver "
            "your single strongest argument."
        )

    return f"""
Ping {ping}. Argue for {own_side}.

{opponent_part}

Return ONLY the required JSON object.
Do not use markdown.
Do not add text before or after the JSON.

Required schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}
"""


def host_opening_address(
    role: str,
    topic: str,
    assigned_side: str,
    opponent_side: str,
    pings: int,
    max_words: int,
) -> str:
    """Personal opening briefing the PARENT/JUDGE delivers to each child
    at session start. Mirrors the boxing-referee protocol described in
    `.claude/skills/debate-host-protocol`.
    """
    return (
        f"PARENT (host): {role} corner, this is your assignment for this "
        f"session.\n"
        f"- Topic: {topic}\n"
        f"- Your side: {assigned_side}\n"
        f"- Opponent's side: {opponent_side}\n"
        f"- Pings per side: {pings}\n"
        f"- Word cap per turn: {max_words}\n"
        f"- You speak only through me; never address the opponent directly.\n"
        f"- One real cited source per turn. Lies are allowed; refuting a "
        f"lie requires a cited source in the same turn.\n"
        f"- Touch gloves. We start with {role} on ping 1."
    )
