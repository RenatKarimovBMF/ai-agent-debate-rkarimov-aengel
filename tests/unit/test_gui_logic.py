"""Cover GUI logic that needs no widgets: env_check, package entrypoints."""

from __future__ import annotations

import debate.gui as gui_pkg
from debate.gui import env_check


def test_validate_inputs_blank():
    error = env_check.validate_inputs("", "Dogs", "Q?")
    assert error is not None
    assert "Fill in both sides" in error


def test_validate_inputs_identical_sides():
    error = env_check.validate_inputs("Cats", "cats", "Best pet?")
    assert error == "Pro and Con must be different."


def test_validate_inputs_ok():
    assert env_check.validate_inputs("Cats", "Dogs", "Best pet?") is None


def test_resolve_provider_status_success():
    status = env_check.resolve_provider_status()
    assert status.startswith("LLM:")


def test_resolve_provider_status_handles_failure(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("no config")

    monkeypatch.setattr(env_check, "load_config", boom)
    status = env_check.resolve_provider_status()
    assert status.startswith("LLM setup error:")


def test_gui_package_main_runs_without_mainloop(monkeypatch):
    class _FakeGui:
        def __init__(self) -> None:
            self.looped = False

        def mainloop(self) -> None:
            self.looped = True

    monkeypatch.setattr(gui_pkg, "ensure_env_loaded", lambda: None)
    monkeypatch.setattr(gui_pkg, "DebateGui", _FakeGui)
    assert gui_pkg.main() == 0


def test_gui_dunder_main_module_imports():
    import debate.gui.__main__ as entry

    assert callable(entry.main)
