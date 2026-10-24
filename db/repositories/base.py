"""Reusable parameterized CRUD operations for fixed table repositories."""

from __future__ import annotations

from typing import Any, Mapping

from db.connection import connection_scope, transaction


class BaseRepository:
    """CRUD helpers; table and column identifiers come only from subclasses."""

    TABLE = ""
    PRIMARY_KEY = ""
    COLUMNS: tuple[str, ...] = ()
    SEARCH_COLUMNS: tuple[str, ...] = ()

    def _select_columns(self) -> str:
        return ", ".join(f"`{column}`" for column in self.COLUMNS)

    def list_all(self) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(f"SELECT {self._select_columns()} FROM `{self.TABLE}` ORDER BY `{self.PRIMARY_KEY}`")
            return list(cursor.fetchall())

    def get(self, record_id: int) -> dict[str, Any] | None:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                f"SELECT {self._select_columns()} FROM `{self.TABLE}` WHERE `{self.PRIMARY_KEY}` = %s",
                (record_id,),
            )
            return cursor.fetchone()

    def search(self, text: str) -> list[dict[str, Any]]:
        if not self.SEARCH_COLUMNS:
            return self.list_all()
        predicates = " OR ".join(f"CAST(`{column}` AS CHAR) LIKE %s" for column in self.SEARCH_COLUMNS)
        parameters = tuple(f"%{text}%" for _ in self.SEARCH_COLUMNS)
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                f"SELECT {self._select_columns()} FROM `{self.TABLE}` WHERE {predicates} "
                f"ORDER BY `{self.PRIMARY_KEY}`",
                parameters,
            )
            return list(cursor.fetchall())

    def add(self, values: Mapping[str, Any]) -> int:
        selected = self._checked_values(values, allow_primary=False)
        columns = tuple(selected)
        placeholders = ", ".join("%s" for _ in columns)
        column_sql = ", ".join(f"`{column}`" for column in columns)
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO `{self.TABLE}` ({column_sql}) VALUES ({placeholders})",
                tuple(selected[column] for column in columns),
            )
            return int(cursor.lastrowid)

    def update(self, record_id: int, values: Mapping[str, Any]) -> bool:
        selected = self._checked_values(values, allow_primary=False)
        if not selected:
            raise ValueError("Choose at least one field to update.")
        assignments = ", ".join(f"`{column}` = %s" for column in selected)
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE `{self.TABLE}` SET {assignments} WHERE `{self.PRIMARY_KEY}` = %s",
                (*selected.values(), record_id),
            )
            return cursor.rowcount > 0

    def delete(self, record_id: int) -> bool:
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM `{self.TABLE}` WHERE `{self.PRIMARY_KEY}` = %s",
                (record_id,),
            )
            return cursor.rowcount > 0

    def _checked_values(self, values: Mapping[str, Any], *, allow_primary: bool) -> dict[str, Any]:
        allowed = set(self.COLUMNS)
        if not allow_primary:
            allowed.discard(self.PRIMARY_KEY)
        unknown = set(values) - allowed
        if unknown:
            raise ValueError("Unsupported fields: " + ", ".join(sorted(unknown)))
        return dict(values)
