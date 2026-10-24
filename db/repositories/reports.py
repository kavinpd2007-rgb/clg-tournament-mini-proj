"""Read-only reports backed by the existing view and procedure."""
from typing import Any
from db.connection import connection_scope

class ReportRepository:
    def standings(self, tournament_id: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM `TournamentStandings`"
        params: tuple[Any, ...] = ()
        if tournament_id is not None:
            sql += " WHERE `tournament_id` = %s"
            params = (tournament_id,)
        sql += " ORDER BY `tournament_id`, `points` DESC, `wins` DESC, `team_name`"
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def team_matches(self, team_id: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with connection_scope() as connection, connection.cursor() as cursor:
            cursor.callproc("GetTeamMatches", (team_id,))
            for stored in cursor.stored_results():
                try:
                    columns = [column[0] for column in stored.description or ()]
                    rows.extend(dict(zip(columns, row)) for row in stored.fetchall())
                finally:
                    stored.close()
        return rows
    def wins_per_team(self) -> list[dict[str, Any]]:
        query = (
            "SELECT t.`team_id`, t.`team_name`, COUNT(m.`match_id`) AS `wins` "
            "FROM `Team` AS t LEFT JOIN `MatchResult` AS r ON r.`winner_id` = t.`team_id` "
            "LEFT JOIN `Matches` AS m ON m.`match_id` = r.`match_id` AND m.`status` = %s "
            "GROUP BY t.`team_id`, t.`team_name` ORDER BY `wins` DESC, t.`team_name`"
        )
        return self._fetch_all(query, ("Completed",))

    def matches_played(self) -> list[dict[str, Any]]:
        query = (
            "SELECT t.`team_id`, t.`team_name`, COUNT(m.`match_id`) AS `matches_played` "
            "FROM `Team` AS t LEFT JOIN `Matches` AS m ON "
            "(t.`team_id` = m.`team1_id` OR t.`team_id` = m.`team2_id`) AND m.`status` = %s "
            "GROUP BY t.`team_id`, t.`team_name` ORDER BY `matches_played` DESC, t.`team_name`"
        )
        return self._fetch_all(query, ("Completed",))

    def total_score_per_team(self) -> list[dict[str, Any]]:
        query = (
            "SELECT scores.`team_id`, scores.`team_name`, SUM(scores.`score`) AS `total_score` FROM ("
            "SELECT t1.`team_id`, t1.`team_name`, r.`team1_score` AS `score` FROM `Matches` AS m "
            "JOIN `Team` AS t1 ON t1.`team_id` = m.`team1_id` JOIN `MatchResult` AS r ON r.`match_id` = m.`match_id` "
            "WHERE m.`status` = %s UNION ALL "
            "SELECT t2.`team_id`, t2.`team_name`, r.`team2_score` AS `score` FROM `Matches` AS m "
            "JOIN `Team` AS t2 ON t2.`team_id` = m.`team2_id` JOIN `MatchResult` AS r ON r.`match_id` = m.`match_id` "
            "WHERE m.`status` = %s) AS scores GROUP BY scores.`team_id`, scores.`team_name` "
            "ORDER BY `total_score` DESC, scores.`team_name`"
        )
        return self._fetch_all(query, ("Completed", "Completed"))

    def upcoming_matches(self) -> list[dict[str, Any]]:
        query = (
            "SELECT m.`match_id`, tr.`tournament_name`, t1.`team_name` AS `team1_name`, "
            "t2.`team_name` AS `team2_name`, v.`venue_name`, m.`match_date`, m.`status` "
            "FROM `Matches` AS m JOIN `Tournament` AS tr ON tr.`tournament_id` = m.`tournament_id` "
            "JOIN `Team` AS t1 ON t1.`team_id` = m.`team1_id` JOIN `Team` AS t2 ON t2.`team_id` = m.`team2_id` "
            "JOIN `Venue` AS v ON v.`venue_id` = m.`venue_id` WHERE m.`status` = %s "
            "ORDER BY m.`match_date`"
        )
        return self._fetch_all(query, ("Scheduled",))

    def dashboard_counts(self) -> dict[str, int]:
        tables = {"players": "Player", "teams": "Team", "sports": "Sport", "tournaments": "Tournament", "venues": "Venue", "matches": "Matches"}
        counts: dict[str, int] = {}
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            for key, table in tables.items():
                cursor.execute(f"SELECT COUNT(*) AS `total` FROM `{table}`")
                counts[key] = int(cursor.fetchone()["total"])
        return counts

    def _fetch_all(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())


