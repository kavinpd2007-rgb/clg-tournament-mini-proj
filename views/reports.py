"""Report navigation and styled results for the database-defined reports."""
from __future__ import annotations

import ttkbootstrap as ttk
from services.reports import ReportService
from views.widgets.data_table import ColumnSpec, DataTable
from views.widgets.page_header import PageHeader
from views.widgets.styles import DARK_THEME, card

REPORT_COLUMNS = {
    "Standings": (ColumnSpec("tournament_name", "Tournament", 190), ColumnSpec("team_name", "Team", 180), ColumnSpec("matches_played", "Played", 72, "e"), ColumnSpec("wins", "Wins", 72, "e"), ColumnSpec("draws", "Draws", 72, "e"), ColumnSpec("losses", "Losses", 72, "e"), ColumnSpec("points", "Points", 84, "e")),
    "Team Matches": (ColumnSpec("match_date", "Date and time", 190), ColumnSpec("tournament_name", "Tournament", 180), ColumnSpec("opponent", "Opponent", 180), ColumnSpec("venue_name", "Venue", 150), ColumnSpec("team1_score", "Score 1", 75, "e"), ColumnSpec("team2_score", "Score 2", 75, "e"), ColumnSpec("status", "Status", 110)),
    "Wins per team": (ColumnSpec("team_name", "Team", 220), ColumnSpec("wins", "Wins", 100, "e")),
    "Matches played": (ColumnSpec("team_name", "Team", 220), ColumnSpec("matches_played", "Matches played", 130, "e")),
    "Total score per team": (ColumnSpec("team_name", "Team", 220), ColumnSpec("total_score", "Total score", 130, "e")),
    "Upcoming matches": (ColumnSpec("match_date", "Date and time", 190), ColumnSpec("tournament_name", "Tournament", 170), ColumnSpec("team1_name", "Team 1", 150), ColumnSpec("team2_name", "Team 2", 150), ColumnSpec("venue_name", "Venue", 150), ColumnSpec("status", "Status", 110)),
}
REPORT_ICONS = ("trophy-fill", "calendar2-week", "award-fill", "play-circle-fill", "bullseye", "calendar-event-fill")


class ReportsPage(ttk.Frame):
    def __init__(self, master, shell):
        super().__init__(master, padding=24)
        self.shell = shell
        self.service = ReportService()
        self._filters = {"tournaments": [], "teams": []}
        self.report_var = ttk.StringVar(value="Standings")
        self.filter_var = ttk.StringVar(value="All tournaments")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        PageHeader(self, "Reports", "Explore standings, results and tournament activity. Standings come directly from TournamentStandings.").grid(row=0, column=0, sticky="ew")

        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.nav_panel = card(body, padding=(10, 12))
        self.nav_panel.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        ttk.Label(self.nav_panel, text="REPORT LIBRARY", style="SidebarTitle.TLabel").pack(anchor="w", padx=8, pady=(2, 10))
        self.report_buttons = {}
        for (name, _columns), icon in zip(REPORT_COLUMNS.items(), REPORT_ICONS):
            button = ttk.Button(self.nav_panel, text=name, icon=icon, compound="left", bootstyle="primary" if name == "Standings" else self._inactive_bootstyle(), command=lambda n=name: self._select_report(n), width=22, padding=(10, 9))
            button.pack(fill="x", pady=3)
            self.report_buttons[name] = button

        self.results_area = ttk.Frame(body)
        self.results_area.grid(row=0, column=1, sticky="nsew")
        self.results_area.grid_columnconfigure(0, weight=1)
        self.results_area.grid_rowconfigure(1, weight=1)
        toolbar = card(self.results_area, padding=(14, 12))
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(toolbar, text="FILTER", style="FormLabel.TLabel").pack(side="left", padx=(0, 10))
        self.filter_box = ttk.Combobox(toolbar, textvariable=self.filter_var, state="readonly", width=38)
        self.filter_box.pack(side="left")
        self.filter_box.bind("<<ComboboxSelected>>", lambda _event: self._load_report())

        self.results_panel = card(self.results_area, padding=16)
        self.results_panel.grid(row=1, column=0, sticky="nsew")
        self.results_panel.grid_rowconfigure(1, weight=1)
        self.results_panel.grid_columnconfigure(0, weight=1)
        self.summary = ttk.Label(self.results_panel, text="Loading report…", style="SectionTitle.TLabel")
        self.summary.grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.table = None
        self.bind("<<ThemeChanged>>", self._theme_changed, add="+")
        self.shell.run_task(self.service.filters, self._filters_loaded)

    def _inactive_bootstyle(self):
        return "secondary" if self.winfo_toplevel().style.theme_use() == DARK_THEME else "light"

    def _theme_changed(self, _event=None):
        inactive = self._inactive_bootstyle()
        active = self.report_var.get()
        for name, button in self.report_buttons.items():
            button.configure(bootstyle="primary" if name == active else inactive)

    def focus_search(self):
        if self.table:
            self.table.focus_search()

    def _filters_loaded(self, values):
        self._filters = values
        self._report_changed()

    def _select_report(self, report):
        self.report_var.set(report)
        for name, button in self.report_buttons.items():
            button.configure(bootstyle="primary" if name == report else self._inactive_bootstyle())
        self._report_changed()

    def _report_changed(self):
        report = self.report_var.get()
        if report == "Standings":
            choices = (("All tournaments", None),) + tuple((item["tournament_name"], item["tournament_id"]) for item in self._filters["tournaments"])
        elif report == "Team Matches":
            choices = (("Choose a team", None),) + tuple((item["team_name"], item["team_id"]) for item in self._filters["teams"])
        else:
            choices = (("All records", None),)
        self.filter_map = {label: value for label, value in choices}
        self.filter_box.configure(values=tuple(self.filter_map))
        self.filter_var.set(choices[0][0])
        if self.table:
            self.table.destroy()
        self.table = DataTable(self.results_panel, REPORT_COLUMNS[report], singular="row", empty_message="No rows returned for this report.")
        self.table.grid(row=1, column=0, sticky="nsew")
        self._load_report()

    def _load_report(self):
        if self.table is None:
            return
        report = self.report_var.get()
        filter_id = self.filter_map.get(self.filter_var.get())
        if report == "Team Matches" and filter_id is None:
            self.table.set_rows([])
            self.summary.configure(text="Choose a team to view its match history")
            return
        if report == "Standings":
            qualifier = self.filter_var.get() if filter_id is not None else "all tournaments"
            self.summary.configure(text=f"Showing standings for {qualifier} · draws included")
        elif report == "Team Matches":
            self.summary.configure(text=f"Showing matches for {self.filter_var.get()}")
        else:
            self.summary.configure(text=f"{report} · all records")
        self.shell.run_task(lambda: self.service.run(report, filter_id), self.table.set_rows)
