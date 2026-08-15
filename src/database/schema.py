SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS locations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    latitude    REAL    NOT NULL,
    longitude   REAL    NOT NULL,
    timezone    TEXT    NOT NULL,
    is_default  INTEGER DEFAULT 0,
    last_used   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT    NOT NULL,
    description         TEXT    DEFAULT '',
    category            TEXT    DEFAULT 'general',
    start_date          TEXT    NOT NULL,
    end_date            TEXT,
    start_time          TEXT,
    end_time            TEXT,
    is_all_day          INTEGER DEFAULT 0,
    color               TEXT    DEFAULT '#4CAF50',
    location_id         INTEGER,
    recurrence_type     TEXT    DEFAULT 'none',
    recurrence_interval INTEGER DEFAULT 1,
    recurrence_end_date TEXT,
    reminder_enabled    INTEGER DEFAULT 0,
    reminder_value      INTEGER DEFAULT 1,
    reminder_unit       TEXT    DEFAULT 'day',
    created_at          TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
"""

MIGRATIONS = [
    # v1 → v2: add recurrence and reminder columns
    [
        "ALTER TABLE events ADD COLUMN recurrence_type TEXT DEFAULT 'none'",
        "ALTER TABLE events ADD COLUMN recurrence_interval INTEGER DEFAULT 1",
        "ALTER TABLE events ADD COLUMN recurrence_end_date TEXT",
        "ALTER TABLE events ADD COLUMN reminder_enabled INTEGER DEFAULT 0",
        "ALTER TABLE events ADD COLUMN reminder_value INTEGER DEFAULT 1",
        "ALTER TABLE events ADD COLUMN reminder_unit TEXT DEFAULT 'day'",
        "CREATE INDEX IF NOT EXISTS idx_events_recurrence ON events(recurrence_type)",
    ],
]
