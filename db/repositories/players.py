"""Player repository."""
from db.repositories.base import BaseRepository

class PlayerRepository(BaseRepository):
    TABLE = "Player"
    PRIMARY_KEY = "player_id"
    COLUMNS = ("player_id", "name", "register_no", "department", "year")
    SEARCH_COLUMNS = ("name", "register_no", "department", "year")
