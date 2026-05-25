from __future__ import annotations

import tkinter as tk

from debate.gui.theme import ACCENT, BG, MUTED, PANEL, TEXT


def labeled_entry(parent: tk.Frame, label: str, side: str, expand: bool) -> tk.Entry:
    frame = tk.Frame(parent, bg=BG)
    frame.pack(side=side, fill=tk.BOTH, expand=expand)

    tk.Label(frame, text=label, font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(anchor=tk.W)

    entry = tk.Entry(
        frame,
        font=("Segoe UI", 12),
        bg=PANEL,
        fg=TEXT,
        insertbackground=TEXT,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground="#333355",
        highlightcolor=ACCENT,
    )
    entry.pack(fill=tk.X, ipady=8, pady=(4, 0))
    return entry
