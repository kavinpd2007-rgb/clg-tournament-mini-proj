"""Reusable summary metric card with a semantic icon accent."""
from __future__ import annotations
import ttkbootstrap as ttk
from .styles import badge_icon, card


class StatCard(ttk.Frame):
    def __init__(self, master, *, label: str, value: str | int = "—", icon: str = "bar-chart", footnote: str = "", bootstyle: str = "primary"):
        super().__init__(master, style="Card.TFrame", padding=10)
        self.columnconfigure(1, weight=1)
        badge = ttk.Frame(self, width=34, height=34, padding=7, bootstyle=bootstyle)
        badge.grid(row=0, column=0, rowspan=2, padx=(0, 8), sticky="n")
        badge.grid_propagate(False)
        badge_icon(badge, icon, bootstyle, size=16).pack(expand=True)
        self.value_label = ttk.Label(self, text=str(value), style="MetricValue.TLabel")
        self.value_label.grid(row=0, column=1, sticky="w")
        self.label_label = ttk.Label(self, text=label.upper(), style="MetricLabel.TLabel")
        self.label_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 0))
        self.footnote_label = ttk.Label(self, text=footnote, style="Caption.TLabel")
        if footnote:
            self.footnote_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

    def set_value(self, value: str | int, footnote: str | None = None):
        self.value_label.configure(text=str(value))
        if footnote is not None:
            self.footnote_label.configure(text=footnote)

