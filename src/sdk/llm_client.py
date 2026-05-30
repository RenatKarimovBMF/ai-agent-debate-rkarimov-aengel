from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from sdk.claude_client import ClaudeAgentClient
from sdk.gemini_client import GeminiAgentClient

logger = logging.getLogger("debate.sdk.llm")

_PLACEHOLDER_MARKERS = (
    "your-key",
    "your_key",
    "paste",
    "example",
    "changeme",
    "xxx",
    "sk-ant-your",
    "aizasy-your",
)


def _env_key(name: str) -> str | None:
    """Return env value only if it looks like a real key, not a template placeholder."""
    value = (os.environ.get(name) or "").strip()
    if not value:
        return None
    lower = value.lower()
    if any(marker in lower for marker in _PLACEHOLDER_MARKERS):
        return None
    return value


@dataclass(frozen=True)
class LlmResponse:
    text: str
    raw: str
    provider: str


class LlmClient:
    """
    Unified LLM access. Priority when LLM_PROVIDER=auto:
      1. Claude CLI login (highest quality; uses a Claude Pro/Max plan)
      2. Anthropic API (ANTHROPIC_API_KEY)
      3. Gemini (GEMINI_API_KEY) — free tier, lower fidelity
    Set LLM_PROVIDER explicitly (gemini / anthropic / claude_cli) to override.
    """

    def __init__(
        self,
        cli_command: str = "claude",
        workdir: Path | None = None,
        timeout_seconds: int = 120,
        gemini_model: str = "gemini-2.5-flash",
        gemini_fallback_models: tuple[str, ...] = (),
        use_google_search: bool = False,
        anthropic_web_search: bool = False,
    ) -> None:
        self._timeout = timeout_seconds
        self._gemini_model = gemini_model
        self._gemini_fallbacks = gemini_fallback_models
        self._use_google_search = use_google_search
        self._claude = ClaudeAgentClient(
            cli_command=cli_command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
            web_search=anthropic_web_search,
        )
        self._gemini: GeminiAgentClient | None = None

    def _resolve_provider(self) -> str:
        forced = (os.environ.get("LLM_PROVIDER") or "auto").strip().lower()
        if forced == "gemini":
            if not _env_key("GEMINI_API_KEY"):
                raise RuntimeError(
                    "LLM_PROVIDER=gemini but GEMINI_API_KEY is missing. "
                    "Add your free key from https://aistudio.google.com/apikey to .env"
                )
            return "gemini"
        if forced == "anthropic":
            return "anthropic"
        if forced == "claude_cli":
            return "claude_cli"
        # auto: prefer the Claude CLI subscription, then the Anthropic
        # API, then the free (but lower-fidelity) Gemini tier.
        if self._claude.available():
            return "claude_cli"
        if _env_key("ANTHROPIC_API_KEY"):
            return "anthropic"
        if _env_key("GEMINI_API_KEY"):
            return "gemini"
        return "claude_cli"

    def _gemini_client(self) -> GeminiAgentClient:
        if self._gemini is None:
            self._gemini = GeminiAgentClient(
                model=self._gemini_model,
                fallback_models=self._gemini_fallbacks,
                timeout_seconds=self._timeout,
                use_google_search=self._use_google_search,
            )
        return self._gemini

    def complete(self, system: str, user: str) -> LlmResponse:
        provider = self._resolve_provider()
        logger.info("LLM call", extra={"extra_data": {"provider": provider}})

        if provider == "gemini":
            r = self._gemini_client().prompt(system, user)
            return LlmResponse(text=r.text, raw=r.raw, provider="gemini")

        if provider == "anthropic":
            r = self._claude.prompt_api(system, user)
            return LlmResponse(text=r.text, raw=r.raw, provider="anthropic")

        try:
            r = self._claude.prompt(system, user)
            return LlmResponse(text=r.text, raw=r.raw, provider="claude_cli")
        except (RuntimeError, FileNotFoundError, TimeoutError) as exc:
            raise RuntimeError(
                "No LLM available. Add GEMINI_API_KEY (free) to .env — see docs/GEMINI_SETUP.md. "
                "Get a key: https://aistudio.google.com/apikey"
            ) from exc

    def active_provider(self) -> str:
        return self._resolve_provider()
