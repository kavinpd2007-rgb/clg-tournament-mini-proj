"""Sport repository."""
from db.repositories.base import BaseRepository

class SportRepository(BaseRepository):
    TABLE = "Sport"
    PRIMARY_KEY = "sport_id"
    COLUMNS = ("sport_id", "sport_name", "type")
    SEARCH_COLUMNS = ("sport_name", "type")
