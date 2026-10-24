"""Team management and member assignment screens."""
from __future__ import annotations
from dataclasses import replace
from datetime import date
from typing import Any, Mapping
import ttkbootstrap as ttk
from db.repositories.teams import TeamRepository
from services.crud import TeamCrudService, validate_team
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec, DataTable
from views.widgets.feedback import ConfirmDialog, Toast
from views.widgets.form_dialog import FieldSpec

class TeamsPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Teams", singular="Team",
            description="Create sport-specific teams and manage their player rosters.",
            columns=(ColumnSpec("team_id", "ID", 72, "center"), ColumnSpec("team_name", "Team name", 250), ColumnSpec("department", "Department", 180), ColumnSpec("sport_name", "Sport", 180)),
            fields=(FieldSpec("team_name", "Team name"), FieldSpec("department", "Department"), FieldSpec("sport_id", "Sport", kind="choice")),
            service=TeamCrudService(TeamRepository()),
            empty_message="No teams yet. Click Add Team to create the first one.",
        )

    def _open_form(self, title: str, row: Mapping[str, Any] | None, field_overrides=None) -> None:
        self.shell.run_task(self.service.available_sports, lambda sports: self._open_team_form(title, row, sports))

    def _open_team_form(self, title: str, row: Mapping[str, Any] | None, sports: list[dict[str, Any]]) -> None:
        if not sports:
            self.shell.set_status("Add a sport before creating a team.")
            return
        choices = tuple((sport["sport_name"], sport["sport_id"]) for sport in sports)
        sport_field = replace(self.fields[2], choices=choices)
        super()._open_form(title, row, {"sport_id": sport_field})

    def view_row(self, row: Mapping[str, Any]) -> None:
        TeamRosterDialog(self, self.shell, row)

class TeamRosterDialog(ttk.Toplevel):
    def __init__(self, parent, shell, team: Mapping[str, Any]):
        super().__init__(title=f"{team['team_name']} · Players", transient=parent, minsize=(780, 520), resizable=(True, True))
        self.shell = shell
        self.team = dict(team)
        self.team_service = parent.service
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        header = ttk.Frame(self, padding=(20, 18))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=self.team["team_name"], style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(header, text=f"{self.team['sport_name']} · {self.team['department']}", bootstyle="secondary").pack(anchor="w", pady=(4, 0))
        self.table = DataTable(
            self,
            (ColumnSpec("player_id", "ID", 70, "center"), ColumnSpec("name", "Player", 220), ColumnSpec("register_no", "Register number", 170), ColumnSpec("department", "Department", 160), ColumnSpec("join_date", "Joined", 140)),
            singular="Player", on_add=self._open_assignment, on_delete=self._remove_player,
            read_only=not shell.can_write,
            empty_message="No players assigned. Click Add Player to build this roster.",
        )
        self.table.grid(row=1, column=0, sticky="nsew", padx=20)
        ttk.Button(self, text="Close", bootstyle="secondary outline", command=self.destroy).grid(row=2, column=0, sticky="e", padx=20, pady=16)
        self._load()
        self.grab_set()

    def _load(self) -> None:
        self.shell.run_task(lambda: self.team_service.team_players(int(self.team["team_id"])), self.table.set_rows)

    def _open_assignment(self) -> None:
        if self.shell.can_write:
            self.shell.run_task(self.team_service.available_players, self._show_assignment)

    def _show_assignment(self, players: list[dict[str, Any]]) -> None:
        if not players:
            self.shell.set_status("Add a player before assigning them to a team.")
            return
        dialog = ttk.Toplevel(title="Assign player", transient=self, minsize=(480, 260), resizable=(False, False))
        frame = ttk.Frame(dialog, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Assign a player", style="SectionTitle.TLabel").pack(anchor="w", pady=(0, 16))
        mapping = {f"{player['name']} · {player['register_no']}": player["player_id"] for player in players}
        selected = ttk.StringVar()
        ttk.Label(frame, text="Player *").pack(anchor="w")
        player_box = ttk.Combobox(frame, textvariable=selected, values=tuple(mapping), state="readonly")
        player_box.pack(fill="x", pady=(5, 12))
        ttk.Label(frame, text="Join date *").pack(anchor="w")
        join_date = ttk.DateEntry(frame, date_format="%Y-%m-%d", value=date.today())
        join_date.pack(anchor="w", pady=(5, 16))
        error = ttk.Label(frame, text="", bootstyle="danger")
        error.pack(anchor="w")
        save = ttk.Button(frame, text="Assign player", icon="person-plus-fill", bootstyle="primary")
        save.pack(anchor="e", pady=(12, 0))

        def assign() -> None:
            player_id = mapping.get(selected.get())
            joined = join_date.get_date()
            if player_id is None or joined is None:
                error.configure(text="Choose a player and join date.")
                return
            save.configure(state="disabled", text="Assigning…")
            join_day = joined.date() if hasattr(joined, "date") else joined
            self.shell.run_task(
                lambda: self.team_service.assign_player(int(self.team["team_id"]), int(player_id), join_day),
                lambda _result: self._assigned(dialog),
                lambda exc: self._assign_failed(error, save, exc),
            )

        save.configure(command=assign)
        player_box.focus_set()
        dialog.bind("<Return>", lambda _event: assign())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()

    @staticmethod
    def _assign_failed(error_label, save_button, exc: BaseException) -> None:
        error_label.configure(text=str(exc))
        save_button.configure(state="normal", text="Assign player")

    def _assigned(self, dialog) -> None:
        dialog.destroy()
        self.shell.set_status("Player assigned to the team.", success=True)
        Toast.show(self, "Player assigned to the team.")
        self._load()

    def _remove_player(self, row: Mapping[str, Any]) -> None:
        if not self.shell.can_write:
            return
        if not ConfirmDialog.ask(self, title="Remove player?", message=f"Remove {row['name']} from {self.team['team_name']}?"):
            return
        self.shell.run_task(
            lambda: self.team_service.remove_player(int(self.team["team_id"]), int(row["player_id"])),
            lambda _result: self._removed(row["name"]),
        )

    def _removed(self, player_name: str) -> None:
        self.shell.set_status(f"Removed {player_name} from the team.", success=True)
        Toast.show(self, "Player removed from the team.")
        self._load()




