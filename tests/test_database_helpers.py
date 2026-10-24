from __future__ import annotations

import pytest
from mysql.connector import Error as MySQLError

from db.errors import DatabaseOperationError, translate_mysql_error
from db.test_database import split_sql_statements, validate_test_database_name


def test_test_database_name_requires_test_suffix() -> None:
    assert validate_test_database_name("CollegeSportsDB_test") == "CollegeSportsDB_test"
    for unsafe in ("CollegeSportsDB", "CollegeSportsDB_test; DROP DATABASE x", "_test", "bad-name_test"):
        with pytest.raises(ValueError):
            validate_test_database_name(unsafe)


def test_sql_splitter_handles_semicolons_quotes_and_comments() -> None:
    source = """-- comment ;
    INSERT INTO t VALUES ('left;right', \"a;b\"); # tail ;
    /* block ; */ SELECT `a;b` FROM t;
    CREATE PROCEDURE p() SELECT 'done;';
    """
    statements = split_sql_statements(source)
    assert len(statements) == 3
    assert "left;right" in statements[0]
    assert "`a;b`" in statements[1]
    assert statements[2].startswith("CREATE PROCEDURE")


def test_sql_splitter_rejects_unterminated_literals() -> None:
    with pytest.raises(ValueError):
        split_sql_statements("SELECT 'unfinished;")


def test_error_translation_for_duplicate_fk_and_check() -> None:
    cases = {
        1062: "already exists",
        1451: "still referenced",
        1452: "no longer exists",
        3819: "violates a database rule",
    }
    for code, fragment in cases.items():
        translated = translate_mysql_error(MySQLError(msg="db error", errno=code))
        assert isinstance(translated, DatabaseOperationError)
        assert fragment in str(translated)


def test_connection_loss_is_retryable() -> None:
    translated = translate_mysql_error(MySQLError(msg="connection lost", errno=2013))
    assert translated.retryable is True
    assert "retry" in str(translated).lower()

def test_reference_schema_contains_only_the_test_database_and_expected_objects() -> None:
    from pathlib import Path

    schema = Path("sql/test_schema.sql").read_text(encoding="utf-8-sig")
    statements = split_sql_statements(schema)
    assert statements[0] == "CREATE DATABASE CollegeSportsDB_test"
    assert "CREATE TABLE AppUser" in schema
    assert "CREATE VIEW TournamentStandings" in schema
    assert "CREATE PROCEDURE GetTeamMatches" in schema
    assert "CREATE TRIGGER ValidateMatchResult" in schema
    for column in ("year", "type", "status", "name", "location"):
        assert f"`{column}`" in schema
    assert schema.count("INSERT INTO Matches") == 2
    assert schema.count("INSERT INTO MatchResult") == 2
    assert "Ramesh Kumar" not in schema
    assert "DELETE FROM Player" not in schema
    assert "VALUES (4, 1, -10, 80)" not in schema


