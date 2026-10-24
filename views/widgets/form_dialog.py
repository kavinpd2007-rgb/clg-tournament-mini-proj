"""Consistent modal forms with clear grouping and inline validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Callable, Mapping, Sequence
import ttkbootstrap as ttk
from .styles import card

Choice = tuple[str, Any]


@dataclass(frozen=True, slots=True)
class FieldSpec:
    key: str
    label: str
    kind: str = "text"
    required: bool = True
    choices: Sequence[Choice] = field(default_factory=tuple)
    initial: Any = None
    width: int = 38
    minimum: int | None = None
    maximum: int | None = None
    help_text: str = ""
    disabled: bool = False


class FormDialog(ttk.Toplevel):
    def __init__(self, parent, *, title: str, fields: Sequence[FieldSpec],
                 on_submit: Callable[[dict[str, Any]], Any] | None = None,
                 validator: Callable[[dict[str, Any]], None] | None = None,
                 read_only: bool = False):
        super().__init__(title=title, transient=parent, minsize=(580, 360), resizable=(True, True))
        self._fields = tuple(fields)
        self._on_submit, self._validator, self._read_only = on_submit, validator, read_only
        self._widgets: dict[str, Any] = {}
        self._variables: dict[str, Any] = {}
        self._choice_maps: dict[str, dict[str, Any]] = {}
        self._error_vars: dict[str, Any] = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        header = ttk.Frame(self, padding=(24, 18))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="", icon="clipboard2-check-fill", icon_size=20, bootstyle="primary").grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ttk.Label(header, text=title, style="SectionTitle.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Complete the fields below and save your changes.", style="Caption.TLabel").grid(row=1, column=1, sticky="w", pady=(3, 0))
        ttk.Separator(self).grid(row=1, column=0, sticky="new")
        body = ttk.Frame(self, padding=(24, 18, 24, 12))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)
        self.error = ttk.Label(body, text="", bootstyle="danger", wraplength=520)
        self.error.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        fields_panel = card(body, padding=(16, 12))
        fields_panel.grid(row=1, column=0, columnspan=2, sticky="nsew")
        fields_panel.columnconfigure(1, weight=1)
        for index, spec in enumerate(self._fields):
            row = index * 3
            ttk.Label(fields_panel, text=spec.label + (" *" if spec.required else ""), style="FormLabel.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 20), pady=(8, 6))
            widget, variable = self._create_field(fields_panel, spec)
            widget.grid(row=row, column=1, sticky="ew", pady=(4, 4))
            self._widgets[spec.key], self._variables[spec.key] = widget, variable
            self._error_vars[spec.key] = ttk.StringVar(value="")
            ttk.Label(fields_panel, textvariable=self._error_vars[spec.key], bootstyle="danger", style="Caption.TLabel").grid(row=row + 1, column=1, sticky="w")
            if spec.help_text:
                ttk.Label(fields_panel, text=spec.help_text, style="Caption.TLabel").grid(row=row + 2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        buttons = ttk.Frame(body)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", bootstyle="secondary outline", command=self.destroy, width=12).pack(side="right", padx=(10, 0))
        self.save_button = ttk.Button(buttons, text="Save", icon="check-lg", bootstyle="primary", command=self._save, width=13)
        self.save_button.pack(side="right")
        if read_only:
            self.save_button.pack_forget()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Return>", self._return_pressed)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()
        self.after(80, self._focus_first)
        height = min(720, 180 + len(self._fields) * 74)
        self.geometry(self._position(parent, 650, height))

    def _create_field(self, parent, spec):
        if spec.kind == "date":
            widget = ttk.DateEntry(parent, date_format="%Y-%m-%d", value=self._as_date(spec.initial), bootstyle="primary", width=spec.width)
            if self._read_only or spec.disabled: widget.configure(state="disabled")
            return widget, None
        if spec.kind == "datetime":
            shell = ttk.Frame(parent)
            shell.columnconfigure(0, weight=1)
            date_widget = ttk.DateEntry(shell, date_format="%Y-%m-%d", value=self._as_date(spec.initial), bootstyle="primary", width=20)
            date_widget.grid(row=0, column=0, sticky="w")
            time_var = ttk.StringVar(value=spec.initial.strftime("%H:%M") if isinstance(spec.initial, datetime) else "10:00")
            time_widget = ttk.Entry(shell, textvariable=time_var, width=10)
            ttk.Label(shell, text="Time (HH:MM)", style="Caption.TLabel").grid(row=0, column=1, padx=(14, 6))
            time_widget.grid(row=0, column=2, sticky="w")
            shell.date_widget, shell.time_widget = date_widget, time_widget
            if self._read_only or spec.disabled:
                date_widget.configure(state="disabled"); time_widget.configure(state="disabled")
            return shell, time_var
        variable = ttk.StringVar(value="")
        if spec.kind == "choice":
            mapping = {label: value for label, value in spec.choices}
            self._choice_maps[spec.key] = mapping
            reverse = {value: label for label, value in spec.choices}
            variable.set(reverse.get(spec.initial, ""))
            widget = ttk.Combobox(parent, textvariable=variable, values=tuple(mapping), state="readonly", width=spec.width)
        else:
            variable.set("" if spec.initial is None else str(spec.initial))
            widget = ttk.Entry(parent, textvariable=variable, width=spec.width)
        if self._read_only or spec.disabled:
            widget.configure(state="disabled")
        return widget, variable

    @staticmethod
    def _as_date(value):
        if isinstance(value, datetime): return value.date()
        if isinstance(value, date): return value
        if isinstance(value, str) and value:
            try: return date.fromisoformat(value[:10])
            except ValueError: return None
        return None

    def values(self):
        result = {}
        for spec in self._fields:
            if spec.disabled: continue
            widget = self._widgets[spec.key]
            if spec.kind == "date":
                result[spec.key] = self._date_widget_value(widget)
            elif spec.kind == "datetime":
                picked = self._date_widget_value(widget.date_widget)
                try:
                    hour, minute = map(int, self._variables[spec.key].get().strip().split(":"))
                    parsed = time(hour, minute)
                except (ValueError, TypeError):
                    raise ValueError(f"{spec.label} time must use HH:MM (24-hour time).") from None
                result[spec.key] = datetime.combine(picked, parsed) if picked else None
            elif spec.kind == "choice":
                result[spec.key] = self._choice_maps[spec.key].get(self._variables[spec.key].get())
            else:
                raw = self._variables[spec.key].get().strip()
                if spec.kind == "integer" and raw:
                    try: result[spec.key] = int(raw)
                    except ValueError: raise ValueError(f"{spec.label} must be a whole number.") from None
                else: result[spec.key] = raw
        return result

    @staticmethod
    def _date_widget_value(widget):
        parsed = widget.get_date()
        return parsed.date() if isinstance(parsed, datetime) else parsed

    def _save(self):
        if self._read_only or self._on_submit is None: return
        self.error.configure(text="")
        for variable in self._error_vars.values(): variable.set("")
        try:
            payload = self.values()
            self._check_required(payload)
            if self._validator: self._validator(payload)
            self.set_busy(True)
            result = self._on_submit(payload)
            if result is True: self.destroy()
            elif result is False: self.set_busy(False)
        except (ValueError, TypeError) as exc:
            self._show_validation_error(str(exc))
            self.set_busy(False)
        except Exception:
            self.error.configure(text="The form could not be saved. Review the fields and retry.")
            self.set_busy(False)

    def _check_required(self, values: Mapping[str, Any]):
        missing = [field for field in self._fields if field.required and not field.disabled and values.get(field.key) in (None, "")]
        if missing:
            field = missing[0]
            self._error_vars[field.key].set(f"{field.label} is required.")
            self._widgets[field.key].focus_set()
            raise ValueError(f"Required: {', '.join(item.label for item in missing)}")
        for spec in self._fields:
            value = values.get(spec.key)
            if value is None: continue
            if spec.kind == "integer":
                if spec.minimum is not None and value < spec.minimum: raise ValueError(f"{spec.label} must be at least {spec.minimum}.")
                if spec.maximum is not None and value > spec.maximum: raise ValueError(f"{spec.label} must be no more than {spec.maximum}.")

    def _show_validation_error(self, message):
        for spec in self._fields:
            if spec.label.casefold() in message.casefold():
                self._error_vars[spec.key].set(message)
                self.error.configure(text="Please correct the highlighted field.")
                return
        self.error.configure(text=message)

    def set_busy(self, busy):
        if not self._read_only:
            self.save_button.configure(state="disabled" if busy else "normal", text="Saving…" if busy else "Save")

    def set_error(self, message):
        self.error.configure(text=message)
        self.set_busy(False)

    def set_choices(self, key, choices: Sequence[Choice]):
        mapping = {label: value for label, value in choices}
        self._choice_maps[key] = mapping
        self._widgets[key].configure(values=tuple(mapping))
        if self._variables[key].get() not in mapping:
            self._variables[key].set("")

    def bind_choice_change(self, key, callback):
        self._widgets[key].bind("<<ComboboxSelected>>", lambda _event: callback(self._choice_maps[key].get(self._variables[key].get())))

    def close(self): self.destroy()

    def _return_pressed(self, _event=None):
        if not self._read_only: self._save()
        return "break"

    def _focus_first(self):
        if self._read_only: return
        spec = next((field for field in self._fields if not field.disabled), None)
        if spec is None: return
        widget = self._widgets[spec.key]
        if spec.kind == "date": widget.entry.focus_set()
        elif spec.kind == "datetime": widget.date_widget.entry.focus_set()
        else: widget.focus_set()

    @staticmethod
    def _position(parent, width, height):
        root = parent.winfo_toplevel()
        root.update_idletasks()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - width) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - height) // 2)
        return f"{width}x{height}+{x}+{y}"

