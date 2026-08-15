from __future__ import annotations

from typing import Optional

from src.database.connection import db
from src.models import CalendarEvent


class EventRepository:
    def create(self, event: CalendarEvent) -> int:
        cursor = db.connection.execute(
            """INSERT INTO events (title, description, category, start_date,
               end_date, start_time, end_time, is_all_day, color, location_id,
               recurrence_type, recurrence_interval, recurrence_end_date,
               reminder_enabled, reminder_value, reminder_unit)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.title, event.description, event.category,
                event.start_date, event.end_date, event.start_time,
                event.end_time, int(event.is_all_day), event.color,
                event.location_id,
                event.recurrence_type, event.recurrence_interval,
                event.recurrence_end_date,
                int(event.reminder_enabled), event.reminder_value,
                event.reminder_unit,
            ),
        )
        db.connection.commit()
        return cursor.lastrowid

    def update(self, event: CalendarEvent) -> None:
        db.connection.execute(
            """UPDATE events SET title=?, description=?, category=?,
               start_date=?, end_date=?, start_time=?, end_time=?,
               is_all_day=?, color=?, location_id=?,
               recurrence_type=?, recurrence_interval=?, recurrence_end_date=?,
               reminder_enabled=?, reminder_value=?, reminder_unit=?
               WHERE id=?""",
            (
                event.title, event.description, event.category,
                event.start_date, event.end_date, event.start_time,
                event.end_time, int(event.is_all_day), event.color,
                event.location_id,
                event.recurrence_type, event.recurrence_interval,
                event.recurrence_end_date,
                int(event.reminder_enabled), event.reminder_value,
                event.reminder_unit, event.id,
            ),
        )
        db.connection.commit()

    def delete(self, event_id: int) -> None:
        db.connection.execute("DELETE FROM events WHERE id=?", (event_id,))
        db.connection.commit()

    def get_by_id(self, event_id: int) -> Optional[CalendarEvent]:
        row = db.connection.execute(
            "SELECT * FROM events WHERE id=?", (event_id,)
        ).fetchone()
        return self._row_to_event(row) if row else None

    def get_by_date_range(self, start: str, end: str) -> list[CalendarEvent]:
        rows = db.connection.execute(
            """SELECT * FROM events
               WHERE start_date <= ? AND (end_date >= ? OR end_date IS NULL)
               ORDER BY start_date, start_time""",
            (end, start),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_recurring(self) -> list[CalendarEvent]:
        rows = db.connection.execute(
            "SELECT * FROM events WHERE recurrence_type != 'none' ORDER BY start_date"
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_by_date(self, date_str: str) -> list[CalendarEvent]:
        rows = db.connection.execute(
            """SELECT * FROM events
               WHERE start_date <= ? AND (end_date >= ? OR end_date IS NULL)
               ORDER BY start_time""",
            (date_str, date_str),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_all(self) -> list[CalendarEvent]:
        rows = db.connection.execute(
            "SELECT * FROM events ORDER BY start_date, start_time"
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    @staticmethod
    def _row_to_event(row) -> CalendarEvent:
        return CalendarEvent(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            category=row["category"] or "general",
            start_date=row["start_date"],
            end_date=row["end_date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            is_all_day=bool(row["is_all_day"]),
            color=row["color"] or "#4CAF50",
            location_id=row["location_id"],
            recurrence_type=row["recurrence_type"] or "none",
            recurrence_interval=row["recurrence_interval"] or 1,
            recurrence_end_date=row["recurrence_end_date"],
            reminder_enabled=bool(row["reminder_enabled"]),
            reminder_value=row["reminder_value"] or 1,
            reminder_unit=row["reminder_unit"] or "day",
            created_at=row["created_at"] or "",
        )
