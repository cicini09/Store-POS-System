"""Login window for the POS application."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import database
from ..config import APP_TITLE


class LoginWindow(tk.Tk):
    """A standalone login prompt shown before the main window."""

    def __init__(self, on_success) -> None:
        super().__init__()
        self.on_success = on_success
        self.login_succeeded = False
        self.title(f"{APP_TITLE} - Login")
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._open_maximized()

        shell = ttk.Frame(self, padding=24)
        shell.pack(fill="both", expand=True)

        container = ttk.Frame(shell, padding=24)
        container.place(relx=0.5, rely=0.42, anchor="center")

        ttk.Label(
            container,
            text="Admin Login",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        ttk.Label(container, text="Username").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(container, text="Password").grid(row=2, column=0, sticky="w", pady=6)

        self.username_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar()
        self.error_var = tk.StringVar()

        username_entry = ttk.Entry(container, textvariable=self.username_var, width=30)
        password_entry = ttk.Entry(container, textvariable=self.password_var, width=30, show="*")
        username_entry.grid(row=1, column=1, sticky="ew", pady=6)
        password_entry.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Button(container, text="Login", command=self._attempt_login, takefocus=False).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 6),
        )
        ttk.Label(container, textvariable=self.error_var, foreground="#b42318").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
        )

        container.columnconfigure(1, weight=1)
        username_entry.focus_set()
        self.bind("<Return>", lambda _event: self._attempt_login())
        self.after(10, self._show_window)

    def _attempt_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if database.validate_login(username, password):
            self.login_succeeded = True
            self.on_success()
            self.destroy()
            return
        self.error_var.set("Invalid username or password.")
        self.password_var.set("")

    def _handle_close(self) -> None:
        self.destroy()

    def _show_window(self) -> None:
        self.update_idletasks()
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def _open_maximized(self) -> None:
        try:
            self.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-fullscreen", True)
        except tk.TclError:
            pass
