"""Build the real Tk widget tree headlessly (root withdrawn, no mainloop).

Exercises ``widgets``, ``form``, ``panels`` and ``layout`` so the form
builders, both button styles, header and log panel all execute.
"""

from __future__ import annotations

import tkinter as tk

import pytest

from debate.gui.form import FormWidgets, build_form
from debate.gui.layout import GuiWidgets, build_layout
from debate.gui.panels import build_header, build_log_panel
from debate.gui.widgets import labeled_entry


@pytest.fixture
def root():
    tk_root = tk.Tk()
    tk_root.withdraw()
    try:
        yield tk_root
    finally:
        tk_root.destroy()


def test_labeled_entry_returns_entry(root):
    frame = tk.Frame(root)
    entry = labeled_entry(frame, "Side A", side=tk.LEFT, expand=True)
    assert isinstance(entry, tk.Entry)


def test_build_form_returns_all_widgets(root):
    body = tk.Frame(root)
    form = build_form(body)
    assert isinstance(form, FormWidgets)
    assert isinstance(form.start_btn, tk.Button)
    assert isinstance(form.reset_btn, tk.Button)
    assert isinstance(form.topic_entry, tk.Entry)


def test_build_header_and_log_panel(root):
    build_header(root)
    body = tk.Frame(root)
    log = build_log_panel(body)
    log.insert(tk.END, "hello\n")
    assert "hello" in log.get("1.0", tk.END)


def test_build_layout_returns_gui_widgets(root):
    widgets = build_layout(root)
    assert isinstance(widgets, GuiWidgets)
    assert isinstance(widgets.log, tk.Text)
    assert isinstance(widgets.pro_entry, tk.Entry)
