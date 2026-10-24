"""Tournament repository."""
from typing import Any
from db.connection import connection_scope
from db.repositories.base import BaseRepository

class TournamentRepository(BaseRepository):
    TABLE = "Tournament"
    PRIMARY_KEY = "tournament_id"
    COLUMNS = ("tournament_id", "tournament_name", "sport_id", "start_date", "end_date")
    SEARCH_COLUMNS = ("tournament_name", "sport_id", "start_date", "end_date")

    def list_with_sport(self) -> list[dict[str, Any]]:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT t.`tournament_id`, t.`tournament_name`, t.`sport_id`, s.`sport_name`, "
                "t.`start_date`, t.`end_date` FROM `Tournament` AS t "
                "JOIN `Sport` AS s ON s.`sport_id` = t.`sport_id` ORDER BY t.`start_date`, t.`tournament_name`"
            )
            return list(cursor.fetchall())
