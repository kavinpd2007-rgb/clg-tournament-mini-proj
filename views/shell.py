"""Authenticated application shell and main navigation."""
from __future__ import annotations
import logging
import tkinter.messagebox as messagebox
from collections.abc import Callable
from typing import Any
import ttkbootstrap as ttk
from db.errors import DatabaseOperationError
from services.auth import UserSession
from views.widgets.feedback import Toast, Tooltip
from views.widgets.preferences import save_theme
from views.widgets.sidebar import NAV_ITEMS, Sidebar
from views.widgets.status_bar import StatusBar
from views.widgets.styles import DARK_THEME

LOGGER = logging.getLogger(__name__)


class ApplicationShell(ttk.Frame):
    def __init__(self, master, user: UserSession, tasks, on_logout: Callable[[], None]):
        super().__init__(master)
        self.user, self.tasks, self._on_logout = user, tasks, on_logout
        self._page_factories: dict[str, Callable[[Any], ttk.Frame]] = {}
        self._active_key = "Dashboard"
        self._pages: dict[str, ttk.Frame] = {}
        self._build()
        self.show_page("Dashboard")
        self._bind_shortcuts()

    @property
    def can_write(self) -> bool:
        return self.user.can_write

    def register_page(self, key: str, factory: Callable[[Any], ttk.Frame]) -> None:
        self._page_factories[key] = factory
        if key == self._active_key:
            self.show_page(key)

    def show_page(self, key: str) -> None:
        if key not in {name for name, _icon in NAV_ITEMS}:
            return
        factory = self._page_factories.get(key)
        if factory is None:
            return
        previous = self._pages.pop(self._active_key, None)
        if previous is not None:
            previous.destroy()
        page = factory(self.content)
        page.grid(row=0, column=0, sticky="nsew")
        self._pages[key] = page
        self._active_key = key
        self.sidebar.set_active(key)
        self.page_title.configure(text=key)

    def set_status(self, text: str, *, success: bool = False) -> None:
        self.status_bar.show(text, success=success)

    def run_task(self, work: Callable[[], Any], on_success: Callable[[Any], None], on_error: Callable[[BaseException], None] | None = None) -> None:
        self.status_bar.show("Working…")
        self.tasks.submit(work, lambda result: on_success(result), lambda error: self._task_failed(error, work, on_success, on_error))

    def focus_search(self) -> None:
        page = self._pages.get(self._active_key)
        if page is not None and hasattr(page, "focus_search"):
            page.focus_search()

    def add_current(self) -> None:
        page = self._pages.get(self._active_key)
        if self.can_write and page is not None and hasattr(page, "add_new"):
            page.add_new()

    def delete_current(self) -> None:
        page = self._pages.get(self._active_key)
        if self.can_write and page is not None and hasattr(page, "delete_selected"):
            page.delete_selected()

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.sidebar = Sidebar(self, self.show_page, self.user, self._on_logout)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        main = ttk.Frame(self)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=0)
        main.grid_columnconfigure(0, weight=1)
        topbar = ttk.Frame(main, padding=(24, 16))
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)
        self.page_title = ttk.Label(topbar, text="Dashboard", style="PageTitle.TLabel")
        self.page_title.grid(row=0, column=0, sticky="w")
        controls = ttk.Frame(topbar)
        controls.grid(row=0, column=1, sticky="e")
        dark = self.winfo_toplevel().style.theme_use() == DARK_THEME
        self.theme_button = ttk.Button(controls, text="", icon="sun" if dark else "moon-stars-fill", bootstyle="secondary" if dark else "light", command=self._toggle_theme, width=4)
        self.theme_button.pack(side="left", padx=(0, 10))
        self.theme_tooltip = Tooltip(self.theme_button, "Switch to light mode" if dark else "Switch to dark mode")
        chip = ttk.Frame(controls, style="UserChip.TFrame", padding=(10, 6))
        chip.pack(side="left")
        ttk.Label(chip, text="", icon="person-circle", icon_size=18, bootstyle="primary").pack(side="left", padx=(0, 7))
        ttk.Label(chip, text=self.user.username, style="Body.TLabel").pack(side="left", padx=(0, 8))
        ttk.Label(chip, text=self.user.role, bootstyle="info", padding=(7, 3)).pack(side="left")
        ttk.Separator(main).grid(row=1, column=0, sticky="ew")
        main.grid_rowconfigure(2, weight=1)
        self.content = ttk.Frame(main, padding=0)
        self.content.grid(row=2, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _toggle_theme(self) -> None:
        root = self.winfo_toplevel()
        root.toggle_theme()
        theme = root.style.theme_use()
        save_theme(theme)
        dark = theme == DARK_THEME
        self.theme_button.configure(icon="sun" if dark else "moon-stars-fill", bootstyle="secondary" if dark else "light")
        self.theme_tooltip.text = "Switch to light mode" if dark else "Switch to dark mode"

    def _task_failed(self, error: BaseException, work: Callable[[], Any], on_success: Callable[[Any], None], on_error: Callable[[BaseException], None] | None = None) -> None:
        if isinstance(error, DatabaseOperationError):
            LOGGER.error("Database operation failed: errno=%s retryable=%s", error.errno, error.retryable)
            if error.retryable and messagebox.askretrycancel("Connection lost", str(error), parent=self.winfo_toplevel()):
                self.run_task(work, on_success, on_error)
                return
            Toast.show(self, "The database operation failed. Check the connection and retry.", title="Connection issue", success=False)
            if on_error is not None:
                on_error(error)
            else:
                self.status_bar.show(str(error))
            return
        LOGGER.error("Background operation failed: type=%s", type(error).__name__)
        Toast.show(self, "The action could not be completed. Check logs/app.log for details.", title="Action failed", success=False)
        if on_error is not None:
            on_error(error)
        else:
            self.status_bar.show("The operation failed. Check logs/app.log for details.")

    def _bind_shortcuts(self) -> None:
        root = self.winfo_toplevel()
        root.bind_all("<Control-f>", lambda _event: self.focus_search())
        root.bind_all("<Control-F>", lambda _event: self.focus_search())
        root.bind_all("<Control-n>", lambda _event: self.add_current())
        root.bind_all("<Control-N>", lambda _event: self.add_current())
        root.bind_all("<Delete>", lambda _event: self.delete_current())
        for index, (key, _icon) in enumerate(NAV_ITEMS, start=1):
            root.bind_all(f"<Alt-Key-{index}>", lambda _event, page=key: self.show_page(page))



