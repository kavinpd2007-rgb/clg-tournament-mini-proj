"""Tournament management screen."""
from __future__ import annotations
from dataclasses import replace
from typing import Any, Mapping
from db.repositories.tournaments import TournamentRepository
from services.crud import TournamentCrudService
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec
from views.widgets.form_dialog import FieldSpec

class TournamentsPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Tournaments", singular="Tournament",
            description="Plan college competitions by sport and tournament date range.",
            columns=(
                ColumnSpec("tournament_id", "ID", 72, "center"),
                ColumnSpec("tournament_name", "Tournament", 300),
                ColumnSpec("sport_name", "Sport", 180),
                ColumnSpec("start_date", "Starts", 160),
                ColumnSpec("end_date", "Ends", 160),
            ),
            fields=(
                FieldSpec("tournament_name", "Tournament name"),
                FieldSpec("sport_id", "Sport", kind="choice"),
                FieldSpec("start_date", "Start date", kind="date"),
                FieldSpec("end_date", "End date", kind="date"),
            ),
            service=TournamentCrudService(TournamentRepository()),
            empty_message="No tournaments yet. Click Add Tournament to plan the first one.",
        )

    def _open_form(self, title: str, row: Mapping[str, Any] | None, field_overrides=None) -> None:
        self.shell.run_task(
            self.service.available_sports,
            lambda sports: self._open_tournament_form(title, row, sports),
        )

    def _open_tournament_form(self, title: str, row: Mapping[str, Any] | None, sports: list[dict[str, Any]]) -> None:
        if not sports:
            self.shell.set_status("Add a sport before creating a tournament.")
            return
        choices = tuple((sport["sport_name"], sport["sport_id"]) for sport in sports)
        sport_field = replace(self.fields[1], choices=choices)
        super()._open_form(title, row, {"sport_id": sport_field})
