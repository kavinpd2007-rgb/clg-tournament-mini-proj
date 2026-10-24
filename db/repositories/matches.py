"""Match scheduling repository."""
from typing import Any, Mapping
from db.connection import connection_scope, transaction

class MatchRepository:
    def list_with_details(self, search: str = "") -> list[dict[str, Any]]:
        sql = (
            "SELECT m.`match_id`, m.`tournament_id`, tr.`tournament_name`, m.`team1_id`, "
            "t1.`team_name` AS `team1_name`, m.`team2_id`, t2.`team_name` AS `team2_name`, "
            "m.`venue_id`, v.`venue_name`, m.`match_date`, m.`status`, r.`result_id` "
            "FROM `Matches` AS m JOIN `Tournament` AS tr ON tr.`tournament_id` = m.`tournament_id` "
            "JOIN `Team` AS t1 ON t1.`team_id` = m.`team1_id` "
            "JOIN `Team` AS t2 ON t2.`team_id` = m.`team2_id` "
            "JOIN `Venue` AS v ON v.`venue_id` = m.`venue_id` "
            "LEFT JOIN `MatchResult` AS r ON r.`match_id` = m.`match_id`"
        )
        params: tuple[str, ...] = ()
        if search.strip():
            sql += (
                " WHERE tr.`tournament_name` LIKE %s OR t1.`team_name` LIKE %s "
                "OR t2.`team_name` LIKE %s OR v.`venue_name` LIKE %s OR m.`status` LIKE %s"
            )
            needle = f"%{search.strip()}%"
            params = (needle, needle, needle, needle, needle)
        sql += " ORDER BY m.`match_date`, m.`match_id`"
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def get(self, match_id: int) -> dict[str, Any] | None:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM `Matches` WHERE `match_id` = %s", (match_id,))
            return cursor.fetchone()

    def add(self, values: Mapping[str, Any]) -> int:
        allowed = {"tournament_id", "team1_id", "team2_id", "venue_id", "match_date", "status"}
        if set(values) - allowed:
            raise ValueError("Unsupported match fields.")
        if values.get("status", "Scheduled") == "Completed":
            raise ValueError("A match becomes Completed only when a result is saved.")
        columns = tuple(values)
        sql = "INSERT INTO `Matches` (" + ", ".join(f"`{c}`" for c in columns) + ") VALUES (" + ", ".join("%s" for _ in columns) + ")"
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(sql, tuple(values[c] for c in columns))
            return int(cursor.lastrowid)

    def update(self, match_id: int, values: Mapping[str, Any]) -> bool:
        allowed = {"tournament_id", "team1_id", "team2_id", "venue_id", "match_date", "status"}
        if not values or set(values) - allowed:
            raise ValueError("Choose valid match fields to update.")
        if values.get("status") == "Completed":
            raise ValueError("A match becomes Completed only when a result is saved.")
        assignments = ", ".join(f"`{column}` = %s" for column in values)
        with transaction() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM `Matches` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            current = cursor.fetchone()
            if current is None:
                return False
            cursor.execute("SELECT `result_id` FROM `MatchResult` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            has_result = cursor.fetchone() is not None
            if has_result and any(
                key in values and values[key] != current[key]
                for key in ("team1_id", "team2_id", "tournament_id")
            ):
                raise ValueError("Delete this match's result before changing its teams or tournament.")
            if has_result and values.get("status") == "Cancelled":
                raise ValueError("A match with a result cannot be cancelled. Delete the result first.")
            if has_result and "status" in values and values["status"] != current["status"]:
                raise ValueError("A match with a result stays Completed. Delete the result before changing its status.")
            cursor.execute(
                f"UPDATE `Matches` SET {assignments} WHERE `match_id` = %s",
                (*values.values(), match_id),
            )
            return cursor.rowcount > 0

    def delete(self, match_id: int, *, confirm_result_cascade: bool = False) -> bool:
        with transaction() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT `match_id` FROM `Matches` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            if cursor.fetchone() is None:
                return False
            cursor.execute("SELECT `result_id` FROM `MatchResult` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            if cursor.fetchone() and not confirm_result_cascade:
                raise ValueError("This match has a result that will also be deleted. Confirm the deletion first.")
            cursor.execute("DELETE FROM `Matches` WHERE `match_id` = %s", (match_id,))
            return cursor.rowcount > 0







