"""Team repository and eligible team lookup."""
from typing import Any
from db.connection import connection_scope
from db.repositories.base import BaseRepository

class TeamRepository(BaseRepository):
    TABLE = "Team"
    PRIMARY_KEY = "team_id"
    COLUMNS = ("team_id", "team_name", "department", "sport_id")
    SEARCH_COLUMNS = ("team_name", "department", "sport_id")

    def list_with_sport(self) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT t.`team_id`, t.`team_name`, t.`department`, t.`sport_id`, s.`sport_name` "
                "FROM `Team` AS t JOIN `Sport` AS s ON s.`sport_id` = t.`sport_id` "
                "ORDER BY t.`team_name`"
            )
            return list(cursor.fetchall())

    def eligible_for_match(self, sport_id: int, *, exclude_team_id: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT `team_id`, `team_name`, `department`, `sport_id` FROM `Team` WHERE `sport_id` = %s"
        params: tuple[Any, ...] = (sport_id,)
        if exclude_team_id is not None:
            sql += " AND `team_id` <> %s"
            params += (exclude_team_id,)
        sql += " ORDER BY `team_name`"
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
