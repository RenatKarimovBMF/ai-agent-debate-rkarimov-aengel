from __future__ import annotations

from debate.config import load_config
from debate.env_loader import ensure_env_loaded, gemini_key_hint
from sdk.llm_client import LlmClient


def resolve_provider_status() -> str:
    """Return a human-friendly description of the active LLM provider.

    Called by the GUI to populate the env-status label and by tests to
    avoid duplicating the provider-detection wiring.
    """
    ensure_env_loaded()

    try:
        cfg = load_config()
        client = LlmClient(
            cli_command=cfg.agents.cli_command,
            workdir=cfg.project_root / cfg.agents.workdir,
            gemini_model=cfg.llm.gemini_model,
            gemini_fallback_models=cfg.llm.gemini_model_fallbacks,
            use_google_search=cfg.llm.use_google_search,
        )
        provider = client.active_provider()
        return f"LLM: {provider} | {gemini_key_hint()}"
    except Exception as exc:
        return f"LLM setup error: {exc}"


def validate_inputs(pro: str, con: str, topic: str) -> str | None:
    """Return an error string if the form inputs are unusable, else None."""
    if not pro.strip() or not con.strip() or not topic.strip():
        return "Fill in both sides and the debate question."
    if pro.strip().lower() == con.strip().lower():
        return "Pro and Con must be different."
    return None
