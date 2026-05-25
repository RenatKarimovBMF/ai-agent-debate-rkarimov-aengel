from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import scrolledtext

from debate.gui.panels import build_form, build_header, build_log_panel
from debate.gui.theme import BG


@dataclass
class GuiWidgets:
    pro_entry: tk.Entry
    con_entry: tk.Entry
    topic_entry: tk.Entry
    start_btn: tk.Button
    reset_btn: tk.Button
    clear_btn: tk.Button
    status: tk.Label
    env_status: tk.Label
    log: scrolledtext.ScrolledText


def build_layout(root: tk.Tk) -> GuiWidgets:
    build_header(root)

    body = tk.Frame(root, bg=BG, padx=24, pady=12)
    body.pack(fill=tk.BOTH, expand=True, padx=16)

    form = build_form(body)
    log = build_log_panel(body)

    tk.Label(
        root,
        text="Renat Karimov & Alon Engel · Haifa University · Exercise 02",
        font=("Segoe UI", 8),
        fg="#555566",
        bg=BG,
    ).pack(pady=(0, 12))

    return GuiWidgets(
        pro_entry=form.pro_entry,
        con_entry=form.con_entry,
        topic_entry=form.topic_entry,
        start_btn=form.start_btn,
        reset_btn=form.reset_btn,
        clear_btn=form.clear_btn,
        status=form.status,
        env_status=form.env_status,
        log=log,
    )
