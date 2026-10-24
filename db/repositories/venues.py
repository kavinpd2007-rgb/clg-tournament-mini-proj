"""Venue repository."""
from db.repositories.base import BaseRepository

class VenueRepository(BaseRepository):
    TABLE = "Venue"
    PRIMARY_KEY = "venue_id"
    COLUMNS = ("venue_id", "venue_name", "location", "capacity")
    SEARCH_COLUMNS = ("venue_name", "location", "capacity")
