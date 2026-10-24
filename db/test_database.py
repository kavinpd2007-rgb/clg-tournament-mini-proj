"""Safe builder for the isolated integration-test database."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import mysql.connector

from config import PROJECT_ROOT, Settings, load_settings
from db.connection import connection_scope
from db.errors import DatabaseOperationError, translate_mysql_error

LOGGER = logging.getLogger(__name__)
DEFAULT_TEST_DATABASE = "CollegeSportsDB_test"
TEST_SCHEMA_FILE = PROJECT_ROOT / "sql" / "test_schema.sql"


def validate_test_database_name(name: str) -> str:
    """Require a simple SQL identifier with the explicit test suffix."""
    if not re.fullmatch(r"[A-Za-z0-9_]+_test", name):
        raise ValueError("Refusing database reset: DB_TEST_NAME must be a simple identifier ending in '_test'.")
    return name


def split_sql_statements(script: str) -> list[str]:
    """Split semicolon-terminated SQL while respecting strings and comments."""
    statements: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    index = 0
    line_comment = False
    block_comment = False
    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
                buffer.append(char)
            index += 1
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if quote:
            buffer.append(char)
            if char == "\\" and quote != "`" and next_char:
                buffer.append(next_char)
                index += 2
                continue
            if char == quote:
                if next_char == quote:
                    buffer.append(next_char)
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            index += 2
            continue
        if char == "#" or (char == "-" and next_char == "-" and (index + 2 == len(script) or script[index + 2].isspace())):
            line_comment = True
            index += 2 if char == "-" else 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer.clear()
            index += 1
            continue
        buffer.append(char)
        index += 1
    if quote or block_comment:
        raise ValueError("The test schema contains an unterminated SQL string or comment.")
    trailing = "".join(buffer).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _schema_for_database(database_name: str) -> str:
    schema = TEST_SCHEMA_FILE.read_text(encoding="utf-8-sig")
    if DEFAULT_TEST_DATABASE not in schema:
        raise RuntimeError("The test schema does not contain its expected test database name.")
    return schema.replace(DEFAULT_TEST_DATABASE, database_name)


def rebuild_test_database(settings: Settings | None = None) -> None:
    """Drop and rebuild only DB_TEST_NAME after suffix validation."""
    active = settings or load_settings()
    database_name = validate_test_database_name(active.db_test_name)
    schema = _schema_for_database(database_name)
    # The configured identifier is restricted to letters, digits and underscores.
    with connection_scope(settings=active, use_application_database=False) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
            for statement in split_sql_statements(schema):
                cursor.execute(statement)
        except mysql.connector.Error as exc:
            connection.rollback()
            LOGGER.error("Test database rebuild failed: errno=%s", getattr(exc, "errno", None))
            raise translate_mysql_error(exc) from exc
        finally:
            cursor.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop and rebuild only the configured _test database.")
    parser.add_argument("--reset", action="store_true", help="Confirm the destructive test-database rebuild")
    args = parser.parse_args()
    if not args.reset:
        parser.error("Pass --reset to rebuild the database named in DB_TEST_NAME.")
    rebuild_test_database()
    print("Test database rebuilt successfully.")


if __name__ == "__main__":
    main()
