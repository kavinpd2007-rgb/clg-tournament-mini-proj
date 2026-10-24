"""Persist the light/dark preference in the current user's app-data folder."""
from __future__ import annotations
import json
import os
from pathlib import Path
from .styles import DARK_THEME, LIGHT_THEME

APP_NAME = "CollegeSportsTournamentManager"


def settings_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    return root / APP_NAME / "settings.json"


def load_theme() -> str:
    try:
        value = json.loads(settings_path().read_text(encoding="utf-8")).get("theme")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        value = None
    return value if value in {LIGHT_THEME, DARK_THEME} else LIGHT_THEME


def save_theme(theme: str) -> None:
    if theme not in {LIGHT_THEME, DARK_THEME}:
        return
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"theme": theme}, indent=2), encoding="utf-8")
    except OSError:
        # Theme preference is best-effort; never interrupt the current session.
        return
