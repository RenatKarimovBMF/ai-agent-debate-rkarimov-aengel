from __future__ import annotations


def short_text(text: str, limit: int = 700) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "..."
