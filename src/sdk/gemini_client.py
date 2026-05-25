from __future__ import annotations

import logging
import time

from sdk.claude_client import ClaudeResponse

logger = logging.getLogger("debate.sdk.gemini")


class GeminiAgentClient:
    """Google Gemini API — free tier via AI Studio. Retries and model fallbacks on 429."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        fallback_models: tuple[str, ...] = (),
        timeout_seconds: int = 120,
        use_google_search: bool = False,
        max_retries: int = 3,
    ) -> None:
        self._models = (model, *fallback_models)
        self._timeout = timeout_seconds
        self._use_google_search = use_google_search
        self._max_retries = max_retries
        from sdk.llm_client import _env_key

        api_key = _env_key("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add your free key from "
                "https://aistudio.google.com/apikey to .env"
            )
        self._api_key = api_key

    def prompt(self, system: str, user: str) -> ClaudeResponse:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Package 'google-genai' is not installed. Run: uv sync --extra dev"
            ) from exc

        client = genai.Client(api_key=self._api_key)
        errors: list[str] = []

        for model_name in self._models:
            for use_search in self._search_attempts():
                for attempt in range(self._max_retries):
                    try:
                        text = self._generate(
                            client, model_name, system, user, use_search
                        )
                        logger.info(
                            "Gemini OK",
                            extra={
                                "extra_data": {
                                    "model": model_name,
                                    "search": use_search,
                                }
                            },
                        )
                        return ClaudeResponse(text=text, raw=text)
                    except Exception as exc:
                        msg = str(exc)
                        errors.append(f"{model_name}(search={use_search}): {msg[:200]}")
                        if _is_quota_error(msg) and attempt < self._max_retries - 1:
                            wait = 6 * (attempt + 1)
                            logger.warning("Gemini 429, retry in %ss", wait)
                            time.sleep(wait)
                            continue
                        break

        combined = "\n".join(errors)
        if "expired" in combined.lower():
            raise RuntimeError(
                "Your GEMINI_API_KEY is expired or invalid.\n\n"
                "Fix:\n"
                "1. Open https://aistudio.google.com/apikey\n"
                "2. Delete the old key (or create a new one)\n"
                "3. Paste the NEW key into .env → GEMINI_API_KEY=AIza...\n"
                "4. Close terminal, open a new one, run: python -m debate.test_gemini"
            ) from None

        raise RuntimeError(
            "All Gemini models failed. Try:\n"
            "1. New API key at https://aistudio.google.com/apikey\n"
            "2. Run: python -m debate.test_gemini\n"
            "3. If quota is 0, your region may block free tier — ask lecturer\n\n"
            + "\n".join(errors[-4:])
        )

    def _search_attempts(self) -> list[bool]:
        if self._use_google_search:
            return [True, False]
        return [False]

    def _generate(self, client, model_name: str, system: str, user: str, use_search: bool) -> str:
        from google.genai import types

        if use_search:
            config = types.GenerateContentConfig(
                system_instruction=system,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
        else:
            config = types.GenerateContentConfig(system_instruction=system)

        response = client.models.generate_content(
            model=model_name,
            contents=user,
            config=config,
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text


def _is_quota_error(message: str) -> bool:
    upper = message.upper()
    return "429" in upper or "RESOURCE_EXHAUSTED" in upper or "QUOTA" in upper
