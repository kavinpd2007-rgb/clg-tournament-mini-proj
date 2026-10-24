"""Shared ttkbootstrap 2.x theme and typography styles."""
from __future__ import annotations
import tkinter.font as tkfont
import ttkbootstrap as ttk

LIGHT_THEME = "bootstrap-light"
DARK_THEME = "bootstrap-dark"


def configure_styles(app: ttk.Window) -> None:
    """Set the application-wide typography scale and reusable surface styles."""
    family = "Segoe UI" if "Segoe UI" in tkfont.families(app) else "TkDefaultFont"
    ttk.set_global_family(family)
    style = app.style
    colors = style.colors
    style.configure("TLabel", font=(family, 10))
    style.configure("TButton", font=(family, 10), padding=(12, 8))
    style.configure("TEntry", font=(family, 10), padding=(10, 8))
    style.configure("TCombobox", font=(family, 10), padding=(8, 6))
    style.configure("TCheckbutton", font=(family, 10))
    style.configure("Treeview", font=(family, 10), rowheight=32, background=colors.inputbg, fieldbackground=colors.inputbg, borderwidth=0)
    style.configure("Treeview.Heading", font=(family, 10, "bold"), padding=(10, 10), relief="flat")
    style.map("Treeview", background=[("selected", colors.primary)], foreground=[("selected", colors.light)])
    style.configure("PageTitle.TLabel", font=(family, 20, "bold"))
    style.configure("SectionTitle.TLabel", font=(family, 13, "bold"))
    style.configure("Body.TLabel", font=(family, 10))
    style.configure("Caption.TLabel", font=(family, 9), foreground=colors.secondary)
    style.configure("MetricValue.TLabel", font=(family, 24, "bold"))
    style.configure("FormLabel.TLabel", font=(family, 10, "bold"))
    style.configure("ToastTitle.TLabel", font=(family, 10, "bold"))
    style.configure("MetricLabel.TLabel", font=(family, 9, "bold"), foreground=colors.secondary)
    style.configure("Card.TFrame", background=colors.inputbg, bordercolor=colors.border, borderwidth=1, relief="solid")
    style.configure("Subtle.TFrame", background="#f3f6fb" if style.theme_use() == LIGHT_THEME else "#171d27")
    style.configure("Sidebar.TFrame", background=colors.bg)
    style.configure("SidebarTitle.TLabel", font=(family, 9, "bold"), foreground=colors.secondary)
    style.configure("UserChip.TFrame", background=colors.inputbg)
    for accent in ("primary", "secondary", "success", "info", "warning", "danger"):
        style.configure(f"{accent}.BadgeIcon.TLabel", background=getattr(colors, accent), foreground=colors.light, borderwidth=0)
    style.configure("TSeparator", background=colors.border)
    style.map("TButton", focuscolor=[("focus", colors.primary)])
    if not getattr(app, "_sports_cursor_bound", False):
        app.bind_class("TButton", "<Enter>", lambda event: event.widget.configure(cursor="hand2"))
        app.bind_class("TButton", "<Leave>", lambda event: event.widget.configure(cursor="arrow"))
        app._sports_cursor_bound = True
    if not getattr(app, "_sports_styles_bound", False):
        app.bind("<<ThemeChanged>>", lambda _event: configure_styles(app), add="+")
        app._sports_styles_bound = True


def card(master, *, padding: int = 16, **kwargs):
    """Construct a standard bordered card using the active theme palette."""
    return ttk.Frame(master, style="Card.TFrame", padding=padding, **kwargs)






def badge_icon(master, name: str, accent: str, *, size: int = 18):
    """Return a Bootstrap Icon label blended into its colored badge surface."""
    return ttk.Label(master, text="", icon=name, icon_size=size, style=f"{accent}.BadgeIcon.TLabel")
