"""Application entry point for the Store Inventory & POS System."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import database
from .gui.dashboard import MainApplication
from .gui.login import LoginWindow


def configure_tk_environment() -> None:
    """Set Tcl/Tk environment variables when Python does not discover them automatically."""
    python_root = Path(sys.executable).resolve().parent
    tcl_root = python_root / "tcl"
    tcl_library = tcl_root / "tcl8.6"
    tk_library = tcl_root / "tk8.6"

    if tcl_library.exists() and not os.environ.get("TCL_LIBRARY"):
        os.environ["TCL_LIBRARY"] = str(tcl_library)
    if tk_library.exists() and not os.environ.get("TK_LIBRARY"):
        os.environ["TK_LIBRARY"] = str(tk_library)


def main() -> None:
    """Initialize the database and start the Tkinter application."""
    configure_tk_environment()
    database.init_db()
    database.seed_demo_data()

    login_window = LoginWindow(on_success=lambda: None)
    login_window.mainloop()

    if not login_window.login_succeeded:
        return

    app = MainApplication()
    app.show_main()
    app.mainloop()


if __name__ == "__main__":
    main()
