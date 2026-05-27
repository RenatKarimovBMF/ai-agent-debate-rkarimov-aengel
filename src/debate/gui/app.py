from __future__ import annotations

import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from debate.config import load_config
from debate.env_loader import ensure_env_loaded, gemini_key_hint
from debate.gui.layout import GuiWidgets, build_layout
from debate.gui.runner import start_debate_thread
from debate.gui.theme import BG
from sdk.llm_client import LlmClient


class DebateGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Agent Debate — Exercise 02")
        self.geometry("900x720")
        self.minsize(760, 600)
        self.configure(bg=BG)

        self._running = False
        self._log_queue: queue.Queue[str] = queue.Queue()
        self._widgets = build_layout(self)

        self._widgets.start_btn.config(command=self._on_start)
        self._widgets.reset_btn.config(command=self._load_defaults)
        self._widgets.clear_btn.config(command=self._clear_log)

        ensure_env_loaded()
        self._load_defaults()
        self._refresh_env_status()
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

    def _refresh_env_status(self) -> None:
        ensure_env_loaded()

        try:
            cfg = load_config()
            client = LlmClient(
                cli_command=cfg.agents.cli_command,
                workdir=cfg.project_root / cfg.agents.workdir,
                gemini_model=cfg.llm.gemini_model,
                gemini_fallback_models=cfg.llm.gemini_model_fallbacks,
                use_google_search=cfg.llm.use_google_search,
            )
            provider = client.active_provider()
            hint = gemini_key_hint()
            self.w.env_status.config(text=f"LLM: {provider} | {hint}")
        except Exception as exc:
            self.w.env_status.config(text=f"LLM setup error: {exc}")

    def _validate(self) -> tuple[str, str, str] | None:
        pro = self.w.pro_entry.get().strip()
        con = self.w.con_entry.get().strip()
        topic = self.w.topic_entry.get().strip()

        if not pro or not con or not topic:
            messagebox.showwarning("Missing fields", "Fill in both sides and the debate question.")
            return None

        if pro.lower() == con.lower():
            messagebox.showwarning("Same sides", "Pro and Con must be different.")
            return None

        return pro, con, topic

    def _set_running_ui(self, running: bool) -> None:
        state = tk.DISABLED if running else tk.NORMAL
        self.w.start_btn.config(state=state)
        self.w.reset_btn.config(state=state)
        self.w.pro_entry.config(state=state)
        self.w.con_entry.config(state=state)
        self.w.topic_entry.config(state=state)

    def _on_start(self) -> None:
        if self._running:
            return

        values = self._validate()
        if not values:
            return

        pro, con, topic = values

        self._running = True
        self._set_running_ui(True)
        self._set_status("Debate running… this can take several minutes.")

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
        )

    def _on_done(self, verdict_path: Path | None, error: Exception | None) -> None:
        self._running = False
        self._set_running_ui(False)

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
