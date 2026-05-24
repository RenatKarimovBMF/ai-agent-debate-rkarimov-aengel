"""
Optional debate launcher GUI (Exercise 02 §8.6 — GUI allowed; terminal still required).

Run:
    python -m debate.gui

or:
    python -m debate.main --gui
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

from debate.config import load_config, with_custom_debate
from debate.env_loader import ensure_env_loaded, gemini_key_hint
from debate.orchestrator import DebateOrchestrator
from sdk.llm_client import LlmClient

BG = "#0f0f1a"
PANEL = "#1a1a2e"
ACCENT = "#c9a227"
TEXT = "#eaeaea"
MUTED = "#8a8a9a"
VS_COLOR = "#e94560"


class DebateGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Agent Debate — Exercise 02")
        self.geometry("900x720")
        self.minsize(760, 600)
        self.configure(bg=BG)

        self._running = False
        self._log_queue: queue.Queue[str] = queue.Queue()

        self._build_ui()
        ensure_env_loaded()
        self._load_defaults()
        self._refresh_env_status()
        self.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=PANEL, padx=24, pady=20)
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

        body = tk.Frame(self, bg=BG, padx=24, pady=12)
        body.pack(fill=tk.BOTH, expand=True, padx=16)

        sides = tk.Frame(body, bg=BG)
        sides.pack(fill=tk.X, pady=(8, 16))

        self.pro_entry = self._labeled_entry(sides, "Side A (Pro)", side=tk.LEFT, expand=True)

        vs = tk.Label(sides, text="VS", font=("Segoe UI", 18, "bold"), fg=VS_COLOR, bg=BG)
        vs.pack(side=tk.LEFT, padx=12, pady=28)

        self.con_entry = self._labeled_entry(sides, "Side B (Con)", side=tk.LEFT, expand=True)

        q_frame = tk.Frame(body, bg=BG)
        q_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            q_frame,
            text="Debate question",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        ).pack(anchor=tk.W)

        self.topic_entry = tk.Entry(
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
        self.topic_entry.pack(fill=tk.X, ipady=8, pady=(4, 0))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill=tk.X, pady=8)

        self.start_btn = tk.Button(
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
            command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT)

        self.reset_btn = tk.Button(
            btn_row,
            text="Reset defaults",
            font=("Segoe UI", 10),
            bg=PANEL,
            fg=TEXT,
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._load_defaults,
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(12, 0))

        self.clear_btn = tk.Button(
            btn_row,
            text="Clear log",
            font=("Segoe UI", 10),
            bg=PANEL,
            fg=TEXT,
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._clear_log,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(12, 0))

        self.status = tk.Label(body, text="Ready", font=("Segoe UI", 9), fg=MUTED, bg=BG)
        self.status.pack(anchor=tk.W, pady=(4, 0))

        self.env_status = tk.Label(body, text="", font=("Segoe UI", 8), fg=MUTED, bg=BG)
        self.env_status.pack(anchor=tk.W, pady=(0, 4))

        log_frame = tk.LabelFrame(
            body,
            text=" Live debate flow ",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=BG,
            labelanchor=tk.NW,
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.log = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            font=("Consolas", 9),
            bg="#12121f",
            fg="#b8b8c8",
            insertbackground=TEXT,
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._log("Tip: Terminal mode still works: python -m debate.main")
        self._log("Live progress will appear here after you press Start debate.")

        footer = tk.Label(
            self,
            text="Renat Karimov & Alon Engel · Haifa University · Exercise 02",
            font=("Segoe UI", 8),
            fg="#555566",
            bg=BG,
        )
        footer.pack(pady=(0, 12))

    def _labeled_entry(self, parent: tk.Frame, label: str, side: str, expand: bool) -> tk.Entry:
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

    def _load_defaults(self) -> None:
        cfg = load_config()

        self.pro_entry.delete(0, tk.END)
        self.pro_entry.insert(0, cfg.debate.pro_side)

        self.con_entry.delete(0, tk.END)
        self.con_entry.insert(0, cfg.debate.con_side)

        self.topic_entry.delete(0, tk.END)
        self.topic_entry.insert(0, cfg.debate.topic)

    def _log(self, msg: str) -> None:
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def _clear_log(self) -> None:
        self.log.delete("1.0", tk.END)

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
        self.status.config(text=msg)

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
            self.env_status.config(text=f"LLM: {provider} | {hint}")
        except Exception as exc:
            self.env_status.config(text=f"LLM setup error: {exc}")

    def _validate(self) -> tuple[str, str, str] | None:
        pro = self.pro_entry.get().strip()
        con = self.con_entry.get().strip()
        topic = self.topic_entry.get().strip()

        if not pro or not con or not topic:
            messagebox.showwarning("Missing fields", "Fill in both sides and the debate question.")
            return None

        if pro.lower() == con.lower():
            messagebox.showwarning("Same sides", "Pro and Con must be different.")
            return None

        return pro, con, topic

    def _set_running_ui(self, running: bool) -> None:
        state = tk.DISABLED if running else tk.NORMAL
        self.start_btn.config(state=state)
        self.reset_btn.config(state=state)
        self.pro_entry.config(state=state)
        self.con_entry.config(state=state)
        self.topic_entry.config(state=state)

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
        self._log(f"PRO: {pro}")
        self._log(f"CON: {con}")
        self._log("Please wait. Each agent turn calls the LLM/API.")

        def worker() -> None:
            try:
                ensure_env_loaded()
                base = load_config()
                config = with_custom_debate(base, pro_side=pro, con_side=con, topic=topic)

                orch = DebateOrchestrator(config, progress_callback=self._queue_log)
                orch.start_watchdogs()

                try:
                    path = orch.run()
                    self.after(0, lambda p=path: self._on_done(p, None))
                finally:
                    orch.stop_watchdogs()

            except Exception as exc:
                self.after(0, lambda err=exc: self._on_done(None, err))

        threading.Thread(target=worker, daemon=True).start()

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


def main() -> int:
    ensure_env_loaded()
    app = DebateGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())