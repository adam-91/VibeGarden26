from __future__ import annotations

import pytest

from src.database.connection import DatabaseConnection
from src.database.schema import SCHEMA_SQL


@pytest.fixture
def memory_db(monkeypatch):
    import sqlite3

    db = DatabaseConnection.__new__(DatabaseConnection)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    db._connection = conn

    import src.database.connection as db_conn
    monkeypatch.setattr(db_conn, "db", db)

    yield db
    conn.close()
    db._connection = None
