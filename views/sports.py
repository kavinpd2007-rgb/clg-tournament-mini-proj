"""Sports catalog management screen."""
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec
from views.widgets.form_dialog import FieldSpec
from db.repositories.sports import SportRepository
from services.crud import ValidatedCrudService, validate_sport

class SportsPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Sports", singular="Sport",
            description="Maintain the college sports catalog used by teams and tournaments.",
            columns=(
                ColumnSpec("sport_id", "ID", 72, "center"),
                ColumnSpec("sport_name", "Sport name", 260),
                ColumnSpec("type", "Category", 190),
            ),
            fields=(
                FieldSpec("sport_name", "Sport name"),
                FieldSpec("type", "Category"),
            ),
            service=ValidatedCrudService(SportRepository(), validate_sport),
            empty_message="No sports yet. Click Add Sport to create the first record.",
        )
