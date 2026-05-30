from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable

from debate.config import AppConfig
from debate.models import AgentRole
from debate.orchestrator.child_worker import child_worker
from debate.orchestrator.parent_worker import parent_worker


class DebateProcessPool:
    def __init__(self, ctx: mp.context.BaseContext, config: AppConfig, session_id: str) -> None:
        self._ctx = ctx
        self._config = config
        self._session_id = session_id

        self.parent_commands: mp.Queue = ctx.Queue()
        self.events: mp.Queue = ctx.Queue()
        self.parent_to_pro: mp.Queue = ctx.Queue()
        self.pro_to_parent: mp.Queue = ctx.Queue()
        self.parent_to_con: mp.Queue = ctx.Queue()
        self.con_to_parent: mp.Queue = ctx.Queue()

        self.processes: dict[str, mp.Process] = {}

    def start_all(self, on_started: Callable[[str, int], None]) -> None:
        self.processes["pro"] = self._spawn_child("pro", AgentRole.PRO.value)
        self.processes["con"] = self._spawn_child("con", AgentRole.CON.value)
        self.processes["parent"] = self._ctx.Process(  # type: ignore[attr-defined]
            name=f"debate-parent-{self._session_id}",
            target=parent_worker,
            args=(
                self._config,
                self._session_id,
                self.parent_commands,
                self.events,
                self.parent_to_pro,
                self.pro_to_parent,
                self.parent_to_con,
                self.con_to_parent,
            ),
        )

        for name, process in self.processes.items():
            process.start()
            on_started(name, process.pid or 0)

    def _spawn_child(self, label: str, role_value: str) -> mp.Process:
        if label == "pro":
            inbound, outbound = self.parent_to_pro, self.pro_to_parent
        else:
            inbound, outbound = self.parent_to_con, self.con_to_parent

        return self._ctx.Process(  # type: ignore[attr-defined]
            name=f"debate-{label}-{self._session_id}",
            target=child_worker,
            args=(
                role_value,
                self._config,
                self._session_id,
                inbound,
                outbound,
                self.events,
            ),
        )

    def restart_child(self, name: str, on_started: Callable[[str, int], None]) -> None:
        if name not in {"pro", "con"}:
            return

        old = self.processes.get(name)
        if old is not None and old.is_alive():
            old.terminate()
            old.join(timeout=3)

        role = AgentRole.PRO.value if name == "pro" else AgentRole.CON.value
        process = self._spawn_child(name, role)
        process.start()
        self.processes[name] = process
        on_started(name, process.pid or 0)

    def stop_all(self, on_terminate: Callable[[str], None]) -> None:
        from debate.orchestrator.commands import STOP

        for q in (self.parent_to_pro, self.parent_to_con):
            try:
                q.put({"type": STOP})
            except Exception:
                pass

        for name, process in self.processes.items():
            if process.is_alive():
                process.join(timeout=3)

            if process.is_alive():
                on_terminate(name)
                process.terminate()
                process.join(timeout=3)
