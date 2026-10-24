"""Match result repository; result and match status changes are atomic."""
from typing import Any

from db.connection import connection_scope, transaction


class MatchResultRepository:
    def list_with_details(self) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT r.`result_id`, r.`match_id`, m.`tournament_id`, tr.`tournament_name`, "
                "m.`team1_id`, m.`team2_id`, t1.`team_name` AS `team1_name`, t2.`team_name` AS `team2_name`, "
                "r.`winner_id`, CASE WHEN r.`winner_id` IS NULL THEN %s ELSE w.`team_name` END AS `winner_name`, "
                "r.`team1_score`, r.`team2_score`, m.`status` "
                "FROM `MatchResult` AS r JOIN `Matches` AS m ON m.`match_id` = r.`match_id` "
                "JOIN `Tournament` AS tr ON tr.`tournament_id` = m.`tournament_id` "
                "JOIN `Team` AS t1 ON t1.`team_id` = m.`team1_id` "
                "JOIN `Team` AS t2 ON t2.`team_id` = m.`team2_id` "
                "LEFT JOIN `Team` AS w ON w.`team_id` = r.`winner_id` ORDER BY m.`match_date` DESC",
                ("Draw",),
            )
            return list(cursor.fetchall())
    def get(self, result_id: int) -> dict[str, Any] | None:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM `MatchResult` WHERE `result_id` = %s", (result_id,))
            return cursor.fetchone()

    def for_match(self, match_id: int) -> dict[str, Any] | None:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM `MatchResult` WHERE `match_id` = %s", (match_id,))
            return cursor.fetchone()
    def entry_matches(self) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT m.`match_id`, m.`tournament_id`, tr.`tournament_name`, m.`team1_id`, "
                "t1.`team_name` AS `team1_name`, m.`team2_id`, t2.`team_name` AS `team2_name`, "
                "m.`match_date`, m.`status` FROM `Matches` AS m "
                "JOIN `Tournament` AS tr ON tr.`tournament_id` = m.`tournament_id` "
                "JOIN `Team` AS t1 ON t1.`team_id` = m.`team1_id` "
                "JOIN `Team` AS t2 ON t2.`team_id` = m.`team2_id` "
                "LEFT JOIN `MatchResult` AS r ON r.`match_id` = m.`match_id` "
                "WHERE m.`status` IN (%s, %s) AND r.`result_id` IS NULL ORDER BY m.`match_date`",
                ("Scheduled", "Ongoing"),
            )
            return list(cursor.fetchall())

    def add(self, match_id: int, winner_id: int | None, team1_score: int, team2_score: int) -> int:
        with transaction() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT `status` FROM `Matches` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            match = cursor.fetchone()
            if match is None:
                raise ValueError("This match no longer exists.")
            if match["status"] not in ("Scheduled", "Ongoing"):
                raise ValueError("Results can only be entered for Scheduled or Ongoing matches.")
            cursor.execute("SELECT `result_id` FROM `MatchResult` WHERE `match_id` = %s FOR UPDATE", (match_id,))
            if cursor.fetchone() is not None:
                raise ValueError("This match already has a result. Use Edit on its result.")
            cursor.execute(
                "INSERT INTO `MatchResult` (`match_id`, `winner_id`, `team1_score`, `team2_score`) VALUES (%s, %s, %s, %s)",
                (match_id, winner_id, team1_score, team2_score),
            )
            result_id = int(cursor.lastrowid)
            cursor.execute("UPDATE `Matches` SET `status` = %s WHERE `match_id` = %s", ("Completed", match_id))
            return result_id

    def update(self, result_id: int, match_id: int, winner_id: int | None, team1_score: int, team2_score: int) -> bool:
        with transaction() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT `result_id` FROM `MatchResult` WHERE `result_id` = %s AND `match_id` = %s FOR UPDATE", (result_id, match_id))
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "UPDATE `MatchResult` SET `winner_id` = %s, `team1_score` = %s, `team2_score` = %s WHERE `result_id` = %s AND `match_id` = %s",
                (winner_id, team1_score, team2_score, result_id, match_id),
            )
            cursor.execute("UPDATE `Matches` SET `status` = %s WHERE `match_id` = %s", ("Completed", match_id))
            return True

    def delete(self, result_id: int, match_id: int) -> bool:
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM `MatchResult` WHERE `result_id` = %s AND `match_id` = %s", (result_id, match_id))
            if cursor.rowcount == 0:
                return False
            cursor.execute("UPDATE `Matches` SET `status` = %s WHERE `match_id` = %s", ("Scheduled", match_id))
            return True



