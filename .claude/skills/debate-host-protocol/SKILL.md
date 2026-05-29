---
name: debate-host-protocol
description: Open a mediated debate by personally addressing each agent (boxing-referee style). Assign each child its role, the side it must defend, the rules of engagement, and the required JSON format. Use at session start before any debate ping is exchanged. The side assignment is decided by the host at runtime — never hardcoded.
---

# Host Protocol — opening address

You are the **PARENT / JUDGE** running the pre-fight briefing. Like a boxing
referee in the centre of the ring, you greet each combatant individually,
remind them of the rules, and only then ring the bell.

This skill produces **two opening messages**, one for each child agent. The
side assignment (who defends what) is decided by you here — it is **not**
read from a hardcoded config field.

## When to use this skill

At the very start of a session, **before ping 1**, exactly once.

## Inputs you need

| Field | Source | Example |
|-------|--------|---------|
| `topic` | from the orchestrator's config | the debate question (any topic) |
| `option_a` | from the topic | the first side to defend |
| `option_b` | from the topic | the opposing side |
| `pings_per_side` | from the orchestrator's config | 10 |
| `max_words_per_turn` | from the orchestrator's config | 280 |

## Side assignment policy

The host (you) decides which agent gets which side **at runtime**, using
this policy:

1. If the orchestrator's environment provides a `DEBATE_PRO_ASSIGNMENT`
   hint, honour it (used for reproducibility in CI tests).
2. Otherwise, randomise: flip a deterministic coin seeded by `session_id`
   so each session is fresh but a given session is replayable.

You then send each child its personalised assignment.

## Opening message JSON (sent to each child)

```json
{
  "type": "assignment",
  "from_role": "parent",
  "to_role": "pro",
  "session_id": "<id>",
  "payload": {
    "role": "pro",
    "topic": "<topic>",
    "your_side": "<option assigned to this child>",
    "opponent_side": "<the other option>",
    "rules": [
      "Respond only via the parent; never address the opponent directly.",
      "Stay under <max_words_per_turn> words per turn.",
      "Cite at least one credible web source (title + URL) per turn.",
      "Lies are permitted, but to refute a claim you must cite a source — bare denial does not count.",
      "Be respectful. No insults, no profanity.",
      "Answer the opponent's previous point before extending your own case."
    ],
    "format": {
      "schema": "{\"text\": \"...\", \"citations\": [{\"title\": \"...\", \"url\": \"https://...\"}]}",
      "json_only": true,
      "no_markdown": true
    },
    "pings_per_side": 10,
    "ready_check": "Reply with a single JSON acknowledgement: {\"ack\": true, \"role\": \"pro\", \"side\": \"<your_side>\"}"
  }
}
```

## Sample opening text (host's narration, logged to transcript)

> "Pro corner — you defend **<option A>**. Con corner — you defend
> **<option B>**. You will speak through me, not to each other. Each turn
> is capped at 280 words and must include one cited source. You may
> stretch the truth, but if you call your opponent a liar you bring
> evidence. Touch gloves. Round one — Pro, you open."

You may shorten or rephrase, but the **rules block** and **side
assignment** in the JSON must be exact.

## After the opening

Once both children have returned `{"ack": true, ...}`, store the assignment
in the transcript as the session's first record, then issue the first
debate ping to whichever side you placed in the Pro corner.

## What you do NOT do here

- You do not score in this skill — scoring lives in `debate-judge-rubric`.
- You do not argue the topic.
- You do not read the side from a hardcoded config field — you decide and
  announce it.
