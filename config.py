"""Application configuration loaded from a project-local .env file."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
LOG_FILE = PROJECT_ROOT / "logs" / "app.log"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for the desktop application."""

    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    db_test_name: str
    log_level: str


def load_settings() -> Settings:
    """Read settings from .env and the process environment."""
    load_dotenv(ENV_FILE)

    try:
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    except ValueError as exc:
        raise ValueError("MYSQL_PORT must be an integer.") from exc

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if level not in logging.getLevelNamesMapping():
        raise ValueError("LOG_LEVEL must be a valid Python logging level.")

    return Settings(
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=mysql_port,
        mysql_database=os.getenv("MYSQL_DATABASE", "CollegeSportsDB"),
        mysql_user=os.getenv("MYSQL_USER", ""),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        db_test_name=os.getenv("DB_TEST_NAME", "CollegeSportsDB_test"),
        log_level=level,
    )


def configure_logging(settings: Settings | None = None) -> None:
    """Configure UTF-8 file logging at logs/app.log."""
    active_settings = settings or load_settings()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=getattr(logging, active_settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


