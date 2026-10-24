"""Player management screen."""
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec
from views.widgets.form_dialog import FieldSpec
from db.repositories.players import PlayerRepository
from services.crud import ValidatedCrudService, validate_player

class PlayersPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Players", singular="Player",
            description="Register students, keep contact-free team records tidy, and search by name or register number.",
            columns=(
                ColumnSpec("player_id", "ID", 72, "center"),
                ColumnSpec("name", "Player name", 220),
                ColumnSpec("register_no", "Register number", 170),
                ColumnSpec("department", "Department", 190),
                ColumnSpec("year", "Year", 88, "center"),
            ),
            fields=(
                FieldSpec("name", "Player name"),
                FieldSpec("register_no", "Register number"),
                FieldSpec("department", "Department"),
                FieldSpec("year", "Year", kind="integer", minimum=1, maximum=5),
            ),
            service=ValidatedCrudService(PlayerRepository(), validate_player),
            empty_message="No players yet. Click Add Player to create the first record.",
        )
