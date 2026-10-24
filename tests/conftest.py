"""Integration fixture always pins repository calls to DB_TEST_NAME."""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Iterator

import pytest

from config import load_settings
from db.test_database import rebuild_test_database, validate_test_database_name


@pytest.fixture(scope="session")
def test_database() -> Iterator[str]:
    settings = load_settings()
    name = validate_test_database_name(settings.db_test_name)
    if not settings.mysql_user:
        pytest.skip("Set MYSQL_USER in .env to run MySQL integration tests.")
    old_database = os.environ.get("MYSQL_DATABASE")
    os.environ["MYSQL_DATABASE"] = name
    test_settings = replace(settings, mysql_database=name)
    try:
        rebuild_test_database(test_settings)
        yield name
    finally:
        if old_database is None:
            os.environ.pop("MYSQL_DATABASE", None)
        else:
            os.environ["MYSQL_DATABASE"] = old_database
