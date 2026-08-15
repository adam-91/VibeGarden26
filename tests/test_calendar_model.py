from __future__ import annotations

from datetime import date

from src.models import CalendarEvent
from src.ui.calendar.calendar_model import CalendarModel


def test_add_all_day_event(memory_db):
    model = CalendarModel()
    model.selected_date = date(2026, 8, 15)

    event = CalendarEvent(
        title="Urlop",
        category="general",
        start_date="2026-08-10",
        end_date="2026-08-15",
        is_all_day=True,
        color="#4CAF50",
    )
    event_id = model.add_event(event)

    assert event_id > 0
    events = model.get_events_for_date(date(2026, 8, 10))
    assert len(events) == 1
    assert events[0].title == "Urlop"
    assert events[0].is_all_day is True


def test_add_timed_event(memory_db):
    model = CalendarModel()
    model.selected_date = date(2026, 8, 15)

    event = CalendarEvent(
        title="Spotkanie",
        category="office",
        start_date="2026-08-12",
        start_time="10:00",
        end_time="11:30",
        is_all_day=False,
        color="#2196F3",
    )
    model.add_event(event)

    events = model.get_events_for_date(date(2026, 8, 12))
    assert len(events) == 1
    assert events[0].start_time == "10:00"
    assert events[0].end_time == "11:30"
    assert events[0].color == "#2196F3"


def test_add_events_with_distinct_colors(memory_db):
    model = CalendarModel()
    model.selected_date = date(2026, 8, 15)

    model.add_event(
        CalendarEvent(title="A", category="general", start_date="2026-08-03", color="#4CAF50")
    )
    model.add_event(
        CalendarEvent(title="B", category="office", start_date="2026-08-03", color="#2196F3")
    )
    model.add_event(
        CalendarEvent(title="C", category="garden", start_date="2026-08-03", color="#FF9800")
    )

    events = model.get_events_for_date(date(2026, 8, 3))
    assert len(events) == 3
    assert {e.color for e in events} == {"#4CAF50", "#2196F3", "#FF9800"}


def test_recurring_event_not_duplicated_on_start_date(memory_db):
    model = CalendarModel()
    model.selected_date = date(2026, 8, 15)

    event = CalendarEvent(
        title="Podlewanie",
        category="garden",
        start_date="2026-08-01",
        is_all_day=True,
        color="#FF9800",
        recurrence_type="weekly",
        recurrence_interval=1,
    )
    model.add_event(event)

    events = model.get_events_for_date(date(2026, 8, 1))
    assert len(events) == 1
    assert events[0].title == "Podlewanie"


def test_delete_event(memory_db):
    model = CalendarModel()
    model.selected_date = date(2026, 8, 15)

    event_id = model.add_event(
        CalendarEvent(title="Do usunięcia", start_date="2026-08-11")
    )
    assert len(model.get_events_for_date(date(2026, 8, 11))) == 1

    model.delete_event(event_id)
    assert model.get_events_for_date(date(2026, 8, 11)) == []
