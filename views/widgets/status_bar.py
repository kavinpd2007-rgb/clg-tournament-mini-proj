"""Small status strip for non-modal feedback."""
from __future__ import annotations
import ttkbootstrap as ttk

class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=(16, 8))
        self.message = ttk.StringVar(value="Ready")
        self.label = ttk.Label(self, textvariable=self.message, bootstyle="secondary")
        self.label.pack(side="left", fill="x", expand=True)

    def show(self, message: str, *, success: bool = False) -> None:
        self.message.set(message)
        self.label.configure(bootstyle="success" if success else "secondary")
