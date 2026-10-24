"""Shared list/detail/edit/delete page for simple entities."""
from __future__ import annotations
from dataclasses import replace
from typing import Any, Callable, Mapping, Sequence
import ttkbootstrap as ttk
from views.widgets.data_table import ColumnSpec, DataTable
from views.widgets.feedback import ConfirmDialog, Toast
from views.widgets.form_dialog import FieldSpec, FormDialog
from views.widgets.page_header import PageHeader


class CrudPage(ttk.Frame):
    def __init__(self, master, shell, *, title: str, description: str, singular: str,
                 columns: Sequence[ColumnSpec], fields: Sequence[FieldSpec], service,
                 empty_message: str):
        super().__init__(master, padding=24)
        self.shell, self.title, self.singular = shell, title, singular
        self.fields, self.service = tuple(fields), service
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.header = PageHeader(self, title, description, action_text=f"Add {singular}", action=self.add_new, can_write=shell.can_write)
        self.header.grid(row=0, column=0, sticky="ew")
        self.table = DataTable(self, columns, singular=singular, on_view=self.view_row,
                               on_edit=self.edit_row, on_delete=self.delete_row,
                               read_only=not shell.can_write, empty_message=empty_message)
        self.table.grid(row=1, column=0, sticky="nsew")
        self.load()

    def load(self):
        self.shell.run_task(self.service.list_all, self.table.set_rows)

    def focus_search(self):
        self.table.focus_search()

    def add_new(self):
        if self.shell.can_write:
            self._open_form(f"Add {self.singular}", None)

    def view_row(self, row: Mapping[str, Any]):
        self._show_form(f"{self.singular} details", row, read_only=True)

    def edit_row(self, row: Mapping[str, Any]):
        if self.shell.can_write:
            self._open_form(f"Edit {self.singular}", row)

    def delete_row(self, row: Mapping[str, Any]):
        if not self.shell.can_write:
            return
        label = self._row_label(row)
        if not ConfirmDialog.ask(self, title=f"Delete {self.singular}?", message=f"Delete {label}? This action cannot be undone."):
            return
        self.shell.run_task(lambda: self.service.delete(int(row[self._primary_key()])), lambda _result: self._deleted(label))

    def delete_selected(self):
        row = self.table.selected_row()
        if row is not None:
            self.delete_row(row)

    def _open_form(self, title: str, row: Mapping[str, Any] | None,
                   field_overrides: Mapping[str, FieldSpec] | None = None,
                   dialog_configurator: Callable[[FormDialog], None] | None = None):
        overrides = field_overrides or {}
        fields = tuple(replace(overrides.get(field.key, field), initial=row.get(field.key) if row else overrides.get(field.key, field).initial) for field in self.fields)
        dialog_ref: dict[str, FormDialog] = {}
        record_id = int(row[self._primary_key()]) if row else None
        def submit(values):
            dialog = dialog_ref["dialog"]
            operation = (lambda: self.service.create(values)) if record_id is None else (lambda: self.service.update(record_id, values))
            dialog.set_busy(True)
            self.shell.run_task(operation,
                lambda _result: self._saved(dialog, "added" if record_id is None else "updated"),
                lambda error: dialog.set_error(str(error)))
        dialog = FormDialog(self, title=title, fields=fields, on_submit=submit)
        dialog_ref["dialog"] = dialog
        if dialog_configurator:
            dialog_configurator(dialog)

    def _show_form(self, title: str, row: Mapping[str, Any], *, read_only: bool):
        fields = tuple(replace(field, initial=row.get(field.key)) for field in self.fields)
        FormDialog(self, title=title, fields=fields, read_only=read_only)

    def _saved(self, dialog: FormDialog, action: str):
        dialog.close()
        message = f"{self.singular} {action} successfully."
        self.shell.set_status(message, success=True)
        Toast.show(self, message)
        self.load()

    def _deleted(self, label: str):
        message = f"Deleted {label}."
        self.shell.set_status(message, success=True)
        Toast.show(self, message)
        self.load()

    def _primary_key(self):
        return getattr(self.service.repository, "PRIMARY_KEY")

    def _row_label(self, row):
        for key in ("name", "sport_name", "venue_name", "tournament_name", "team_name", "register_no"):
            if row.get(key):
                return str(row[key])
        return f"{self.singular} #{row.get(self._primary_key())}"
