from __future__ import annotations

from debate.agents.debater_agent import DebaterAgent


class ConAgent(DebaterAgent):
    """Con-corner debater. Role is fixed; the defended side is assigned by
    the parent at runtime via `apply_assignment`."""
