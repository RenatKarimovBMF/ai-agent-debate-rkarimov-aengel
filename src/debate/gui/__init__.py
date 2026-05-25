import sys

from debate.env_loader import ensure_env_loaded
from debate.gui.app import DebateGui


def main() -> int:
    ensure_env_loaded()
    app = DebateGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
