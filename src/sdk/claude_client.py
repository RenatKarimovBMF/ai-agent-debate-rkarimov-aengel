from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("debate.sdk")


@dataclass(frozen=True)
class ClaudeResponse:
    text: str
    raw: str


class ClaudeAgentClient:
    """SDK wrapper for Claude CLI one-shot prompts (debuggable without orchestrator)."""

    def __init__(
        self,
        cli_command: str = "claude",
        workdir: Path | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self._cli = os.environ.get("CLAUDE_CLI_PATH", cli_command)
        self._workdir = workdir or Path.cwd()
        self._timeout = timeout_seconds

    def prompt(self, system: str, user: str) -> ClaudeResponse:
        """Run a single non-interactive CLI invocation."""
        payload = json.dumps({"system": system, "user": user}, ensure_ascii=False)
        cmd = [
            self._cli,
            "-p",
            user,
            "--system-prompt",
            system,
            "--output-format",
            "text",
        ]
        logger.info("SDK prompt", extra={"extra_data": {"cmd": cmd[:3]}})
        try:
            result = subprocess.run(
                cmd,
                cwd=self._workdir,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Claude CLI timed out after {self._timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Claude CLI failed")
        text = result.stdout.strip()
        return ClaudeResponse(text=text, raw=result.stdout)

    def prompt_api(self, system: str, user: str, model: str = "claude-sonnet-4-20250514") -> ClaudeResponse:
        """Fallback via Anthropic API when CLI is unavailable."""
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Package 'anthropic' is not installed. Run: uv sync --extra dev"
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your API key."
            )
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
            timeout=self._timeout,
        )
        text = message.content[0].text  # type: ignore[union-attr]
        return ClaudeResponse(text=text, raw=text)
