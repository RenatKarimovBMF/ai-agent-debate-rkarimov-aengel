"""Cover ``DebateGui`` callbacks with messagebox + worker thread stubbed.

A real (withdrawn) Tk window is built so widget state changes execute,
but dialogs and the debate worker are monkeypatched away.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import pytest

from debate.gui import app as app_mod
from debate.gui import controls as controls_mod


@pytest.fixture
def gui(monkeypatch):
    calls: dict[str, list] = {"warn": [], "error": [], "info": [], "start": []}
    mb = controls_mod.messagebox
    monkeypatch.setattr(mb, "showwarning", lambda *a: calls["warn"].append(a))
    monkeypatch.setattr(mb, "showerror", lambda *a: calls["error"].append(a))
    monkeypatch.setattr(mb, "showinfo", lambda *a: calls["info"].append(a))
    monkeypatch.setattr(controls_mod, "start_debate_thread", lambda **k: calls["start"].append(k))
    window = app_mod.DebateGui()
    window.withdraw()
    try:
        yield window, calls
    finally:
        window.destroy()


def test_defaults_logging_and_status(gui):
    window, _ = gui
    assert window.w.pro_entry.get()
    window._clear_log()
    window._queue_log("queued line")
    window._drain_log_queue()
    assert "queued line" in window.w.log.get("1.0", tk.END)
    window._set_status("Busy")
    assert window.w.status.cget("text") == "Busy"


def test_running_ui_toggle(gui):
    window, _ = gui
    window._set_running_ui(True)
    assert window.w.start_btn.cget("text") == "Stop debate"
    assert str(window.w.reset_btn.cget("state")) == tk.DISABLED
    window._set_running_ui(False)
    assert window.w.start_btn.cget("text") == "Start debate"
    assert str(window.w.reset_btn.cget("state")) == tk.NORMAL


def test_pulse_indicator_blinks_then_clears(gui):
    window, _ = gui
    window._running = True
    window._pulse_indicator()
    assert window.w.running_indicator.cget("text")  # non-empty while running
    window._running = False
    window._pulse_indicator()
    assert window.w.running_indicator.cget("text") == ""


def test_on_stop_requests_cancel(gui):
    window, _ = gui
    window._running = True
    window._set_running_ui(True)
    window._on_stop()
    assert window._cancel.is_set()
    assert "Stopping" in window.w.status.cget("text")

    window._running = False
    window._cancel.clear()
    window._on_stop()  # ignored when not running
    assert not window._cancel.is_set()


def test_on_done_cancelled_is_graceful(gui):
    from debate.orchestrator import DebateCancelled

    window, calls = gui
    # Simulate a stop: the button is disabled with "Stopping…" first.
    window._running = True
    window._set_running_ui(True)
    window._on_stop()
    assert str(window.w.start_btn.cget("state")) == tk.DISABLED

    window._on_done(None, DebateCancelled("stopped"))
    assert window.w.status.cget("text") == "Stopped"
    assert calls["error"] == []
    # Regression guard: a new debate must be startable afterwards.
    assert str(window.w.start_btn.cget("state")) == tk.NORMAL
    assert window.w.start_btn.cget("text") == "Start debate"


def test_on_start_valid_launches_worker(gui):
    window, calls = gui
    window.w.pro_entry.delete(0, tk.END)
    window.w.pro_entry.insert(0, "Cats")
    window.w.con_entry.delete(0, tk.END)
    window.w.con_entry.insert(0, "Dogs")
    window.w.topic_entry.delete(0, tk.END)
    window.w.topic_entry.insert(0, "Best pet?")

    window._on_start()
    assert window._running is True
    assert len(calls["start"]) == 1


def test_on_start_invalid_warns(gui):
    window, calls = gui
    for entry in (window.w.pro_entry, window.w.con_entry):
        entry.delete(0, tk.END)
        entry.insert(0, "Same")
    window._on_start()
    assert calls["warn"]
    assert window._running is False
    assert calls["start"] == []


def test_on_start_ignored_when_running(gui):
    window, calls = gui
    window._running = True
    window._on_start()
    assert calls["start"] == []


def test_on_done_success_and_error(gui):
    window, calls = gui
    window._on_done(Path("logs/v.json"), None)
    assert calls["info"]
    assert window.w.status.cget("text") == "Finished"

    window._on_done(None, RuntimeError("boom"))
    assert calls["error"]
    assert window.w.status.cget("text") == "Error"
