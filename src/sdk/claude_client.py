from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
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
        configured = os.environ.get("CLAUDE_CLI_PATH", cli_command)
        # On Windows the CLI is a `claude.cmd` / `claude.ps1` shim that
        # CreateProcess cannot find from the bare name, so resolve the
        # real path via PATHEXT. Falls back to the configured name when
        # the CLI is absent (CI), preserving the missing-CLI error path.
        self._cli = shutil.which(configured) or configured
        self._workdir = workdir or Path.cwd()
        self._timeout = timeout_seconds

    def available(self) -> bool:
        """True if the Claude CLI is installed and resolvable on PATH."""
        return shutil.which(self._cli) is not None

    def prompt(self, system: str, user: str) -> ClaudeResponse:
        """Run a single non-interactive CLI invocation.

        The system prompt is written to a temp file (`--system-prompt-file`)
        and the user prompt is piped via stdin. Multi-line text passed as a
        CLI argument breaks the Windows `claude.cmd` shim, whereas a file
        path and stdin are safe on every platform.
        """
        sys_file = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        sys_file.write(system)
        sys_file.close()
        cmd = [
            self._cli,
            "--print",
            "--system-prompt-file",
            sys_file.name,
            "--output-format",
            "text",
        ]
        logger.info("SDK prompt", extra={"extra_data": {"cmd": cmd[:2]}})
        try:
            result = subprocess.run(
                cmd,
                cwd=self._workdir,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
                input=user,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Claude CLI timed out after {self._timeout}s") from exc
        finally:
            os.unlink(sys_file.name)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Claude CLI failed")
        text = result.stdout.strip()
        return ClaudeResponse(text=text, raw=result.stdout)

    def prompt_api(
        self,
        system: str,
        user: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> ClaudeResponse:
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
