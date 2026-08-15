from __future__ import annotations

import contextlib
import logging

from src.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _instance: "DatabaseConnection | None" = None
    _connection: "sqlite3.Connection | None" = None  # noqa: F821

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def connection(self) -> "sqlite3.Connection":  # noqa: F821
        if self._connection is None:
            import sqlite3
            self._connection = sqlite3.connect(str(DATABASE_PATH))
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.row_factory = sqlite3.Row
            logger.info("Database connection established: %s", DATABASE_PATH)
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def init_schema(self) -> None:
        from src.database.schema import SCHEMA_SQL, MIGRATIONS
        conn = self.connection
        conn.executescript(SCHEMA_SQL)
        for migration_group in MIGRATIONS:
            for statement in migration_group:
                try:
                    conn.execute(statement)
                except Exception:
                    pass
        conn.commit()
        logger.info("Database schema initialized")


db = DatabaseConnection()
