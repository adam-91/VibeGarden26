from __future__ import annotations

from typing import Optional

from src.database.connection import db
from src.models import Location


class LocationRepository:
    def get_all(self) -> list[Location]:
        rows = db.connection.execute(
            "SELECT * FROM locations ORDER BY last_used DESC"
        ).fetchall()
        return [self._row_to_location(r) for r in rows]

    def get_default(self) -> Optional[Location]:
        row = db.connection.execute(
            "SELECT * FROM locations WHERE is_default=1 LIMIT 1"
        ).fetchone()
        return self._row_to_location(row) if row else None

    def upsert(self, location: Location) -> int:
        existing = db.connection.execute(
            "SELECT id FROM locations WHERE latitude=? AND longitude=?",
            (location.latitude, location.longitude),
        ).fetchone()
        if existing:
            db.connection.execute(
                "UPDATE locations SET name=?, timezone=?, last_used=datetime('now') WHERE id=?",
                (location.name, location.timezone, existing["id"]),
            )
            db.connection.commit()
            return existing["id"]
        cursor = db.connection.execute(
            """INSERT INTO locations (name, latitude, longitude, timezone, is_default)
               VALUES (?, ?, ?, ?, ?)""",
            (location.name, location.latitude, location.longitude,
             location.timezone, int(location.is_default)),
        )
        db.connection.commit()
        return cursor.lastrowid

    def set_default(self, location_id: int) -> None:
        db.connection.execute("UPDATE locations SET is_default=0")
        db.connection.execute(
            "UPDATE locations SET is_default=1 WHERE id=?", (location_id,)
        )
        db.connection.commit()

    @staticmethod
    def _row_to_location(row) -> Optional[Location]:
        if row is None:
            return None
        return Location(
            id=row["id"],
            name=row["name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            timezone=row["timezone"],
            is_default=bool(row["is_default"]),
            last_used=row["last_used"] or "",
        )
