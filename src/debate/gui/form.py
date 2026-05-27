from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from debate.gui.theme import ACCENT, BG, MUTED, PANEL, TEXT, VS_COLOR
from debate.gui.widgets import labeled_entry


@dataclass
class FormWidgets:
    pro_entry: tk.Entry
    con_entry: tk.Entry
    topic_entry: tk.Entry
    start_btn: tk.Button
    reset_btn: tk.Button
    clear_btn: tk.Button
    status: tk.Label
    env_status: tk.Label


def _build_sides_row(body: tk.Frame) -> tuple[tk.Entry, tk.Entry]:
    sides = tk.Frame(body, bg=BG)
    sides.pack(fill=tk.X, pady=(8, 16))

    pro_entry = labeled_entry(sides, "Side A (Pro)", side=tk.LEFT, expand=True)

    tk.Label(sides, text="VS", font=("Segoe UI", 18, "bold"), fg=VS_COLOR, bg=BG).pack(
        side=tk.LEFT, padx=12, pady=28
    )

    con_entry = labeled_entry(sides, "Side B (Con)", side=tk.LEFT, expand=True)
    return pro_entry, con_entry


def _build_topic_entry(body: tk.Frame) -> tk.Entry:
    q_frame = tk.Frame(body, bg=BG)
    q_frame.pack(fill=tk.X, pady=(0, 12))

    tk.Label(q_frame, text="Debate question", font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(
        anchor=tk.W
    )

    topic_entry = tk.Entry(
        q_frame,
        font=("Segoe UI", 12),
        bg=PANEL,
        fg=TEXT,
        insertbackground=TEXT,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground="#333355",
        highlightcolor=ACCENT,
    )
    topic_entry.pack(fill=tk.X, ipady=8, pady=(4, 0))
    return topic_entry


def _button(parent: tk.Frame, *, text: str, primary: bool) -> tk.Button:
    if primary:
        return tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT,
            fg="#1a1a1a",
            activebackground="#ddb83a",
            activeforeground="#1a1a1a",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
    return tk.Button(
        parent,
        text=text,
        font=("Segoe UI", 10),
        bg=PANEL,
        fg=TEXT,
        relief=tk.FLAT,
        padx=12,
        pady=8,
        cursor="hand2",
    )


def _build_button_row(body: tk.Frame) -> tuple[tk.Button, tk.Button, tk.Button]:
    btn_row = tk.Frame(body, bg=BG)
    btn_row.pack(fill=tk.X, pady=8)

    start_btn = _button(btn_row, text="Start debate", primary=True)
    start_btn.pack(side=tk.LEFT)

    reset_btn = _button(btn_row, text="Reset defaults", primary=False)
    reset_btn.pack(side=tk.LEFT, padx=(12, 0))

    clear_btn = _button(btn_row, text="Clear log", primary=False)
    clear_btn.pack(side=tk.LEFT, padx=(12, 0))
    return start_btn, reset_btn, clear_btn


def build_form(body: tk.Frame) -> FormWidgets:
    pro_entry, con_entry = _build_sides_row(body)
    topic_entry = _build_topic_entry(body)
    start_btn, reset_btn, clear_btn = _build_button_row(body)

    status = tk.Label(body, text="Ready", font=("Segoe UI", 9), fg=MUTED, bg=BG)
    status.pack(anchor=tk.W, pady=(4, 0))

    env_status = tk.Label(body, text="", font=("Segoe UI", 8), fg=MUTED, bg=BG)
    env_status.pack(anchor=tk.W, pady=(0, 4))

    return FormWidgets(
        pro_entry=pro_entry,
        con_entry=con_entry,
        topic_entry=topic_entry,
        start_btn=start_btn,
        reset_btn=reset_btn,
        clear_btn=clear_btn,
        status=status,
        env_status=env_status,
    )
