---
name: debate-evidence
description: Source and deploy concrete evidence for any debate side and any topic. Teaches how to find credible, citeable sources, rank evidence quality, turn the opponent's evidence, and avoid fabrication. Side-agnostic and topic-agnostic — it never supplies hardcoded facts; the debater finds its own. Use as a supporting evidence layer alongside debate-argument-builder and debate-rebuttal-strategist, whatever side the parent assigned.
---

# Evidence — find and deploy your own sources

This skill is **side-agnostic and topic-agnostic**. It does **not** contain
any facts about any specific subject. Your job is to find concrete,
verifiable evidence for whatever side the Parent assigned you, on whatever
the topic is, and to cite it correctly. `debate-argument-builder` owns the
constructive prose and `debate-rebuttal-strategist` owns refutation; this
skill makes sure both rest on real, well-chosen sources.

## Find your own evidence (never rely on pre-supplied facts)

For your assigned side, gather support from the strongest sources you can
justify — for example:

- **Authoritative rankings / awards / records** relevant to the topic.
- **Expert or institutional consensus** (official bodies, standards,
  peer-reviewed or professional sources).
- **Primary sources** (original documents, datasets, official statements).
- **Reputable reporting** from major, named publications.

Prefer sources the opponent cannot easily dismiss. If the topic is
unfamiliar, reason from the most credible category of source available and
state which standard of proof you are using.

## Evidence quality ladder (strongest first)

1. Primary source / official record.
2. Expert or institutional consensus.
3. Reputable secondary reporting.
4. Aggregated popularity / crowd signal (weak — opponents will attack the
   methodology, so frame it carefully).

When two sources conflict, prefer the higher rung and say why.

## Make each point concrete and valid

- One **specific, checkable** claim per source — not a vague gesture.
- Pair every factual claim with a **real title + real http/https URL**.
- State *what* the source shows and *why* it supports your side (link the
  evidence to your value standard).
- Quantify where possible (a date, a rank, a figure) instead of adjectives.

## Turn the opponent's evidence

If the opponent leans on a weak source (e.g. a popularity poll), expose the
methodology and re-anchor on a higher rung. If their own source actually
supports your side, **turn it** — the most efficient evidence move.

## Hard rules (shared with the rubric)

- **Never fabricate a source or URL.** The judge penalises hallucinated
  sources harder than missing ones. If unsure, attack the reasoning
  instead of alleging a falsehood.
- To allege the opponent stated a falsehood, cite a real source in the
  **same turn** (see `debate-rebuttal-strategist`).
- A citation must have a non-empty title and a URL starting with
  `http://` or `https://`.

This skill produces no JSON itself; it feeds vetted sources and framing
into the constructive and rebuttal skills, which own the final turn.
