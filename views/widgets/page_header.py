"""Shared page heading with a role-aware primary action."""
from __future__ import annotations
from collections.abc import Callable
import ttkbootstrap as ttk


class PageHeader(ttk.Frame):
    def __init__(self, master, title: str, description: str, *, action_text: str | None = None, action: Callable[[], None] | None = None, can_write: bool = True):
        super().__init__(master, padding=(0, 0, 0, 16))
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=title, style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=description, style="Caption.TLabel", wraplength=980).grid(row=1, column=0, sticky="w", pady=(4, 0))
        if action_text and action and can_write:
            ttk.Button(self, text=action_text, icon="plus-lg", bootstyle="primary", command=action, width=16).grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0))
