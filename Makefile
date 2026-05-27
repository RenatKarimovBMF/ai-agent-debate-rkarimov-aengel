# Convenience wrappers over `uv run ...` so contributors can rely on
# the same commands locally and in CI. Every target documented in the
# `help` block; the help block itself is what `make` (no target) prints.
#
# Pre-requisite: install `uv` first (https://docs.astral.sh/uv/).

.DEFAULT_GOAL := help
.PHONY: help install install-dev clean \
        test test-cov lint format cap check ci \
        run dry-run gui version

help: ## show this help
	@echo "AI Agent Debate -- common make targets:"
	@echo ""
	@echo "  install        sync runtime dependencies"
	@echo "  install-dev    sync runtime + dev dependencies"
	@echo ""
	@echo "  test           run the pytest suite"
	@echo "  test-cov       run the pytest suite with coverage report"
	@echo "  lint           run ruff in check mode"
	@echo "  format         run ruff in fix-and-format mode"
	@echo "  cap            verify every src/.py file is <= 150 raw lines"
	@echo "  check          run lint + cap + test-cov (the full local gate)"
	@echo "  ci             alias for check, intended for CI"
	@echo ""
	@echo "  run            python -m debate.main (full debate)"
	@echo "  dry-run        python -m debate.main --dry-run (config + provider check)"
	@echo "  gui            python -m debate.gui (Tkinter launcher)"
	@echo "  version        python -m debate.main --version"
	@echo ""
	@echo "  clean          remove .venv, build, and tooling caches"

install: ## sync runtime dependencies
	uv sync

install-dev: ## sync runtime + dev dependencies
	uv sync --extra dev

test: ## run the pytest suite
	uv run pytest -q

test-cov: ## run the pytest suite with coverage
	uv run pytest --cov

lint: ## ruff check
	uv run ruff check src tests

format: ## ruff fix + format
	uv run ruff check --fix src tests
	uv run ruff format src tests

cap: ## verify the 150-line raw-line file cap
	uv run python scripts/check_line_cap.py 150

check: lint cap test-cov ## run the full local quality gate
ci: check ## same as check; called from CI

run: ## run a full debate session
	uv run python -m debate.main --config config/setup.json

dry-run: ## print config + active LLM provider without calling agents
	uv run python -m debate.main --dry-run --config config/setup.json

gui: ## open the optional Tkinter launcher
	uv run python -m debate.gui

version: ## print the package version
	uv run python -m debate.main --version

clean: ## remove .venv, build, and tooling caches
	rm -rf .venv build dist .pytest_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
