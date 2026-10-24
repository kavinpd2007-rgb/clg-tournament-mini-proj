"""Match result entry and editing screen."""
from __future__ import annotations
from typing import Any, Mapping

import ttkbootstrap as ttk
from tkinter import messagebox

from services.results import ResultService
from views.widgets.data_table import ColumnSpec, DataTable
from views.widgets.feedback import ConfirmDialog, Toast
from views.widgets.form_dialog import FieldSpec, FormDialog
from views.widgets.page_header import PageHeader


class ResultsPage(ttk.Frame):
    def __init__(self, master, shell):
        super().__init__(master, padding=24)
        self.shell = shell
        self.service = ResultService()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        header = PageHeader(self, "Results", "Record scores and winners. Saving a result completes its match.", action_text="Add Result", action=self.add_new, can_write=shell.can_write)
        header.grid(row=0, column=0, sticky="ew")
        cols = (
            ColumnSpec("result_id", "ID", 64, "e"), ColumnSpec("tournament_name", "Tournament", 190),
            ColumnSpec("team1_name", "Team 1", 160), ColumnSpec("team1_score", "Score", 70, "e"),
            ColumnSpec("team2_score", "Score", 70, "e"), ColumnSpec("team2_name", "Team 2", 160),
            ColumnSpec("winner_name", "Winner / Draw", 145), ColumnSpec("status", "Status", 100),
        )
        self.table = DataTable(self, cols, singular="Result", on_view=self.view_row,
                               on_edit=self.edit_row, on_delete=self.delete_row, read_only=not shell.can_write,
                               empty_message="No results yet. Add a result for an eligible match.")
        self.table.grid(row=1, column=0, sticky="nsew")
        self.load()

    def load(self):
        self.shell.run_task(self.service.list_all, self.table.set_rows)

    def focus_search(self):
        self.table.focus_search()

    def delete_selected(self):
        row = self.table.selected_row()
        if row:
            self.delete_row(row)

    def add_new(self):
        if self.shell.can_write:
            self.shell.run_task(self.service.entry_matches, self._add_with_matches)

    def _add_with_matches(self, matches):
        if not matches:
            messagebox.showinfo("No eligible matches", "There are no Scheduled or Ongoing matches without a result.", parent=self)
            return
        choices = tuple((f"{m['tournament_name']} · {m['team1_name']} vs {m['team2_name']}", m["match_id"]) for m in matches)
        initial = matches[0]
        self._open("Add Result", None, matches, choices, initial)

    def view_row(self, row: Mapping[str, Any]):
        self._open("Result details", row, (), (), None, read_only=True)

    def edit_row(self, row: Mapping[str, Any]):
        if self.shell.can_write:
            self._open("Edit Result", row, (), (), None)

    def _open(self, title, row, matches, match_choices, selected_match, read_only=False):
        match_id = int(row["match_id"]) if row else None
        team1 = int(row["team1_id"]) if row else int(selected_match["team1_id"])
        team2 = int(row["team2_id"]) if row else int(selected_match["team2_id"])
        if row:
            match_label = f"{row['tournament_name']} · {row['team1_name']} vs {row['team2_name']}"
            choices = ((match_label, match_id),)
            winner_initial = row.get("winner_id")
            first_score, second_score = row["team1_score"], row["team2_score"]
        else:
            winner_initial, first_score, second_score = "", "", ""
            choices = match_choices
        winner_choices = (("Choose winner", ""), ("Draw", None), (row.get("team1_name", "Team 1") if row else selected_match["team1_name"], team1), (row.get("team2_name", "Team 2") if row else selected_match["team2_name"], team2))
        fields = (
            FieldSpec("match_id", "Match", kind="choice", choices=choices, initial=match_id or selected_match["match_id"], disabled=bool(row)),
            FieldSpec("team1_score", "Team 1 score", kind="integer", initial=first_score, minimum=0),
            FieldSpec("team2_score", "Team 2 score", kind="integer", initial=second_score, minimum=0),
            FieldSpec("winner_id", "Winner", kind="choice", choices=winner_choices, initial=winner_initial, required=False),
        )
        dialog_ref = {}
        def submit(values):
            dialog = dialog_ref["dialog"]
            dialog.set_busy(True)
            work = (lambda: self.service.create(values)) if row is None else (lambda: self.service.update(int(row["result_id"]), values))
            self.shell.run_task(work, lambda _result: self._saved(dialog, "added" if row is None else "updated"), lambda error: dialog.set_error(str(error)))
        dialog = FormDialog(self, title=title, fields=fields, on_submit=None if read_only else submit, read_only=read_only)
        dialog_ref["dialog"] = dialog
        if not row and matches:
            match_by_id = {m["match_id"]: m for m in matches}
            def match_changed(value):
                chosen = match_by_id.get(value)
                if chosen:
                    dialog.set_choices("winner_id", (("Choose winner", ""), ("Draw", None), (chosen["team1_name"], chosen["team1_id"]), (chosen["team2_name"], chosen["team2_id"])))
            dialog.set_choices("winner_id", (("Choose winner", ""), ("Draw", None), (selected_match["team1_name"], team1), (selected_match["team2_name"], team2)))
            dialog.bind_choice_change("match_id", match_changed)

    def delete_row(self, row):
        if not self.shell.can_write:
            return
        if not ConfirmDialog.ask(self, title="Delete result?", message="Delete this result? Its match status will return to Scheduled."):
            return
        self.shell.run_task(lambda: self.service.delete(int(row["result_id"]), confirmed=True), lambda _result: self._deleted())

    def _saved(self, dialog, action):
        dialog.close()
        self.shell.set_status(f"Result {action} successfully; match is Completed.", success=True)
        Toast.show(self, f"Result {action} successfully.")
        self.load()

    def _deleted(self):
        self.shell.set_status("Result deleted; match is now Scheduled.", success=True)
        Toast.show(self, "Result deleted.")
        self.load()
