from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from debate.gui.form import FormWidgets, build_form
from debate.gui.theme import ACCENT, BG, MUTED, PANEL, TEXT

__all__ = ["FormWidgets", "build_form", "build_header", "build_log_panel"]


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
