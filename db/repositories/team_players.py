"""TeamPlayer assignment repository."""
from datetime import date
from typing import Any
from db.connection import connection_scope, transaction

class TeamPlayerRepository:
    def list_for_team(self, team_id: int) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT tp.`team_id`, tp.`player_id`, p.`name`, p.`register_no`, p.`department`, tp.`join_date` "
                "FROM `TeamPlayer` AS tp JOIN `Player` AS p ON p.`player_id` = tp.`player_id` "
                "WHERE tp.`team_id` = %s ORDER BY p.`name`",
                (team_id,),
            )
            return list(cursor.fetchall())

    def add(self, team_id: int, player_id: int, join_date: date) -> None:
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO `TeamPlayer` (`team_id`, `player_id`, `join_date`) VALUES (%s, %s, %s)",
                (team_id, player_id, join_date),
            )

    def remove(self, team_id: int, player_id: int) -> bool:
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM `TeamPlayer` WHERE `team_id` = %s AND `player_id` = %s",
                (team_id, player_id),
            )
            return cursor.rowcount > 0
