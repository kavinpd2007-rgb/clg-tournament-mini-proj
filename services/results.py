"""Result validation and match eligibility rules."""
from __future__ import annotations

from typing import Any, Mapping

from db.repositories.matches import MatchRepository
from db.repositories.results import MatchResultRepository


class ResultService:
    def __init__(self, results: MatchResultRepository | None = None, matches: MatchRepository | None = None):
        self.results = results or MatchResultRepository()
        self.matches = matches or MatchRepository()

    def list_all(self):
        return self.results.list_with_details()

    def entry_matches(self):
        return self.results.entry_matches()

    def create(self, data: Mapping[str, Any]) -> int:
        match_id = self._id(data.get("match_id"), "match")
        match = self.matches.get(match_id)
        if not match:
            raise ValueError("This match no longer exists.")
        if match["status"] not in ("Scheduled", "Ongoing"):
            raise ValueError("Results can only be entered for Scheduled or Ongoing matches.")
        if self.results.for_match(match_id):
            raise ValueError("This match already has a result. Use Edit on its result.")
        winner, first, second = self._scores(data, match)
        return self.results.add(match_id, winner, first, second)

    def update(self, result_id: int, data: Mapping[str, Any]) -> bool:
        result = self.results.get(result_id)
        if not result:
            raise ValueError("This result no longer exists.")
        match = self.matches.get(int(result["match_id"]))
        if not match:
            raise ValueError("The match for this result no longer exists.")
        winner, first, second = self._scores(data, match)
        return self.results.update(result_id, int(result["match_id"]), winner, first, second)

    def delete(self, result_id: int, *, confirmed: bool = False) -> bool:
        result = self.results.get(result_id)
        if not result:
            return False
        if not confirmed:
            raise ValueError("Deleting a result changes its match back to Scheduled. Confirm first.")
        return self.results.delete(result_id, int(result["match_id"]))

    @staticmethod
    def _id(value: Any, label: str) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Select a valid {label}.") from None
        if number <= 0:
            raise ValueError(f"Select a valid {label}.")
        return number

    @classmethod
    def _scores(cls, data: Mapping[str, Any], match: Mapping[str, Any]) -> tuple[int | None, int, int]:
        first = cls._score(data.get("team1_score"), "Team 1 score")
        second = cls._score(data.get("team2_score"), "Team 2 score")
        raw_winner = data.get("winner_id")
        if raw_winner == "":
            raise ValueError("Select Team 1, Team 2, or Draw.")
        winner = None if raw_winner is None else cls._id(raw_winner, "winner")
        team1, team2 = int(match["team1_id"]), int(match["team2_id"])
        expected = team1 if first > second else team2 if second > first else None
        if winner not in (team1, team2, None):
            raise ValueError("Winner must be Team 1, Team 2, or Draw.")
        if winner != expected:
            raise ValueError("Winner must match the scores; equal scores must be recorded as a draw.")
        return winner, first, second

    @staticmethod
    def _score(value: Any, label: str) -> int:
        try:
            score = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be a non-negative whole number.") from None
        if score < 0:
            raise ValueError(f"{label} must be non-negative.")
        return score


