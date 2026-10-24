"""Collapsible, grouped navigation with an account footer."""
from __future__ import annotations
import ttkbootstrap as ttk
from .feedback import Tooltip
from .styles import DARK_THEME, badge_icon

NAV_GROUPS = (
    ("OVERVIEW", (("Dashboard", "speedometer2"),)),
    ("MANAGEMENT", (("Players", "people-fill"), ("Teams", "shield-fill"), ("Sports", "trophy-fill"), ("Tournaments", "calendar3"), ("Venues", "geo-alt-fill"))),
    ("MATCHDAY", (("Matches", "calendar-event-fill"), ("Results", "clipboard2-check-fill"))),
    ("INSIGHTS", (("Reports", "bar-chart-fill"),)),
)
NAV_ITEMS = tuple(item for _group, items in NAV_GROUPS for item in items)


class Sidebar(ttk.Frame):
    def __init__(self, master, on_navigate, user, on_logout, *, expanded=True):
        super().__init__(master, style="Sidebar.TFrame", padding=(8, 8))
        self._on_navigate = on_navigate
        self._user = user
        self._on_logout = on_logout
        self._expanded = expanded
        self._inactive_style = self._inactive_bootstyle()
        self._active = "Dashboard"
        self._buttons = {}
        self.configure(width=224)
        self.grid_propagate(False)
        self._render()
        self.bind("<<ThemeChanged>>", self._theme_changed, add="+")

    def _inactive_bootstyle(self):
        return "secondary" if self.winfo_toplevel().style.theme_use() == DARK_THEME else "light"

    def _theme_changed(self, _event=None):
        self._inactive_style = self._inactive_bootstyle()
        self._render()

    def set_active(self, key):
        self._active = key
        for name, button in self._buttons.items():
            button.configure(bootstyle="primary" if name == key else self._inactive_style)

    def toggle(self):
        self._expanded = not self._expanded
        self.configure(width=224 if self._expanded else 72)
        self._render()

    def _render(self):
        for child in self.winfo_children():
            child.destroy()
        self._buttons.clear()
        brand = ttk.Frame(self, style="Sidebar.TFrame")
        brand.pack(fill="x", pady=(0, 4))
        mark = ttk.Frame(brand, padding=(7, 6), bootstyle="primary")
        mark.pack(side="left", padx=(0, 10))
        badge_icon(mark, "trophy-fill", "primary", size=20).pack()
        if self._expanded:
            branding = ttk.Frame(brand, style="Sidebar.TFrame")
            branding.pack(side="left", fill="x", expand=True)
            ttk.Label(branding, text="COLLEGE SPORTS", style="SidebarTitle.TLabel").pack(anchor="w")
            ttk.Label(branding, text="Tournament Manager", style="SectionTitle.TLabel").pack(anchor="w")
        toggle = ttk.Button(self, text="", icon="layout-sidebar-inset", bootstyle=self._inactive_style, command=self.toggle, width=4, padding=(8, 4))
        toggle.pack(fill="x", pady=(0, 4))
        Tooltip(toggle, "Collapse navigation" if self._expanded else "Expand navigation")
        for group_name, items in NAV_GROUPS:
            if self._expanded:
                ttk.Label(self, text=group_name, style="SidebarTitle.TLabel").pack(anchor="w", padx=(10, 0), pady=(2, 1))
            for key, icon in items:
                button = ttk.Button(
                    self, text=key if self._expanded else "", icon=icon, icon_size=16,
                    compound="left", bootstyle="primary" if key == self._active else self._inactive_style,
                    command=lambda item=key: self._on_navigate(item), padding=(8, 4),
                )
                button.pack(fill="x", pady=0)
                self._buttons[key] = button
                if not self._expanded:
                    Tooltip(button, key)
        footer = ttk.Frame(self, style="Sidebar.TFrame")
        footer.pack(side="bottom", fill="x", pady=(4, 0))
        ttk.Separator(footer).pack(fill="x", pady=(0, 4))
        if self._expanded:
            account = ttk.Frame(footer, style="UserChip.TFrame", padding=8)
            account.pack(fill="x", pady=(0, 4))
            ttk.Label(account, text="", icon="person-circle", icon_size=21, bootstyle="primary").pack(side="left", padx=(0, 8))
            identity = ttk.Frame(account, style="UserChip.TFrame")
            identity.pack(side="left", fill="x", expand=True)
            ttk.Label(identity, text=self._user.username, style="Body.TLabel").pack(anchor="w")
            ttk.Label(identity, text=self._user.role, bootstyle="info", padding=(6, 2)).pack(anchor="w", pady=(3, 0))
            logout_text = "Log out"
        else:
            logout_text = ""
        if self._expanded:
            logout = ttk.Button(footer, text="Log out", bootstyle="danger outline", command=self._on_logout, width=16, padding=(8, 4))
        else:
            logout = ttk.Button(footer, text="", icon="box-arrow-right", bootstyle=self._inactive_style, command=self._on_logout, width=4, icon_only=True, padding=(8, 4))
        self.logout_button = logout
        logout.pack(fill="x")
        if not self._expanded:
            Tooltip(logout, f"Log out · {self._user.username}")



