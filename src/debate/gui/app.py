from __future__ import annotations

import queue
import threading
import tkinter as tk

from debate.config import load_config
from debate.env_loader import ensure_env_loaded
from debate.gui.controls import DebateControlMixin
from debate.gui.env_check import resolve_provider_status
from debate.gui.layout import GuiWidgets, build_layout
from debate.gui.theme import BG


class DebateGui(DebateControlMixin, tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Agent Debate — Exercise 02")
        self.geometry("900x720")
        self.minsize(760, 600)
        self.configure(bg=BG)

        self._running = False
        self._pulse_on = False
        self._cancel = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue()
        self._widgets = build_layout(self)

        self._widgets.start_btn.config(command=self._on_start)
        self._widgets.reset_btn.config(command=self._load_defaults)
        self._widgets.clear_btn.config(command=self._clear_log)

        ensure_env_loaded()
        self._load_defaults()
        self.w.env_status.config(text=resolve_provider_status())
        self._log("Tip: Terminal mode still works: python -m debate.main")
        self._log("Live progress will appear here after you press Start debate.")
        self.after(100, self._drain_log_queue)

    @property
    def w(self) -> GuiWidgets:
        return self._widgets

    def _load_defaults(self) -> None:
        cfg = load_config()

        self.w.pro_entry.delete(0, tk.END)
        self.w.pro_entry.insert(0, cfg.debate.pro_side)

        self.w.con_entry.delete(0, tk.END)
        self.w.con_entry.insert(0, cfg.debate.con_side)

        self.w.topic_entry.delete(0, tk.END)
        self.w.topic_entry.insert(0, cfg.debate.topic)

    def _log(self, msg: str) -> None:
        self.w.log.insert(tk.END, msg + "\n")
        self.w.log.see(tk.END)

    def _clear_log(self) -> None:
        self.w.log.delete("1.0", tk.END)

    def _queue_log(self, msg: str) -> None:
        self._log_queue.put(msg)

    def _drain_log_queue(self) -> None:
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self._log(msg)

        self.after(100, self._drain_log_queue)

    def _set_status(self, msg: str) -> None:
        self.w.status.config(text=msg)
