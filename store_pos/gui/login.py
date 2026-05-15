"""Login window for the POS application."""

from __future__ import annotations

import tkinter as tk

from .. import database
from ..config import APP_TITLE, STORE_NAME


# Color palette
LEFT_BG = "#1E293B"
LEFT_TEXT = "#F8FAFC"
LEFT_MUTED = "#94A3B8"
RIGHT_BG = "#FFFFFF"
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
TEXT = "#1E293B"
SUBTLE = "#64748B"
MUTED = "#94A3B8"
BORDER = "#E2E8F0"
INPUT_BG = "#F8FAFC"
ERROR_COLOR = "#DC2626"


class LoginWindow(tk.Tk):
    """Full-screen login with branding panel on the left and form on the right."""

    def __init__(self, on_success) -> None:
        super().__init__()
        self.on_success = on_success
        self.login_succeeded = False
        self.title(f"{APP_TITLE} - Login")
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._open_maximized()
        self.configure(bg=RIGHT_BG)

        # Root container — two halves
        container = tk.Frame(self, bg=RIGHT_BG)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=3)
        container.rowconfigure(0, weight=1)

        # ===== LEFT PANEL — branding / description =====
        left = tk.Frame(container, bg=LEFT_BG)
        left.grid(row=0, column=0, sticky="nsew")

        # Center content vertically
        left_spacer_top = tk.Frame(left, bg=LEFT_BG)
        left_spacer_top.pack(fill="both", expand=True)

        left_content = tk.Frame(left, bg=LEFT_BG, padx=48)
        left_content.pack()

        tk.Label(
            left_content,
            text=STORE_NAME,
            bg=LEFT_BG,
            fg=LEFT_TEXT,
            font=("Segoe UI Bold", 28),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            left_content,
            text="Point of Sale System",
            bg=LEFT_BG,
            fg=LEFT_MUTED,
            font=("Segoe UI", 13),
            anchor="w",
        ).pack(fill="x", pady=(4, 28))

        # Divider line
        tk.Frame(left_content, bg="#334155", height=1).pack(fill="x", pady=(0, 24))

        description = (
            "Manage your store inventory, process customer\n"
            "orders, track sales performance, and generate\n"
            "reports — all from one place."
        )
        tk.Label(
            left_content,
            text=description,
            bg=LEFT_BG,
            fg=LEFT_MUTED,
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(0, 32))

        # Feature bullets
        features = [
            "Real-time inventory tracking",
            "Quick order processing",
            "Automated email receipts",
            "PDF report generation",
        ]
        for feat in features:
            row = tk.Frame(left_content, bg=LEFT_BG)
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text="•",
                bg=LEFT_BG,
                fg=PRIMARY,
                font=("Segoe UI", 12),
            ).pack(side="left", padx=(0, 10))
            tk.Label(
                row,
                text=feat,
                bg=LEFT_BG,
                fg=LEFT_TEXT,
                font=("Segoe UI", 11),
                anchor="w",
            ).pack(side="left")

        left_spacer_bottom = tk.Frame(left, bg=LEFT_BG)
        left_spacer_bottom.pack(fill="both", expand=True)

        # Footer on left panel
        tk.Label(
            left,
            text=f"© 2025 {STORE_NAME}. All rights reserved.",
            bg=LEFT_BG,
            fg="#475569",
            font=("Segoe UI", 9),
        ).pack(side="bottom", pady=24)

        # ===== RIGHT PANEL — login form =====
        right = tk.Frame(container, bg=RIGHT_BG)
        right.grid(row=0, column=1, sticky="nsew")

        # Center the form vertically and horizontally
        right.rowconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(2, weight=1)

        form = tk.Frame(right, bg=RIGHT_BG, width=360)
        form.grid(row=1, column=1)
        form.grid_propagate(True)

        # Form header
        tk.Label(
            form,
            text="Welcome back",
            bg=RIGHT_BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 20),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        tk.Label(
            form,
            text="Sign in to your account to continue",
            bg=RIGHT_BG,
            fg=SUBTLE,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", pady=(0, 32))

        # Username field
        self.username_var = tk.StringVar(value="admin")
        self._username_entry = self._create_field(form, "Username", self.username_var)

        # Password field
        self.password_var = tk.StringVar()
        self._password_entry = self._create_field(form, "Password", self.password_var, show="●")

        # Error label
        self.error_var = tk.StringVar()
        tk.Label(
            form,
            textvariable=self.error_var,
            bg=RIGHT_BG,
            fg=ERROR_COLOR,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Sign in button
        self.btn = tk.Button(
            form,
            text="Sign In",
            command=self._attempt_login,
            bg=PRIMARY,
            fg="#FFFFFF",
            activebackground=PRIMARY_HOVER,
            activeforeground="#FFFFFF",
            font=("Segoe UI Semibold", 12),
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=12,
            takefocus=False,
        )
        self.btn.pack(fill="x", ipady=3, pady=(6, 0))
        self.btn.bind("<Enter>", lambda _: self.btn.configure(bg=PRIMARY_HOVER))
        self.btn.bind("<Leave>", lambda _: self.btn.configure(bg=PRIMARY))

        # Hint
        tk.Label(
            form,
            text="Default: admin / admin123",
            bg=RIGHT_BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(pady=(20, 0))

        # Key bindings
        self.bind("<Return>", lambda _: self._attempt_login())
        self._username_entry.focus_set()
        self.after(10, self._show_window)

    # ------------------------------------------------------------------
    def _create_field(self, parent: tk.Frame, label: str, var: tk.StringVar, show: str = "") -> tk.Entry:
        """Create a labeled input field and return the Entry widget."""
        tk.Label(
            parent,
            text=label,
            bg=RIGHT_BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        frame = tk.Frame(
            parent,
            bg=INPUT_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
        )
        frame.pack(fill="x", pady=(0, 18))

        entry = tk.Entry(
            frame,
            textvariable=var,
            font=("Segoe UI", 12),
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            bd=0,
            relief="flat",
            show=show,
            width=32,
        )
        entry.pack(fill="x", padx=12, pady=11)
        return entry

    # ------------------------------------------------------------------
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
