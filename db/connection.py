"""MySQL connection and transaction helpers."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector.connection import MySQLConnection

from config import Settings, load_settings
from db.errors import DatabaseOperationError, translate_mysql_error

LOGGER = logging.getLogger(__name__)


def open_connection(*, database: str | None = None, settings: Settings | None = None) -> MySQLConnection:
    """Open a connection; ``database=None`` intentionally connects at server level."""
    active = settings or load_settings()
    params: dict[str, object] = {
        "host": active.mysql_host,
        "port": active.mysql_port,
        "user": active.mysql_user,
        "password": active.mysql_password,
        "connection_timeout": 5,
        "charset": "utf8mb4",
        "autocommit": False,
    }
    if database is not None:
        params["database"] = database
    try:
        connection = mysql.connector.connect(**params)
        connection.ping(reconnect=True, attempts=2, delay=1)
        return connection
    except mysql.connector.Error as exc:
        LOGGER.error("MySQL connection failed: errno=%s", getattr(exc, "errno", None))
        raise translate_mysql_error(exc) from exc


@contextmanager
def connection_scope(
    database: str | None = None,
    *,
    settings: Settings | None = None,
    use_application_database: bool = True,
) -> Iterator[MySQLConnection]:
    """Yield a live connection and always close it, translating driver errors."""
    active = settings or load_settings()
    selected_database = database
    if database is None and use_application_database:
        selected_database = active.mysql_database
    connection = open_connection(database=selected_database, settings=active)
    try:
        yield connection
    except mysql.connector.Error as exc:
        LOGGER.error("MySQL query failed: errno=%s", getattr(exc, "errno", None))
        raise translate_mysql_error(exc) from exc
    finally:
        try:
            connection.close()
        except mysql.connector.Error:
            LOGGER.warning("Failed to close MySQL connection cleanly")


@contextmanager
def transaction(
    database: str | None = None,
    *,
    settings: Settings | None = None,
    use_application_database: bool = True,
) -> Iterator[MySQLConnection]:
    """Run related writes atomically, rolling back on every exception."""
    with connection_scope(
        database,
        settings=settings,
        use_application_database=use_application_database,
    ) as connection:
        try:
            connection.start_transaction()
            yield connection
            connection.commit()
        except Exception as exc:
            try:
                connection.rollback()
            except mysql.connector.Error:
                LOGGER.exception("Rollback failed after a database operation error")
            if isinstance(exc, mysql.connector.Error):
                LOGGER.error("MySQL transaction failed: errno=%s", getattr(exc, "errno", None))
                raise translate_mysql_error(exc) from exc
            raise
