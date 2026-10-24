"""Shared confirmation, toast and tooltip helpers."""
from __future__ import annotations
import tkinter as tk
import tkinter.messagebox as messagebox
import ttkbootstrap as ttk
from .styles import badge_icon


class ConfirmDialog:
    @staticmethod
    def ask(parent, *, title: str, message: str, destructive: bool = True) -> bool:
        return bool(messagebox.askyesno(title, message, parent=parent, icon="warning" if destructive else "question"))


class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.window = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self.window or not self.text:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.attributes("-topmost", True)
        ttk.Label(self.window, text=self.text, padding=(8, 5), bootstyle="secondary").pack()
        self.window.geometry(f"+{self.widget.winfo_rootx()+8}+{self.widget.winfo_rooty()+self.widget.winfo_height()+4}")

    def _hide(self, _event=None):
        if self.window:
            self.window.destroy()
            self.window = None


class Toast:
    """Small non-modal notification anchored to the app's lower-right corner."""
    _active: list[tk.Toplevel] = []

    @classmethod
    def show(cls, parent, message: str, *, title: str = "Saved", success: bool = True) -> None:
        root = parent.winfo_toplevel()
        toast = ttk.Toplevel(root, title=title, transient=root, resizable=(False, False))
        toast.overrideredirect(True)
        style = "success" if success else "danger"
        icon = "check-circle-fill" if success else "exclamation-triangle-fill"
        panel = ttk.Frame(toast, padding=(16, 12), bootstyle=style)
        panel.pack(fill="both", expand=True)
        badge_icon(panel, icon, style, size=18).pack(side="left", padx=(0, 10))
        text = ttk.Frame(panel, bootstyle=style)
        text.pack(side="left", fill="both", expand=True)
        ttk.Label(text, text=title, bootstyle="light", style="ToastTitle.TLabel").pack(anchor="w")
        ttk.Label(text, text=message, bootstyle="light", wraplength=280).pack(anchor="w", pady=(2, 0))
        toast.update_idletasks()
        x = root.winfo_rootx() + max(16, root.winfo_width() - toast.winfo_width() - 24)
        y = root.winfo_rooty() + max(16, root.winfo_height() - toast.winfo_height() - 48)
        toast.geometry(f"+{x}+{y}")
        cls._active.append(toast)
        def dismiss():
            if toast in cls._active:
                cls._active.remove(toast)
            if toast.winfo_exists():
                toast.destroy()
        toast.after(3000, dismiss)


