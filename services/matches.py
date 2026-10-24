"""Match scheduling rules and lookups."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping
from db.repositories.matches import MatchRepository
from db.repositories.teams import TeamRepository
from db.repositories.tournaments import TournamentRepository
from db.repositories.venues import VenueRepository

ALLOWED_DIRECT_STATUSES = {"Scheduled", "Ongoing", "Cancelled"}

class MatchService:
    def __init__(self, matches: MatchRepository | None = None, tournaments: TournamentRepository | None = None, teams: TeamRepository | None = None, venues: VenueRepository | None = None):
        self.matches = matches or MatchRepository()
        self.tournaments = tournaments or TournamentRepository()
        self.teams = teams or TeamRepository()
        self.venues = venues or VenueRepository()

    def list_all(self):
        return self.matches.list_with_details()

    def form_options(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "tournaments": self.tournaments.list_with_sport(),
            "teams": self.teams.list_all(),
            "venues": self.venues.list_all(),
        }

    def create(self, data: Mapping[str, Any]) -> int:
        values = self._validate(data, allow_missing_status=True)
        values["status"] = values.get("status") or "Scheduled"
        return self.matches.add(values)

    def update(self, match_id: int, data: Mapping[str, Any]) -> bool:
        values = self._validate(data, allow_missing_status=True)
        if "status" in values and values["status"] not in ALLOWED_DIRECT_STATUSES:
            raise ValueError("Choose Scheduled, Ongoing, or Cancelled. A result sets Completed automatically.")
        return self.matches.update(match_id, values)

    def delete(self, match_id: int, *, confirm_result_cascade: bool = False) -> bool:
        return self.matches.delete(match_id, confirm_result_cascade=confirm_result_cascade)

    def _validate(self, data: Mapping[str, Any], *, allow_missing_status: bool) -> dict[str, Any]:
        required = ("tournament_id", "team1_id", "team2_id", "venue_id", "match_date")
        missing = [field.replace("_", " ").title() for field in required if data.get(field) in (None, "")]
        if missing:
            raise ValueError("Required: " + ", ".join(missing))
        try:
            values: dict[str, Any] = {field: int(data[field]) for field in ("tournament_id", "team1_id", "team2_id", "venue_id")}
        except (TypeError, ValueError, KeyError):
            raise ValueError("Select a valid tournament, both teams, and venue.") from None
        if any(value <= 0 for value in values.values()):
            raise ValueError("Select valid tournament, team, and venue records.")
        match_date = data["match_date"]
        if not isinstance(match_date, datetime):
            raise ValueError("Choose a valid match date and time.")
        if values["team1_id"] == values["team2_id"]:
            raise ValueError("A team cannot play itself.")
        tournament = self.tournaments.get(values["tournament_id"])
        team1 = self.teams.get(values["team1_id"])
        team2 = self.teams.get(values["team2_id"])
        venue = self.venues.get(values["venue_id"])
        if not tournament or not team1 or not team2 or not venue:
            raise ValueError("A selected tournament, team, or venue no longer exists. Refresh the choices.")
        if team1["sport_id"] != tournament["sport_id"] or team2["sport_id"] != tournament["sport_id"]:
            raise ValueError("Both teams must play the tournament's sport.")
        match_day = match_date.date()
        if not (tournament["start_date"] <= match_day <= tournament["end_date"]):
            raise ValueError("Match date must fall within the tournament start and end dates.")
        values["match_date"] = match_date
        if "status" in data and data["status"] not in (None, ""):
            values["status"] = str(data["status"])
            if values["status"] not in ALLOWED_DIRECT_STATUSES:
                raise ValueError("Choose Scheduled, Ongoing, or Cancelled. A result sets Completed automatically.")
        elif not allow_missing_status:
            raise ValueError("Choose a match status.")
        return values


