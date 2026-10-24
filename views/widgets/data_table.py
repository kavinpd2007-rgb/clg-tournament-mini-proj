"""Reusable searchable, sortable table with clear action and empty states."""
from __future__ import annotations
import tkinter as tk
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Iterable, Mapping, Sequence
import ttkbootstrap as ttk
from .styles import card


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    key: str
    title: str
    width: int = 140
    anchor: str = "w"
    formatter: Callable[[Any], str] | None = None

    def format(self, value: Any) -> str:
        if self.formatter:
            return self.formatter(value)
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y · %H:%M")
        if isinstance(value, date):
            return value.strftime("%d %b %Y")
        return "" if value is None else str(value)


class DataTable(ttk.Frame):
    """Searchable and sortable Treeview with role-aware row actions."""
    def __init__(self, master, columns: Sequence[ColumnSpec], *, singular: str,
                 on_add: Callable[[], None] | None = None,
                 on_view: Callable[[Mapping[str, Any]], None] | None = None,
                 on_edit: Callable[[Mapping[str, Any]], None] | None = None,
                 on_delete: Callable[[Mapping[str, Any]], None] | None = None,
                 read_only: bool = False,
                 empty_message: str = "No records yet.",
                 filter_builders: Iterable[Callable[[Any, int], tk.Widget]] = ()):
        super().__init__(master)
        filter_builders = tuple(filter_builders)
        self.columns = tuple(columns)
        self.singular = singular
        self.on_add, self.on_view, self.on_edit, self.on_delete = on_add, on_view, on_edit, on_delete
        self._rows: list[dict[str, Any]] = []
        self._iid_to_row: dict[str, dict[str, Any]] = {}
        self._sort_key: str | None = None
        self._sort_desc = False
        self._search_after = None
        self._read_only = read_only
        self.empty_message = empty_message
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_toolbar(filter_builders)
        self._build_tree()
        self._build_context_menu()
        self.set_read_only(read_only)
        self._selection_changed()
        self.bind("<<ThemeChanged>>", self._theme_changed, add="+")

    def _build_toolbar(self, filter_builders) -> None:
        toolbar = card(self, padding=(14, 12))
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.grid_columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="", icon="search", icon_size=16, bootstyle="secondary").grid(row=0, column=0, padx=(0, 9))
        self.search_var = ttk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self._set_placeholder()
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_entry.bind("<KeyRelease>", self._schedule_search)
        for column, builder in enumerate(filter_builders, start=2):
            widget = builder(toolbar, column)
            widget.grid(row=0, column=column, padx=(10, 0))
        actions = ttk.Frame(toolbar)
        actions.grid(row=0, column=max(2, len(tuple(filter_builders)) + 2), sticky="e", padx=(12, 0))
        self.view_button = ttk.Button(actions, text="View", icon="eye", bootstyle="secondary outline", command=lambda: self._invoke(self.on_view))
        if self.on_view is not None:
            self.view_button.pack(side="left", padx=3)
        self.edit_button = ttk.Button(actions, text="Edit", icon="pencil-square", bootstyle="secondary outline", command=lambda: self._invoke(self.on_edit))
        if self.on_edit is not None:
            self.edit_button.pack(side="left", padx=3)
        self.delete_button = ttk.Button(actions, text="Delete", icon="trash3", bootstyle="danger outline", command=lambda: self._invoke(self.on_delete))
        if self.on_delete is not None:
            self.delete_button.pack(side="left", padx=3)
        self.add_button = ttk.Button(actions, text=f"Add {self.singular}", icon="plus-lg", bootstyle="primary", command=self.on_add)
        if self.on_add is not None:
            self.add_button.pack(side="left", padx=(8, 0))

    def _set_placeholder(self):
        self._placeholder = f"Search {self.singular.lower()}s…"
        self.search_var.set(self._placeholder)
        self.search_entry.configure(foreground=self.winfo_toplevel().style.colors.secondary)

    def _clear_placeholder(self, _event=None):
        if self.search_var.get() == self._placeholder:
            self.search_var.set("")
            self.search_entry.configure(foreground=self.winfo_toplevel().style.colors.inputfg)

    def _restore_placeholder(self, _event=None):
        if not self.search_var.get():
            self._set_placeholder()

    def _query(self) -> str:
        value = self.search_var.get()
        return "" if value == self._placeholder else value.strip().casefold()

    def _build_tree(self):
        panel = card(self, padding=8)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        frame = ttk.Frame(panel)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        keys = tuple(col.key for col in self.columns)
        self.tree = ttk.Treeview(frame, columns=keys, show="headings", selectmode="browse", height=12)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview, bootstyle="round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        for column in self.columns:
            self.tree.heading(column.key, text=column.title, command=lambda key=column.key: self.sort_by(key))
            self.tree.column(column.key, width=column.width, minwidth=72, anchor=column.anchor, stretch=True)
        self.empty_state = ttk.Frame(frame, style="Card.TFrame", padding=24)
        self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(self.empty_state, text="", icon="inbox", icon_size=24, bootstyle="secondary").pack(pady=(0, 8))
        ttk.Label(self.empty_state, text=self.empty_message, style="Caption.TLabel", wraplength=360, justify="center").pack()
        footer = ttk.Frame(panel, padding=(8, 10, 8, 2))
        footer.grid(row=1, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.row_count = ttk.Label(footer, text="0 records", style="Caption.TLabel")
        self.row_count.grid(row=0, column=0, sticky="w")
        ttk.Label(footer, text="Double-click a row to view or edit", style="Caption.TLabel").grid(row=0, column=1, sticky="e")
        self.tree.bind("<Double-1>", lambda _event: self._invoke(self.on_view if self._read_only else self.on_edit))
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        self.tree.bind("<Button-3>", self._popup_context_menu)
        self.tree.bind("<Motion>", self._hover_row)
        self._theme_changed()

    def _theme_changed(self, _event=None):
        colors = self.winfo_toplevel().style.colors
        self.tree.tag_configure("odd", background=colors.inputbg)
        self.tree.tag_configure("even", background=colors.bg)
        self.tree.tag_configure("hover", background=colors.active)
        for status, color in {"scheduled": colors.info, "ongoing": colors.warning, "completed": colors.success, "cancelled": colors.danger}.items():
            self.tree.tag_configure(f"status-{status}", foreground=color)
        if self.search_var.get() == self._placeholder:
            self.search_entry.configure(foreground=colors.secondary)

    def _hover_row(self, event):
        iid = self.tree.identify_row(event.y)
        if iid == getattr(self, "_hover_iid", None):
            return
        old = getattr(self, "_hover_iid", None)
        if old and self.tree.exists(old):
            self._set_row_tags(old)
        self._hover_iid = iid
        if iid:
            tags = list(self.tree.item(iid, "tags"))
            if "hover" not in tags:
                tags.append("hover")
            self.tree.item(iid, tags=tuple(tags))

    def _set_row_tags(self, iid):
        index = int(iid) if iid.isdigit() else 0
        row = self._iid_to_row.get(iid, {})
        status = str(row.get("status", "")).lower()
        tags = ["even" if index % 2 == 0 else "odd"]
        if status in {"scheduled", "ongoing", "completed", "cancelled"}:
            tags.append(f"status-{status}")
        self.tree.item(iid, tags=tuple(tags))

    def set_rows(self, rows: Iterable[Mapping[str, Any]]):
        self._rows = [dict(row) for row in rows]
        self._refresh()

    def set_read_only(self, read_only: bool):
        self._read_only = read_only
        if read_only:
            for button in (self.add_button, self.edit_button, self.delete_button):
                button.pack_forget()
        else:
            for button, callback, side, padx in (
                (self.edit_button, self.on_edit, "left", 3),
                (self.delete_button, self.on_delete, "left", 3),
                (self.add_button, self.on_add, "left", (8, 0)),
            ):
                if callback is not None and not button.winfo_manager():
                    button.pack(side=side, padx=padx)
        self._selection_changed()

    def focus_search(self):
        self.search_entry.focus_set()
        self._clear_placeholder()
        self.search_entry.selection_range(0, "end")

    def selected_row(self):
        selected = self.tree.selection()
        return self._iid_to_row.get(selected[0]) if selected else None

    def sort_by(self, key: str):
        if key not in {column.key for column in self.columns}:
            return
        self._sort_desc = not self._sort_desc if self._sort_key == key else False
        self._sort_key = key
        self._refresh()

    def _schedule_search(self, _event=None):
        if self._search_after:
            self.after_cancel(self._search_after)
        self._search_after = self.after(160, self._refresh)

    def _refresh(self):
        query = self._query()
        rows = [row for row in self._rows if not query or any(query in str(value or "").casefold() for value in row.values())]
        if self._sort_key:
            rows.sort(key=lambda row: self._sortable(row.get(self._sort_key)), reverse=self._sort_desc)
        self.tree.delete(*self.tree.get_children())
        self._iid_to_row.clear()
        for index, row in enumerate(rows):
            values = tuple(column.format(row.get(column.key)) for column in self.columns)
            tags = ["even" if index % 2 == 0 else "odd"]
            status = str(row.get("status", "")).casefold()
            if status in {"scheduled", "ongoing", "completed", "cancelled"}:
                tags.append(f"status-{status}")
            iid = str(index)
            self.tree.insert("", "end", iid=iid, values=values, tags=tuple(tags))
            self._iid_to_row[iid] = row
        if rows:
            self.empty_state.place_forget()
        else:
            self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
        self.row_count.configure(text=f"{len(rows)} {self.singular.lower()}" + ("s" if len(rows) != 1 else ""))
        for column in self.columns:
            marker = " ▲" if column.key == self._sort_key and not self._sort_desc else " ▼" if column.key == self._sort_key else ""
            self.tree.heading(column.key, text=column.title + marker)
            values = [row.get(column.key) for row in rows if row.get(column.key) is not None]
            numeric = bool(values) and all(isinstance(value, (int, float)) for value in values)
            if numeric and column.anchor == "w":
                self.tree.column(column.key, anchor="e")
        self._selection_changed()

    @staticmethod
    def _sortable(value: Any):
        if value is None:
            return 0, ""
        if isinstance(value, (int, float, date, datetime)):
            return 1, value
        try:
            return 1, float(value)
        except (TypeError, ValueError):
            return 2, str(value).casefold()

    def _invoke(self, callback):
        row = self.selected_row()
        if row is not None and callback is not None:
            callback(row)

    def _selection_changed(self, _event=None):
        selected = bool(self.tree.selection())
        if hasattr(self, "view_button"):
            self.view_button.configure(state="normal" if selected else "disabled")
        for button in (getattr(self, "edit_button", None), getattr(self, "delete_button", None)):
            if button is not None:
                button.configure(state="disabled" if self._read_only or not selected else "normal")

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=False)
        if self.on_view:
            self.context_menu.add_command(label="View", command=lambda: self._invoke(self.on_view))
        if self.on_edit:
            self.context_menu.add_command(label="Edit", command=lambda: self._invoke(self.on_edit))
        if self.on_delete:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Delete…", command=lambda: self._invoke(self.on_delete))

    def _popup_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
        for label in ("Edit", "Delete…"):
            try:
                self.context_menu.entryconfigure(label, state="disabled" if self._read_only else "normal")
            except tk.TclError:
                pass
        if iid:
            self.context_menu.tk_popup(event.x_root, event.y_root)


