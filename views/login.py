"""Centered authentication screen with a compact, accessible sign-in card."""
from __future__ import annotations
import tkinter as tk
import ttkbootstrap as ttk
from db.errors import DatabaseOperationError
from db.repositories.users import AppUserRepository
from services.auth import AuthService, AuthenticationError, UserSession
from views.widgets.feedback import Tooltip
from views.widgets.styles import badge_icon, card


class LoginView(ttk.Frame):
    def __init__(self, master, tasks, on_authenticated, on_status, on_retry):
        super().__init__(master, padding=24, style="Subtle.TFrame")
        self._tasks, self._on_authenticated = tasks, on_authenticated
        self._on_status, self._on_retry = on_status, on_retry
        self._password_visible = False
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        card_frame = card(self, padding=32)
        card_frame.configure(width=440, height=500)
        card_frame.grid(row=1, column=0)
        card_frame.grid_propagate(False)
        card_frame.columnconfigure(0, weight=1)
        mark = ttk.Frame(card_frame, padding=10, bootstyle="primary")
        mark.grid(row=0, column=0, sticky="w")
        badge_icon(mark, "trophy-fill", "primary", size=22).pack()
        ttk.Label(card_frame, text="College Sports Tournament Manager", style="PageTitle.TLabel", wraplength=360).grid(row=1, column=0, sticky="w", pady=(20, 6))
        ttk.Label(card_frame, text="Sign in to manage teams, fixtures and results.", style="Caption.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 24))
        ttk.Label(card_frame, text="Username *", style="SectionTitle.TLabel").grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.username = ttk.Entry(card_frame)
        self.username.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(card_frame, text="Password *", style="SectionTitle.TLabel").grid(row=5, column=0, sticky="w", pady=(0, 6))
        password_row = ttk.Frame(card_frame)
        password_row.grid(row=6, column=0, sticky="ew", pady=(0, 10))
        password_row.columnconfigure(0, weight=1)
        self.password = ttk.Entry(password_row, show="•")
        self.password.grid(row=0, column=0, sticky="ew")
        self.visibility_button = ttk.Button(password_row, text="", icon="eye", bootstyle="secondary outline", command=self._toggle_password, width=4)
        self.visibility_button.grid(row=0, column=1, padx=(8, 0))
        self._visibility_tooltip = Tooltip(self.visibility_button, "Show password")
        self.error = ttk.Label(card_frame, text="", bootstyle="danger", wraplength=360, justify="left")
        self.error.grid(row=7, column=0, sticky="w", pady=(0, 12))
        self.signin = ttk.Button(card_frame, text="Sign In", icon="box-arrow-in-right", bootstyle="primary", command=self._submit)
        self.signin.grid(row=8, column=0, sticky="ew", ipady=3)
        self.username.bind("<Return>", lambda _event: self.password.focus_set())
        self.password.bind("<Return>", lambda _event: self._submit())
        self.after(120, self.username.focus_set)

    def _toggle_password(self):
        self._password_visible = not self._password_visible
        self.password.configure(show="" if self._password_visible else "•")
        self.visibility_button.configure(icon="eye-slash" if self._password_visible else "eye")
        self._visibility_tooltip.text = "Hide password" if self._password_visible else "Show password"

    def _submit(self):
        username = self.username.get().strip()
        password = self.password.get()
        self.error.configure(text="")
        if not username or not password:
            self.error.configure(text="Enter both username and password.")
            return
        self.signin.configure(state="disabled", text="Signing in…")
        self._on_status("Checking account…")
        self._tasks.submit(lambda: AuthService(AppUserRepository()).authenticate(username, password), self._success, self._failure)

    def _success(self, session: UserSession):
        self.password.delete(0, "end")
        self._on_status(f"Signed in as {session.username}.", success=True)
        self._on_authenticated(session)

    def _failure(self, error: BaseException):
        self.signin.configure(state="normal", text="Sign In")
        if isinstance(error, AuthenticationError):
            self.error.configure(text=str(error))
        elif isinstance(error, DatabaseOperationError):
            self._on_retry(error, lambda: self._submit())
        else:
            self.error.configure(text="Sign in failed. Check the connection settings and retry.")
        self._on_status("Sign in failed.")




