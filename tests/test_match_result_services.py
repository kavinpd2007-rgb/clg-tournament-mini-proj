from datetime import date, datetime

import pytest

from services.matches import MatchService
from services.results import ResultService


class MatchRepo:
    def __init__(self):
        self.created = []
        self.updated = []
    def add(self, values):
        self.created.append(dict(values)); return 55
    def update(self, match_id, values):
        self.updated.append((match_id, dict(values))); return True
    def delete(self, match_id, **kwargs):
        return True
    def get(self, match_id):
        return {"match_id": match_id, "tournament_id": 3, "team1_id": 10, "team2_id": 11, "venue_id": 8, "match_date": datetime(2030, 5, 2), "status": "Scheduled"}


class TournamentRepo:
    def get(self, _id):
        return {"sport_id": 7, "start_date": date(2030, 5, 1), "end_date": date(2030, 5, 9)}


class TeamRepo:
    def get(self, team_id):
        return {"sport_id": 7 if team_id in (10, 11) else 8}


class VenueRepo:
    def get(self, _id): return {"venue_id": 8}


class ResultsRepo:
    def __init__(self): self.rows = {}; self.calls = []
    def get(self, result_id): return self.rows.get(result_id)
    def for_match(self, match_id): return next((row for row in self.rows.values() if row["match_id"] == match_id), None)
    def add(self, match_id, winner_id, first, second):
        self.calls.append(("add", match_id, winner_id, first, second)); return 77
    def update(self, result_id, match_id, winner_id, first, second):
        self.calls.append(("update", result_id, match_id, winner_id, first, second)); return True
    def delete(self, result_id, match_id):
        self.calls.append(("delete", result_id, match_id)); return True


def match_payload(**updates):
    data = {"tournament_id": 3, "team1_id": 10, "team2_id": 11, "venue_id": 8, "match_date": datetime(2030, 5, 2), "status": "Scheduled"}
    data.update(updates)
    return data


def test_match_rules_validate_self_sport_and_tournament_dates():
    repo = MatchRepo()
    service = MatchService(repo, TournamentRepo(), TeamRepo(), VenueRepo())
    assert service.create(match_payload()) == 55  # Future date is allowed.
    for payload, message in (
        (match_payload(team2_id=10), "cannot play itself"),
        (match_payload(team2_id=12), "tournament's sport"),
        (match_payload(match_date=datetime(2030, 5, 10)), "within the tournament"),
        (match_payload(status="Completed"), "result sets Completed"),
    ):
        with pytest.raises(ValueError, match=message): service.create(payload)


def test_match_status_only_direct_statuses_and_completed_is_result_only():
    service = MatchService(MatchRepo(), TournamentRepo(), TeamRepo(), VenueRepo())
    assert service._validate(match_payload(status="Ongoing"), allow_missing_status=True)["status"] == "Ongoing"
    with pytest.raises(ValueError, match="result sets Completed"):
        service.update(1, match_payload(status="Completed"))
    with pytest.raises(ValueError, match="result sets Completed"):
        service.update(1, match_payload(status="Unknown"))


def test_result_score_winner_consistency_and_draws():
    match = {"team1_id": 10, "team2_id": 11}
    assert ResultService._scores({"team1_score": 2, "team2_score": 1, "winner_id": 10}, match) == (10, 2, 1)
    assert ResultService._scores({"team1_score": 1, "team2_score": 1, "winner_id": None}, match) == (None, 1, 1)
    for data in (
        {"team1_score": -1, "team2_score": 0, "winner_id": 11},
        {"team1_score": 3, "team2_score": 1, "winner_id": 11},
        {"team1_score": 2, "team2_score": 2, "winner_id": 10},
        {"team1_score": 0, "team2_score": 1, "winner_id": 99},
    ):
        with pytest.raises(ValueError): ResultService._scores(data, match)


def test_result_entry_requires_eligible_match_and_delete_confirmation():
    matches = MatchRepo()
    results = ResultsRepo()
    service = ResultService(results, matches)
    assert service.create({"match_id": 4, "team1_score": 3, "team2_score": 1, "winner_id": 10}) == 77
    assert results.calls[-1] == ("add", 4, 10, 3, 1)
    results.rows[77] = {"result_id": 77, "match_id": 4, "winner_id": 10, "team1_score": 3, "team2_score": 1}
    with pytest.raises(ValueError, match="Confirm first"):
        service.delete(77)
    assert service.delete(77, confirmed=True)


def test_result_edit_uses_existing_result_and_accepts_future_match():
    matches = MatchRepo()
    results = ResultsRepo()
    results.rows[77] = {"result_id": 77, "match_id": 4}
    service = ResultService(results, matches)
    assert service.update(77, {"team1_score": 0, "team2_score": 0, "winner_id": None})
    assert results.calls[-1] == ("update", 77, 4, None, 0, 0)
