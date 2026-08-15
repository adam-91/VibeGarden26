from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.models import CalendarEvent

HOUR_HEIGHT = 56
HOURS = 24
GUTTER = 52
ALL_DAY_ROW_HEIGHT = 26

_DEFAULT_COLOR = "#4CAF50"


def _parse_time(text: Optional[str]) -> int:
    if not text:
        return 0
    try:
        h, m = str(text).split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 0


class TimelineWidget(QWidget):
    edit_event = Signal(object)
    selection_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._events: list[CalendarEvent] = []
        self._blocks: list[tuple[QRectF, CalendarEvent]] = []
        self._all_day_rects: list[tuple[QRectF, CalendarEvent]] = []
        self._all_day_bars: list[tuple[QRectF, CalendarEvent]] = []
        self._selected_id: Optional[int] = None
        self._all_day_height = 0
        self.setMinimumWidth(220)

    def set_events(self, events: list[CalendarEvent]) -> None:
        self._events = list(events)
        self._selected_id = None
        self._recalc()
        self.update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._recalc()
        self.update()

    def selected_event(self) -> Optional[CalendarEvent]:
        for _, ev in self._blocks + self._all_day_rects:
            if ev.id == self._selected_id:
                return ev
        return None

    def _recalc(self) -> None:
        all_day = [e for e in self._events if e.is_all_day]
        timed = [e for e in self._events if not e.is_all_day]
        self._all_day_height = ALL_DAY_ROW_HEIGHT * len(all_day) + 8 if all_day else 4
        self._blocks = []
        self._all_day_rects = []
        self._all_day_bars = []

        for i, ev in enumerate(all_day):
            y = 4 + i * ALL_DAY_ROW_HEIGHT
            rect = QRectF(GUTTER, y, max(10, self.width() - GUTTER - 8), ALL_DAY_ROW_HEIGHT - 4)
            self._all_day_rects.append((rect, ev))

        full_day_top = self._all_day_height
        full_day_h = HOURS * HOUR_HEIGHT
        for i, ev in enumerate(all_day):
            bar_rect = QRectF(2 + i * 6, full_day_top, 4, full_day_h)
            self._all_day_bars.append((bar_rect, ev))

        timed_sorted = sorted(
            timed, key=lambda e: (_parse_time(e.start_time), _parse_time(e.end_time))
        )
        lanes: list[int] = []
        assignments: list[tuple[CalendarEvent, int]] = []
        for ev in timed_sorted:
            start = _parse_time(ev.start_time)
            placed = False
            for li, lane_end in enumerate(lanes):
                if start >= lane_end:
                    lanes[li] = _parse_time(ev.end_time)
                    assignments.append((ev, li))
                    placed = True
                    break
            if not placed:
                lanes.append(_parse_time(ev.end_time))
                assignments.append((ev, len(lanes) - 1))

        max_lanes = max(len(lanes), 1)
        plot_w = max(10, self.width() - GUTTER - 8)
        lane_w = plot_w / max_lanes
        for ev, li in assignments:
            start = _parse_time(ev.start_time)
            end = _parse_time(ev.end_time)
            if end <= start:
                end = start + 60
            y = self._all_day_height + (start / 60) * HOUR_HEIGHT
            block_h = ((end - start) / 60) * HOUR_HEIGHT
            if block_h < 18:
                block_h = 18
            x = GUTTER + li * lane_w + 2
            w = lane_w - 4
            self._blocks.append((QRectF(x, y, w, block_h), ev))

        self.setMinimumHeight(self._all_day_height + HOURS * HOUR_HEIGHT + 8)

    @staticmethod
    def _event_color(ev: CalendarEvent) -> QColor:
        return QColor(ev.color or _DEFAULT_COLOR)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor("#1e1e1e"))

        hour_font = painter.font()
        hour_font.setPixelSize(10)
        painter.setFont(hour_font)

        for hour in range(HOURS + 1):
            y = self._all_day_height + hour * HOUR_HEIGHT
            painter.setPen(QPen(QColor("#3a3a3a"), 1))
            painter.drawLine(QPointF(GUTTER, y), QPointF(w, y))
            if hour < HOURS:
                painter.setPen(QPen(QColor("#888888"), 1))
                painter.drawText(
                    QRectF(0, y - 8, GUTTER - 6, 16),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{hour:02d}:00",
                )

        painter.setPen(QPen(QColor("#3a3a3a"), 1))
        painter.drawLine(QPointF(GUTTER, 0), QPointF(GUTTER, h))

        for rect, ev in self._all_day_rects:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._event_color(ev))
            painter.drawRoundedRect(rect, 4, 4)
            painter.setPen(QColor("#111111"))
            painter.drawText(
                rect.adjusted(6, 0, -6, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                ev.title,
            )

        for rect, ev in self._all_day_bars:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._event_color(ev))
            painter.drawRect(rect)

        for rect, ev in self._blocks:
            col = self._event_color(ev)
            selected = ev.id is not None and ev.id == self._selected_id
            border = QColor("#ffffff") if selected else col.darker(130)
            painter.setPen(QPen(border, 2 if selected else 1))
            fill = QColor(col)
            fill.setAlpha(170)
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 3, 3)

            block_font = painter.font()
            block_font.setPixelSize(11)
            painter.setFont(block_font)
            painter.setPen(QColor("#ffffff"))
            time_label = ev.start_time or ""
            if time_label and ev.end_time:
                time_label += f"-{ev.end_time}"
            text = f"{time_label} {ev.title}".strip()
            painter.drawText(
                rect.adjusted(4, 2, -4, -2),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                text,
            )

        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ev = self._event_at(event.position())
            self._selected_id = ev.id if ev else None
            self.selection_changed.emit(ev)
            self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ev = self._event_at(event.position())
            if ev is not None:
                self._selected_id = ev.id
                self.edit_event.emit(ev)
                self.selection_changed.emit(ev)
                self.update()

    def _event_at(self, pos: QPointF) -> Optional[CalendarEvent]:
        for rect, ev in self._blocks:
            if rect.contains(pos):
                return ev
        for rect, ev in self._all_day_rects:
            if rect.contains(pos):
                return ev
        for rect, ev in self._all_day_bars:
            if rect.contains(pos):
                return ev
        return None

    def default_scroll_y(self, hour: int = 8) -> int:
        return self._all_day_height + hour * HOUR_HEIGHT
