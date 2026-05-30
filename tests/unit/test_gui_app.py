"""Cover ``DebateGui`` callbacks with messagebox + worker thread stubbed.

A real (withdrawn) Tk window is built so widget state changes execute,
but dialogs and the debate worker are monkeypatched away.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import pytest

from debate.gui import app as app_mod


@pytest.fixture
def gui(monkeypatch):
    calls: dict[str, list] = {"warn": [], "error": [], "info": [], "start": []}
    monkeypatch.setattr(app_mod.messagebox, "showwarning", lambda *a: calls["warn"].append(a))
    monkeypatch.setattr(app_mod.messagebox, "showerror", lambda *a: calls["error"].append(a))
    monkeypatch.setattr(app_mod.messagebox, "showinfo", lambda *a: calls["info"].append(a))
    monkeypatch.setattr(app_mod, "start_debate_thread", lambda **k: calls["start"].append(k))
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
    assert str(window.w.start_btn.cget("state")) == tk.DISABLED
    window._set_running_ui(False)
    assert str(window.w.start_btn.cget("state")) == tk.NORMAL


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
