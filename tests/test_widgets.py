from datetime import date, datetime

from views.widgets.data_table import ColumnSpec, DataTable


def test_column_formats_dates_for_display() -> None:
    assert ColumnSpec("date", "Date").format(date(2026, 11, 2)) == "02 Nov 2026"
    assert ColumnSpec("date", "Date").format(datetime(2026, 11, 2, 10, 30)) == "02 Nov 2026 · 10:30"


def test_table_sort_keys_cover_numbers_and_text() -> None:
    assert DataTable._sortable(12) == (1, 12)
    assert DataTable._sortable("12") == (1, 12.0)
    assert DataTable._sortable("Cricket") == (2, "cricket")
    assert DataTable._sortable(None) == (0, "")
