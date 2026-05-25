from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import scrolledtext

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


def build_header(root: tk.Tk) -> None:
    header = tk.Frame(root, bg=PANEL, padx=24, pady=20)
    header.pack(fill=tk.X, padx=16, pady=(16, 8))

    tk.Label(
        header,
        text="AI Agent Debate",
        font=("Segoe UI", 22, "bold"),
        fg=ACCENT,
        bg=PANEL,
    ).pack(anchor=tk.W)

    tk.Label(
        header,
        text="Set two sides and a debate question — then watch the mediated agent debate live.",
        font=("Segoe UI", 10),
        fg=MUTED,
        bg=PANEL,
    ).pack(anchor=tk.W, pady=(4, 0))


def build_form(body: tk.Frame) -> FormWidgets:
    sides = tk.Frame(body, bg=BG)
    sides.pack(fill=tk.X, pady=(8, 16))

    pro_entry = labeled_entry(sides, "Side A (Pro)", side=tk.LEFT, expand=True)

    tk.Label(sides, text="VS", font=("Segoe UI", 18, "bold"), fg=VS_COLOR, bg=BG).pack(
        side=tk.LEFT, padx=12, pady=28
    )

    con_entry = labeled_entry(sides, "Side B (Con)", side=tk.LEFT, expand=True)

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

    btn_row = tk.Frame(body, bg=BG)
    btn_row.pack(fill=tk.X, pady=8)

    start_btn = tk.Button(
        btn_row,
        text="Start debate",
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
    start_btn.pack(side=tk.LEFT)

    reset_btn = tk.Button(
        btn_row,
        text="Reset defaults",
        font=("Segoe UI", 10),
        bg=PANEL,
        fg=TEXT,
        relief=tk.FLAT,
        padx=12,
        pady=8,
        cursor="hand2",
    )
    reset_btn.pack(side=tk.LEFT, padx=(12, 0))

    clear_btn = tk.Button(
        btn_row,
        text="Clear log",
        font=("Segoe UI", 10),
        bg=PANEL,
        fg=TEXT,
        relief=tk.FLAT,
        padx=12,
        pady=8,
        cursor="hand2",
    )
    clear_btn.pack(side=tk.LEFT, padx=(12, 0))

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


def build_log_panel(body: tk.Frame) -> scrolledtext.ScrolledText:
    log_frame = tk.LabelFrame(
        body,
        text=" Live debate flow ",
        font=("Segoe UI", 9),
        fg=MUTED,
        bg=BG,
        labelanchor=tk.NW,
    )
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    log = scrolledtext.ScrolledText(
        log_frame,
        height=20,
        font=("Consolas", 9),
        bg="#12121f",
        fg="#b8b8c8",
        insertbackground=TEXT,
        relief=tk.FLAT,
        wrap=tk.WORD,
    )
    log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    return log
