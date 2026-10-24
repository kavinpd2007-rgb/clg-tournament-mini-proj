from __future__ import annotations

import pytest
from mysql.connector import Error as MySQLError

from db.connection import connection_scope, transaction
from db.errors import DatabaseOperationError
from db.repositories.players import PlayerRepository
from db.repositories.sports import SportRepository
from db.repositories.teams import TeamRepository
from db.repositories.team_players import TeamPlayerRepository
from db.repositories.reports import ReportRepository


def test_player_crud_and_duplicate_register_number(test_database: str) -> None:
    players = PlayerRepository()
    register = "TEST-STAGE-A-001"
    try:
        player_id = players.add({"name": "Stage A Test", "register_no": register, "department": "Test", "year": 1})
        assert players.get(player_id)["register_no"] == register
        assert len(players.search("TEST-STAGE-A")) == 1
        assert players.update(player_id, {"department": "Updated Test"})
        assert players.get(player_id)["department"] == "Updated Test"
        with pytest.raises(DatabaseOperationError) as duplicate:
            players.add({"name": "Duplicate", "register_no": register, "department": "Test", "year": 1})
        assert duplicate.value.errno == 1062
    finally:
        existing = next((row for row in players.search(register) if row["register_no"] == register), None)
        if existing:
            players.delete(existing["player_id"])


def test_constraints_and_restrict_error_translation(test_database: str) -> None:
    with pytest.raises(DatabaseOperationError) as bad_fk:
        TeamRepository().add({"team_name": "Test Bad FK", "department": "Test", "sport_id": 999999})
    assert bad_fk.value.errno == 1452

    with pytest.raises(DatabaseOperationError) as restricted:
        SportRepository().delete(1)
    assert restricted.value.errno == 1451

    with pytest.raises(DatabaseOperationError) as check:
        PlayerRepository().add({"name": "Invalid Year", "register_no": "TEST-STAGE-A-YEAR", "department": "Test", "year": 6})
    assert check.value.errno == 3819

    with pytest.raises(DatabaseOperationError) as score_check:
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO `MatchResult` (`match_id`, `winner_id`, `team1_score`, `team2_score`) "
                "VALUES (%s, %s, %s, %s)", (11, 1, -1, 10)
            )
    assert score_check.value.errno == 3819


def test_existing_view_procedure_and_insert_trigger(test_database: str) -> None:
    reports = ReportRepository()
    standings = reports.standings(1)
    assert standings
    assert any("draws" in row for row in standings)
    assert reports.team_matches(1)

    with transaction() as connection, connection.cursor(dictionary=True) as cursor:
        cursor.execute(
            "INSERT INTO `MatchResult` (`match_id`, `winner_id`, `team1_score`, `team2_score`) "
            "VALUES (%s, %s, %s, %s)", (11, 1, 1, 2)
        )
        cursor.execute("SELECT `winner_id` FROM `MatchResult` WHERE `match_id` = %s", (11,))
        assert cursor.fetchone()["winner_id"] is None
        cursor.execute("DELETE FROM `MatchResult` WHERE `match_id` = %s", (11,))


def test_team_player_composite_key_error(test_database: str) -> None:
    assignments = TeamPlayerRepository()
    with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT `team_id`, `player_id`, `join_date` FROM `TeamPlayer` ORDER BY `team_id`, `player_id` LIMIT 1")
        row = cursor.fetchone()
    with pytest.raises(DatabaseOperationError) as duplicate:
        assignments.add(row["team_id"], row["player_id"], row["join_date"])
    assert duplicate.value.errno == 1062

