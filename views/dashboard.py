"""Dashboard cards, fixture lists, leaders and a status summary chart."""
from __future__ import annotations
import tkinter as tk
import ttkbootstrap as ttk
from services.matches import MatchService
from services.reports import ReportService
from views.widgets.page_header import PageHeader
from views.widgets.stat_card import StatCard
from views.widgets.styles import card


METRICS = (
    ("players", "Players", "people-fill", "primary"),
    ("teams", "Teams", "shield-fill", "info"),
    ("sports", "Sports", "trophy-fill", "success"),
    ("tournaments", "Tournaments", "calendar3", "warning"),
    ("venues", "Venues", "geo-alt-fill", "danger"),
    ("matches", "Matches", "calendar-event-fill", "secondary"),
)


class DashboardPage(ttk.Frame):
    def __init__(self, master, shell):
        super().__init__(master, padding=24)
        self.shell = shell
        self.service = ReportService()
        self.match_service = MatchService()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        header = PageHeader(self, "Dashboard", "A clear view of tournament activity, upcoming fixtures and team standings.")
        header.configure(padding=(0, 0, 0, 8))
        header.grid(row=0, column=0, sticky="ew")
        self.cards_frame = ttk.Frame(self)
        self.cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.stat_cards = {}
        for index, (key, label, icon, accent) in enumerate(METRICS):
            self.cards_frame.grid_columnconfigure(index, weight=1, uniform="metrics")
            metric = StatCard(self.cards_frame, label=label, value="—", icon=icon, bootstyle=accent)
            metric.grid(row=0, column=index, sticky="ew", padx=4)
            self.stat_cards[key] = metric
        self.content = ttk.Frame(self)
        self.content.grid(row=2, column=0, sticky="nsew")
        for column in range(2):
            self.content.grid_columnconfigure(column, weight=1, uniform="feature")
        self.content.grid_rowconfigure(0, weight=1)
        self.fixture_card = card(self.content, padding=16)
        self.fixture_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.fixture_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.fixture_card, text="Upcoming Matches", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self.fixture_card, text="Scheduled fixtures", style="Caption.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 12))
        self.fixture_list = ttk.Frame(self.fixture_card)
        self.fixture_list.grid(row=2, column=0, sticky="nsew")
        self.leaders_card = card(self.content, padding=16)
        self.leaders_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.leaders_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.leaders_card, text="Top Teams", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self.leaders_card, text="Ranked by tournament points", style="Caption.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 12))
        self.leaders_list = ttk.Frame(self.leaders_card)
        self.leaders_list.grid(row=2, column=0, sticky="nsew")
        self.chart_card = card(self, padding=(16, 12))
        self.chart_card.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.chart_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.chart_card, text="Matches by status", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.chart = tk.Canvas(self.chart_card, height=68, highlightthickness=0, borderwidth=0)
        self.chart.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.chart.bind("<Configure>", lambda _event: self._draw_status_chart())
        self._status_counts = {name: 0 for name in ("Scheduled", "Ongoing", "Completed", "Cancelled")}
        self._render_empty(self.fixture_list, "No scheduled matches.", "calendar-x")
        self._render_empty(self.leaders_list, "No standings available yet.", "trophy")
        self.load()

    def load(self):
        self.shell.run_task(self.service.dashboard, self._render)
        self.shell.run_task(self.match_service.list_all, self._status_rows)

    def _render(self, data):
        for key, metric in self.stat_cards.items():
            metric.set_value(data["counts"].get(key, 0))
        self._replace_rows(self.fixture_list, self._fixtures(data.get("upcoming", [])))
        leaders = sorted(data.get("top", []), key=lambda row: (row.get("points", 0), row.get("wins", 0)), reverse=True)[:5]
        self._replace_rows(self.leaders_list, self._leaders(leaders))

    def _status_rows(self, matches):
        self._status_counts = {name: 0 for name in self._status_counts}
        for row in matches:
            status = row.get("status")
            if status in self._status_counts:
                self._status_counts[status] += 1
        self._draw_status_chart()

    @staticmethod
    def _replace_rows(parent, widgets):
        keep = set(widgets)
        for child in parent.winfo_children():
            if child not in keep:
                child.destroy()
        for widget in widgets:
            widget.pack(fill="x", pady=3)

    def _render_empty(self, parent, message, icon):
        ttk.Label(parent, text="", icon=icon, icon_size=23, bootstyle="secondary").pack(pady=(14, 6))
        ttk.Label(parent, text=message, style="Caption.TLabel").pack(pady=(0, 12))

    def _fixtures(self, rows):
        if not rows:
            return self._empty_widgets(self.fixture_list, "No scheduled matches.", "calendar-x")
        items = []
        for row in rows[:3]:
            line = card(self.fixture_list, padding=(8, 6))
            line.grid_columnconfigure(1, weight=1)
            date_text = row["match_date"].strftime("%d %b") if hasattr(row["match_date"], "strftime") else str(row["match_date"])
            ttk.Label(line, text=date_text, bootstyle="primary", padding=(7, 4)).grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="ns")
            ttk.Label(line, text=f"{row['team1_name']}  vs  {row['team2_name']}", style="Body.TLabel", wraplength=280).grid(row=0, column=1, sticky="w")
            ttk.Label(line, text=f"{row['tournament_name']}  ·  {row['venue_name']}", style="Caption.TLabel").grid(row=1, column=1, sticky="w", pady=(3, 0))
            items.append(line)
        return items

    def _leaders(self, rows):
        if not rows:
            return self._empty_widgets(self.leaders_list, "No standings available yet.", "trophy")
        rows = rows[:3]
        maximum = max((int(row.get("points") or 0) for row in rows), default=1) or 1
        items = []
        for index, row in enumerate(rows, start=1):
            line = ttk.Frame(self.leaders_list, padding=(4, 5))
            line.grid_columnconfigure(1, weight=1)
            ttk.Label(line, text=f"{index:02d}", bootstyle="primary", width=4, anchor="center").grid(row=0, column=0, rowspan=2, padx=(0, 10))
            ttk.Label(line, text=row["team_name"], style="Body.TLabel").grid(row=0, column=1, sticky="w")
            ttk.Label(line, text=f"{row.get('points', 0)} pts  ·  {row.get('wins', 0)} W  ·  {row.get('draws', 0)} D", style="Caption.TLabel").grid(row=0, column=2, sticky="e", padx=(8, 0))
            bar = ttk.Progressbar(line, maximum=maximum, value=int(row.get("points") or 0), bootstyle="primary")
            bar.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(6, 0))
            items.append(line)
        return items

    @staticmethod
    def _empty_widgets(parent, message, icon):
        box = ttk.Frame(parent)
        ttk.Label(box, text="", icon=icon, icon_size=23, bootstyle="secondary").pack(pady=(14, 6))
        ttk.Label(box, text=message, style="Caption.TLabel").pack(pady=(0, 12))
        return [box]

    def _draw_status_chart(self):
        if not self.chart.winfo_exists():
            return
        colors = self.winfo_toplevel().style.colors
        width = max(300, self.chart.winfo_width())
        self.chart.configure(background=colors.inputbg)
        self.chart.delete("all")
        values = [("Scheduled", self._status_counts["Scheduled"], colors.info),
                  ("Ongoing", self._status_counts["Ongoing"], colors.warning),
                  ("Completed", self._status_counts["Completed"], colors.success),
                  ("Cancelled", self._status_counts["Cancelled"], colors.danger)]
        highest = max((value for _label, value, _color in values), default=1) or 1
        col_width = width / len(values)
        for index, (label, value, color) in enumerate(values):
            x = col_width * index + 10
            max_bar = col_width - 38
            bar_width = max(4, max_bar * value / highest) if value else 4
            self.chart.create_text(x, 14, text=label, anchor="w", fill=colors.fg, font=self.winfo_toplevel().style.lookup("Caption.TLabel", "font"))
            self.chart.create_rectangle(x, 30, x + max_bar, 42, fill=colors.active, outline="")
            self.chart.create_rectangle(x, 30, x + bar_width, 42, fill=color, outline="")
            self.chart.create_text(x, 56, text=str(value), anchor="w", fill=colors.secondary, font=self.winfo_toplevel().style.lookup("Caption.TLabel", "font"))








