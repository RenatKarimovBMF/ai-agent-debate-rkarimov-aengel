from __future__ import annotations

import argparse
import sys
from pathlib import Path

from debate.config import load_config
from debate.env_loader import ensure_env_loaded
from debate.process_orchestrator import ProcessDebateOrchestrator


def main(argv: list[str] | None = None) -> int:
    ensure_env_loaded()

    parser = argparse.ArgumentParser(
        description="AI Agent Debate — Exercise 02"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.toml (default: project root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print config and exit without calling agents",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open optional topic launcher GUI",
    )
    parser.add_argument("--pro", type=str, default=None, help="Override pro side name")
    parser.add_argument("--con", type=str, default=None, help="Override con side name")
    parser.add_argument("--topic", type=str, default=None, help="Override debate question")
    args = parser.parse_args(argv)

    if args.gui:
        from debate.gui import main as gui_main

        return gui_main()

    config = load_config(args.config)

    if args.pro and args.con and args.topic:
        from debate.config import with_custom_debate

        config = with_custom_debate(
            config,
            pro_side=args.pro,
            con_side=args.con,
            topic=args.topic,
        )

    if args.dry_run:
        from sdk.llm_client import LlmClient

        client = LlmClient(
            cli_command=config.agents.cli_command,
            workdir=config.project_root / config.agents.workdir,
            timeout_seconds=config.debate.request_timeout_seconds,
            gemini_model=config.llm.gemini_model,
            gemini_fallback_models=config.llm.gemini_model_fallbacks,
            use_google_search=config.llm.use_google_search,
        )

        print(f"LLM provider: {client.active_provider()}")
        print(f"Topic: {config.debate.topic}")
        print(f"Pings per side: {config.debate.pings_per_side}")
        print(f"Pro: {config.debate.pro_side} | Con: {config.debate.con_side}")
        print("Execution mode: real multiprocessing agents")
        return 0

    orchestrator = ProcessDebateOrchestrator(config)
    orchestrator.start_watchdogs()

    try:
        verdict_path = orchestrator.run()
        print(f"Debate finished. Verdict written to: {verdict_path}")
        return 0
    finally:
        orchestrator.stop_watchdogs()


if __name__ == "__main__":
    sys.exit(main())