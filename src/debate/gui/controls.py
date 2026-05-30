from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from debate.gui.env_check import validate_inputs
from debate.gui.runner import start_debate_thread
from debate.orchestrator import DebateCancelled


class DebateControlMixin:
    """Debate lifecycle controls for ``DebateGui`` (start / stop / done + the
    live running indicator).

    The mixin relies on attributes and helpers supplied by ``DebateGui``:
    ``w``, ``_running``, ``_cancel``, ``_pulse_on``, ``_log``, ``_queue_log``,
    ``_set_status``, and Tk's ``after``.
    """

    def _set_running_ui(self, running: bool) -> None:
        # The primary button stays enabled but flips role: Start <-> Stop.
        # State is forced back to NORMAL here so the transient "Stopping…"
        # disabled state set in _on_stop is always cleared on completion.
        if running:
            self.w.start_btn.config(text="Stop debate", command=self._on_stop, state=tk.NORMAL)
        else:
            self.w.start_btn.config(text="Start debate", command=self._on_start, state=tk.NORMAL)

        entry_state = tk.DISABLED if running else tk.NORMAL
        self.w.reset_btn.config(state=entry_state)
        self.w.pro_entry.config(state=entry_state)
        self.w.con_entry.config(state=entry_state)
        self.w.topic_entry.config(state=entry_state)

    def _pulse_indicator(self) -> None:
        """Blink a live indicator while a debate runs; clear it when idle."""
        if not self._running:
            self.w.running_indicator.config(text="")
            return
        self._pulse_on = not self._pulse_on
        dot = "\u25cf" if self._pulse_on else "\u25cb"
        self.w.running_indicator.config(text=f"{dot} Debate running")
        self.after(600, self._pulse_indicator)

    def _on_stop(self) -> None:
        if not self._running:
            return
        self._cancel.set()
        self._set_status("Stopping the debate…")
        self.w.start_btn.config(text="Stopping…", state=tk.DISABLED)
        self._log("")
        self._log("--- Stop requested; ending the debate… ---")

    def _on_start(self) -> None:
        if self._running:
            return

        pro = self.w.pro_entry.get().strip()
        con = self.w.con_entry.get().strip()
        topic = self.w.topic_entry.get().strip()

        error = validate_inputs(pro, con, topic)
        if error:
            messagebox.showwarning("Invalid input", error)
            return

        self._running = True
        self._cancel.clear()
        self._set_running_ui(True)
        self._set_status("Debate running… this can take several minutes.")
        self._pulse_indicator()

        self._log("")
        self._log("--- New debate started ---")
        self._log(f"Question: {topic}")
        self._log(f"Options offered to host: {pro}  |  {con}")
        self._log("(The Parent/Judge assigns each side to a corner at session start.)")
        self._log("Live process logs will appear below: supervisor → parent → pro/con → parent.")

        start_debate_thread(
            pro=pro,
            con=con,
            topic=topic,
            queue_log=self._queue_log,
            on_done=lambda path, err: self.after(0, lambda: self._on_done(path, err)),
            cancel_event=self._cancel,
        )

    def _on_done(self, verdict_path: Path | None, error: Exception | None) -> None:
        self._running = False
        self._set_running_ui(False)
        self.w.running_indicator.config(text="")

        if isinstance(error, DebateCancelled):
            self._set_status("Stopped")
            self._log("")
            self._log("Debate stopped by user before a verdict.")
            return

        if error:
            self._set_status("Error")
            self._log("")
            self._log(f"ERROR: {error}")
            messagebox.showerror("Debate failed", str(error))
            return

        self._set_status("Finished")
        self._log("")
        self._log(f"Debate complete. Verdict saved: {verdict_path}")
        messagebox.showinfo("Done", f"Debate complete.\nVerdict:\n{verdict_path}")
