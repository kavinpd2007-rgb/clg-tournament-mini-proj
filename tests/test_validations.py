from datetime import date

import pytest

from services.crud import validate_player, validate_sport, validate_team, validate_tournament, validate_venue


def test_player_validation_strips_required_values_and_checks_year() -> None:
    record = validate_player({"name": "  Ada Student ", "register_no": " CS900 ", "department": " CSE ", "year": "3"})
    assert record == {"name": "Ada Student", "register_no": "CS900", "department": "CSE", "year": 3}
    for year in (0, 6, "not a year"):
        with pytest.raises(ValueError):
            validate_player({"name": "A", "register_no": "A1", "department": "CSE", "year": year})


def test_required_fields_and_venue_capacity_are_validated() -> None:
    with pytest.raises(ValueError, match="Required"):
        validate_player({"name": "", "register_no": "R1", "department": "CSE", "year": 1})
    with pytest.raises(ValueError, match="greater than zero"):
        validate_venue({"venue_name": "Field", "location": "Campus", "capacity": 0})
    assert validate_venue({"venue_name": "Field", "location": "Campus", "capacity": "30"})["capacity"] == 30


def test_sport_requires_both_fields() -> None:
    assert validate_sport({"sport_name": "Cricket", "type": "Outdoor"})["sport_name"] == "Cricket"
    with pytest.raises(ValueError, match="Required"):
        validate_sport({"sport_name": "Cricket", "type": " "})

def test_team_requires_name_department_and_a_selected_sport() -> None:
    valid = validate_team({"team_name": "CSE Cricket", "department": "CSE", "sport_id": "1"})
    assert valid["sport_id"] == 1
    for invalid in (
        {"team_name": "", "department": "CSE", "sport_id": 1},
        {"team_name": "Team", "department": "CSE", "sport_id": ""},
    ):
        with pytest.raises(ValueError):
            validate_team(invalid)

def test_tournament_requires_ordered_dates() -> None:
    valid = validate_tournament({"tournament_name": "Cup", "sport_id": "1", "start_date": date(2026, 11, 1), "end_date": date(2026, 11, 7)})
    assert valid["sport_id"] == 1
    with pytest.raises(ValueError, match="on or after"):
        validate_tournament({"tournament_name": "Cup", "sport_id": 1, "start_date": date(2026, 11, 8), "end_date": date(2026, 11, 7)})
