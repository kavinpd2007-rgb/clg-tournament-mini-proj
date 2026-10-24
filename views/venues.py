"""Venue management screen."""
from views.crud_page import CrudPage
from views.widgets.data_table import ColumnSpec
from views.widgets.form_dialog import FieldSpec
from db.repositories.venues import VenueRepository
from services.crud import ValidatedCrudService, validate_venue

class VenuesPage(CrudPage):
    def __init__(self, master, shell):
        super().__init__(
            master, shell, title="Venues", singular="Venue",
            description="Manage college grounds and courts with their locations and capacities.",
            columns=(
                ColumnSpec("venue_id", "ID", 72, "center"),
                ColumnSpec("venue_name", "Venue name", 250),
                ColumnSpec("location", "Location", 250),
                ColumnSpec("capacity", "Capacity", 130, "center"),
            ),
            fields=(
                FieldSpec("venue_name", "Venue name"),
                FieldSpec("location", "Location"),
                FieldSpec("capacity", "Capacity", kind="integer", minimum=1),
            ),
            service=ValidatedCrudService(VenueRepository(), validate_venue),
            empty_message="No venues yet. Click Add Venue to create the first record.",
        )
