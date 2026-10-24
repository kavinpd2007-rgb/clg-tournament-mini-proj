"""Match scheduling, status management and sport-aware team selection."""
from __future__ import annotations
from dataclasses import replace
from typing import Any, Mapping
import ttkbootstrap as ttk
from services.matches import MatchService
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec
from views.widgets.feedback import ConfirmDialog, Toast
from views.widgets.form_dialog import FieldSpec, FormDialog

class MatchesPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Matches", singular="Match",
            description="Schedule teams at venues inside their tournament dates. Team choices follow the tournament sport.",
            columns=(
                ColumnSpec("match_id", "ID", 64, "center"),
                ColumnSpec("tournament_name", "Tournament", 210),
                ColumnSpec("team1_name", "Team 1", 170),
                ColumnSpec("team2_name", "Team 2", 170),
                ColumnSpec("venue_name", "Venue", 170),
                ColumnSpec("match_date", "Date and time", 190),
                ColumnSpec("status", "Status", 120),
            ),
            fields=(
                FieldSpec("tournament_id", "Tournament", kind="choice"),
                FieldSpec("team1_id", "Team 1", kind="choice"),
                FieldSpec("team2_id", "Team 2", kind="choice"),
                FieldSpec("venue_id", "Venue", kind="choice"),
                FieldSpec("match_date", "Match date and time", kind="datetime"),
                FieldSpec("status", "Status", kind="choice", initial="Scheduled"),
            ),
            service=MatchService(),
            empty_message="No matches scheduled. Click Add Match to create the first one.",
        )

    def _open_form(self, title: str, row: Mapping[str, Any] | None, field_overrides=None) -> None:
        self.shell.run_task(self.service.form_options, lambda options: self._prepare_form(title, row, options, read_only=False))

    def view_row(self, row: Mapping[str, Any]) -> None:
        self.shell.run_task(self.service.form_options, lambda options: self._prepare_form("Match details", row, options, read_only=True))

    def _prepare_form(self, title: str, row: Mapping[str, Any] | None, options: dict[str, list[dict[str, Any]]], *, read_only: bool) -> None:
        tournaments = options["tournaments"]
        teams = options["teams"]
        venues = options["venues"]
        tournament_choices = tuple((item["tournament_name"], item["tournament_id"]) for item in tournaments)
        venue_choices = tuple((item["venue_name"], item["venue_id"]) for item in venues)
        selected_tournament = row.get("tournament_id") if row else None
        sport_id = next((item["sport_id"] for item in tournaments if item["tournament_id"] == selected_tournament), None)
        eligible = [team for team in teams if team["sport_id"] == sport_id]
        team1_choices = tuple((team["team_name"], team["team_id"]) for team in eligible)
        selected_team1 = row.get("team1_id") if row else None
        team2_choices = tuple((team["team_name"], team["team_id"]) for team in eligible if team["team_id"] != selected_team1)
        if row and row.get("status") == "Completed":
            status_choices = (("Completed", "Completed"),)
            status_disabled = True
        else:
            status_choices = tuple((status, status) for status in ("Scheduled", "Ongoing", "Cancelled") if not (row and row.get("result_id") and status == "Cancelled"))
            status_disabled = False
        choice_data = {
            "tournament_id": tournament_choices,
            "team1_id": team1_choices,
            "team2_id": team2_choices,
            "venue_id": venue_choices,
            "status": status_choices,
        }
        overrides: dict[str, FieldSpec] = {}
        for field in self.fields:
            initial = row.get(field.key) if row else field.initial
            if field.key == "match_date" and initial is None:
                initial = None
            overrides[field.key] = replace(field, initial=initial, choices=choice_data.get(field.key, field.choices), disabled=status_disabled if field.key == "status" else False)
        dialog_ref: dict[str, FormDialog] = {}
        match_id = int(row["match_id"]) if row else None

        def submit(values: dict[str, Any]) -> None:
            dialog = dialog_ref["dialog"]
            operation = (lambda: self.service.create(values)) if match_id is None else (lambda: self.service.update(match_id, values))
            dialog.set_busy(True)
            self.shell.run_task(
                operation,
                lambda _result: self._saved_match(dialog, "scheduled" if match_id is None else "updated"),
                lambda error: dialog.set_error(str(error)),
            )

        dialog = FormDialog(
            self, title=title, fields=tuple(overrides[field.key] for field in self.fields),
            on_submit=None if read_only else submit, read_only=read_only,
        )
        dialog_ref["dialog"] = dialog
        if not read_only:
            tournament_by_id = {item["tournament_id"]: item for item in tournaments}

            def refresh_teams(tournament_id: Any) -> None:
                tournament = tournament_by_id.get(tournament_id)
                selected_sport = tournament["sport_id"] if tournament else None
                choices = tuple((team["team_name"], team["team_id"]) for team in teams if team["sport_id"] == selected_sport)
                dialog.set_choices("team1_id", choices)
                self._refresh_team2(dialog, teams, selected_sport)

            def team1_changed(_team_id: Any) -> None:
                selected = dialog.choice_value("tournament_id")
                tournament = tournament_by_id.get(selected)
                self._refresh_team2(dialog, teams, tournament["sport_id"] if tournament else None)

            dialog.bind_choice_change("tournament_id", refresh_teams)
            dialog.bind_choice_change("team1_id", team1_changed)

    @staticmethod
    def _refresh_team2(dialog: FormDialog, teams: list[dict[str, Any]], sport_id: Any) -> None:
        team1_id = dialog.choice_value("team1_id")
        choices = tuple(
            (team["team_name"], team["team_id"])
            for team in teams
            if sport_id is not None and team["sport_id"] == sport_id and team["team_id"] != team1_id
        )
        dialog.set_choices("team2_id", choices)

    def delete_row(self, row: Mapping[str, Any]) -> None:
        if not self.shell.can_write:
            return
        has_result = bool(row.get("result_id"))
        label = f"Match #{row['match_id']}"
        message = (
            f"{label} has a result. Deleting it will also delete that result. Continue?"
            if has_result else f"Delete {label}? This action cannot be undone."
        )
        if not ConfirmDialog.ask(self, title="Delete match?", message=message):
            return
        self.shell.run_task(
            lambda: self.service.delete(int(row["match_id"]), confirm_result_cascade=has_result),
            lambda _result: self._match_deleted(label),
        )

    def _saved_match(self, dialog: FormDialog, action: str) -> None:
        dialog.close()
        self.shell.set_status(f"Match {action} successfully.", success=True)
        Toast.show(self, f"Match {action} successfully.")
        self.load()

    def _match_deleted(self, label: str) -> None:
        self.shell.set_status(f"Deleted {label}; any result was removed with it.", success=True)
        Toast.show(self, f"Deleted {label}.")
        self.load()
