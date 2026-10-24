"""Validated CRUD services for the foundational entities."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Mapping


def _required_text(data: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    cleaned = dict(data)
    missing = [field.replace("_", " ").title() for field in fields if cleaned.get(field) is None or not str(cleaned[field]).strip()]
    if missing:
        raise ValueError("Required: " + ", ".join(missing))
    for field in fields:
        cleaned[field] = str(cleaned[field]).strip()
    return cleaned


def validate_player(data: Mapping[str, Any]) -> dict[str, Any]:
    values = _required_text(data, ("name", "register_no", "department"))
    try:
        values["year"] = int(values["year"])
    except (TypeError, ValueError):
        raise ValueError("Year must be a whole number from 1 to 5.") from None
    if not 1 <= values["year"] <= 5:
        raise ValueError("Year must be between 1 and 5.")
    return values


def validate_sport(data: Mapping[str, Any]) -> dict[str, Any]:
    return _required_text(data, ("sport_name", "type"))


def validate_venue(data: Mapping[str, Any]) -> dict[str, Any]:
    values = _required_text(data, ("venue_name", "location"))
    try:
        values["capacity"] = int(values["capacity"])
    except (TypeError, ValueError):
        raise ValueError("Capacity must be a positive whole number.") from None
    if values["capacity"] <= 0:
        raise ValueError("Capacity must be greater than zero.")
    return values


def validate_tournament(data: Mapping[str, Any]) -> dict[str, Any]:
    values = _required_text(data, ("tournament_name",))
    try:
        values["sport_id"] = int(values["sport_id"])
    except (TypeError, ValueError):
        raise ValueError("Select a sport.") from None
    start = values.get("start_date")
    end = values.get("end_date")
    if not isinstance(start, date) or not isinstance(end, date):
        raise ValueError("Choose both tournament dates.")
    if end < start:
        raise ValueError("End date must be on or after the start date.")
    return values


class ValidatedCrudService:
    """Keep validation in services and storage operations in repositories."""
    def __init__(self, repository, validator: Callable[[Mapping[str, Any]], dict[str, Any]]):
        self.repository = repository
        self.validator = validator

    def list_all(self):
        return self.repository.list_all()

    def create(self, values: Mapping[str, Any]) -> int:
        return self.repository.add(self.validator(values))

    def update(self, record_id: int, values: Mapping[str, Any]) -> bool:
        return self.repository.update(record_id, self.validator(values))

    def delete(self, record_id: int) -> bool:
        return self.repository.delete(record_id)

def validate_team(data: Mapping[str, Any]) -> dict[str, Any]:
    values = _required_text(data, ("team_name", "department"))
    try:
        values["sport_id"] = int(values["sport_id"])
    except (TypeError, ValueError):
        raise ValueError("Select a sport.") from None
    if values["sport_id"] <= 0:
        raise ValueError("Select a valid sport.")
    return values


class TeamCrudService(ValidatedCrudService):
    """Team CRUD and membership operations with no database logic in views."""
    def __init__(self, repository):
        from db.repositories.players import PlayerRepository
        from db.repositories.sports import SportRepository
        from db.repositories.team_players import TeamPlayerRepository
        super().__init__(repository, validate_team)
        self._players = PlayerRepository()
        self._sports = SportRepository()
        self._members = TeamPlayerRepository()

    def list_all(self):
        return self.repository.list_with_sport()

    def available_sports(self):
        return self._sports.list_all()

    def available_players(self):
        return self._players.list_all()

    def team_players(self, team_id: int):
        return self._members.list_for_team(team_id)

    def assign_player(self, team_id: int, player_id: int, join_date: date) -> None:
        if not isinstance(join_date, date):
            raise ValueError("Choose a valid join date.")
        self._members.add(team_id, player_id, join_date)

    def remove_player(self, team_id: int, player_id: int) -> bool:
        return self._members.remove(team_id, player_id)

class TournamentCrudService(ValidatedCrudService):
    def __init__(self, repository):
        from db.repositories.sports import SportRepository
        super().__init__(repository, validate_tournament)
        self._sports = SportRepository()

    def list_all(self):
        return self.repository.list_with_sport()

    def available_sports(self):
        return self._sports.list_all()
