"""Application entry point."""
from __future__ import annotations

import ctypes
import json
import logging
import re
import sys
from pathlib import Path

import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageTk
import tkinter.messagebox as messagebox

from config import PROJECT_ROOT, configure_logging, load_settings
from db.errors import DatabaseOperationError
from services.auth import UserSession
from views.login import LoginView
from views.matches import MatchesPage
from views.results import ResultsPage
from views.reports import ReportsPage
from views.dashboard import DashboardPage
from views.shell import ApplicationShell
from views.players import PlayersPage
from views.sports import SportsPage
from views.teams import TeamsPage
from views.tournaments import TournamentsPage
from views.venues import VenuesPage
from views.widgets.background import BackgroundTasks
from views.widgets.preferences import load_theme
from views.widgets.styles import configure_styles

LOGGER = logging.getLogger(__name__)
STATE_FILE = PROJECT_ROOT / ".app_state" / "window.json"


def configure_dpi_awareness() -> None:
    """Request per-monitor DPI scaling on Windows where the API is available."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            LOGGER.debug("Windows DPI awareness API is unavailable")


def _restore_geometry() -> str:
    try:
        saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        match = re.fullmatch(r"(\d+)x(\d+)(?:[+-]\d+){0,2}", saved.get("geometry", ""))
        if match:
            width, height = map(int, match.groups())
            if width >= 1100 and height >= 700:
                return f"{width}x{height}"
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return "1200x760"


def _save_geometry(window: ttk.App) -> None:
    try:
        geometry = window.geometry().split("+")[0]
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"geometry": geometry}), encoding="utf-8")
    except OSError:
        LOGGER.warning("Could not save window size")


def _set_window_icon(app: ttk.Window) -> None:
    image = Image.new("RGBA", (64, 64), (10, 88, 202, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 61, 61), radius=15, fill=(10, 88, 202, 255))
    draw.rectangle((20, 21, 44, 26), fill=(255, 255, 255, 255))
    draw.polygon(((22, 26), (42, 26), (39, 39), (34, 44), (30, 44), (25, 39)), fill=(255, 193, 7, 255))
    draw.rectangle((28, 44, 36, 49), fill=(255, 255, 255, 255))
    draw.rectangle((24, 49, 40, 53), fill=(255, 255, 255, 255))
    icon = ImageTk.PhotoImage(image)
    app.iconphoto(True, icon)
    app._sports_window_icon = icon


def main() -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError("This application requires Python 3.11 or newer.")
    settings = load_settings()
    configure_logging(settings)
    configure_dpi_awareness()
    ttk.set_global_family("Segoe UI")
    app = ttk.App(title="College Sports Tournament Manager", theme=load_theme())
    configure_styles(app)
    _set_window_icon(app)
    app.geometry(_restore_geometry())
    app.minsize(1100, 700)
    tasks = BackgroundTasks(app)
    tasks.start()
    state: dict[str, object] = {}

    def status(message: str, *, success: bool = False) -> None:
        shell = state.get("shell")
        if isinstance(shell, ApplicationShell):
            shell.set_status(message, success=success)

    def retry(error: DatabaseOperationError, callback) -> None:
        LOGGER.error("Login database failure: errno=%s retryable=%s", error.errno, error.retryable)
        if error.retryable and messagebox.askretrycancel("Connection lost", str(error), parent=app):
            callback()
        else:
            messagebox.showerror("Database error", str(error), parent=app)

    def show_login() -> None:
        previous = state.pop("login", None)
        if previous is not None:
            previous.destroy()
        view = LoginView(app, tasks, show_shell, status, retry)
        view.grid(row=0, column=0, sticky="nsew")
        state["login"] = view

    def show_shell(user: UserSession) -> None:
        login = state.pop("login", None)
        if login is not None:
            login.destroy()
        shell = ApplicationShell(app, user, tasks, show_login)
        shell.register_page("Dashboard", lambda parent: DashboardPage(parent, shell))
        shell.register_page("Players", lambda parent: PlayersPage(parent, shell))
        shell.register_page("Teams", lambda parent: TeamsPage(parent, shell))
        shell.register_page("Sports", lambda parent: SportsPage(parent, shell))
        shell.register_page("Tournaments", lambda parent: TournamentsPage(parent, shell))
        shell.register_page("Venues", lambda parent: VenuesPage(parent, shell))
        shell.register_page("Matches", lambda parent: MatchesPage(parent, shell))
        shell.register_page("Results", lambda parent: ResultsPage(parent, shell))
        shell.register_page("Reports", lambda parent: ReportsPage(parent, shell))
        shell.grid(row=0, column=0, sticky="nsew")
        state["shell"] = shell

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
    show_login()

    def close() -> None:
        _save_geometry(app)
        tasks.shutdown()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", close)
    LOGGER.info("Starting College Sports Tournament Management System")
    app.mainloop()


if __name__ == "__main__":
    main()








