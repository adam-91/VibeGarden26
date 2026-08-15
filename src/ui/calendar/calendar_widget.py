from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, Signal, QRectF, QRect
from PySide6.QtGui import (
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QBrush,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import CATEGORY_COLORS
from src.ui.calendar.calendar_model import CalendarModel


class CalendarDayCell(QWidget):
    clicked = Signal(date)

    COL_PAST_BG = QColor("#1c1c1c")
    COL_FUTURE_BG = QColor("#2d2d2d")
    COL_TODAY_BG = QColor("#3a4a3a")
    COL_SELECTED_BG = QColor("#3d5a3d")
    COL_TODAY_BORDER = QColor("#4CAF50")
    COL_PAST_BORDER = QColor("#2a2a2a")
    COL_FUTURE_BORDER = QColor("#404040")
    COL_PAST_TEXT = QColor("#555555")
    COL_FUTURE_TEXT = QColor("#cccccc")
    COL_TODAY_TEXT = QColor("#ffffff")
    COL_MOON = QColor("#FFD700")
    COL_ALLDAY_DOT = QColor("#4CAF50")
    COL_TIMED_DOT = QColor("#FF9800")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._date: Optional[date] = None
        self._today: Optional[date] = None
        self._selected: Optional[date] = None
        self._all_day_count: int = 0
        self._timed_count: int = 0
        self._is_full_moon: bool = False
        self.setMinimumSize(38, 38)

    def set_data(
        self,
        dt: Optional[date],
        today: date,
        selected: date,
        all_day_count: int = 0,
        timed_count: int = 0,
        is_full_moon: bool = False,
    ) -> None:
        self._date = dt
        self._today = today
        self._selected = selected
        self._all_day_count = all_day_count
        self._timed_count = timed_count
        self._is_full_moon = is_full_moon
        self.setToolTip(dt.isoformat() if dt else "")
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._date is not None:
            self.clicked.emit(self._date)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        rect = QRectF(1, 1, w - 2, h - 2)
        radius = 8.0

        if self._date is None:
            painter.fillRect(self.rect(), QColor("#1e1e1e"))
            painter.end()
            return

        is_past = self._date < self._today
        is_today = self._date == self._today
        is_selected = self._date == self._selected

        if is_today:
            bg = self.COL_TODAY_BG
            border = self.COL_TODAY_BORDER
            border_w = 2.5
        elif is_selected:
            bg = self.COL_SELECTED_BG
            border = self.COL_TODAY_BORDER
            border_w = 2.0
        elif is_past:
            bg = self.COL_PAST_BG
            border = self.COL_PAST_BORDER
            border_w = 1.0
        else:
            bg = self.COL_FUTURE_BG
            border = self.COL_FUTURE_BORDER
            border_w = 1.0

        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QBrush(bg))
        painter.strokePath(path, QPen(border, border_w))
        painter.restore()

        painter.save()
        font = painter.font()
        font.setPixelSize(12)
        if is_today:
            font.setBold(True)
        painter.setFont(font)
        text_color = (
            self.COL_TODAY_TEXT if is_today or is_selected
            else self.COL_PAST_TEXT if is_past
            else self.COL_FUTURE_TEXT
        )
        painter.setPen(text_color)
        painter.drawText(
            QRectF(0, 1, w, h * 0.45),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            str(self._date.day),
        )
        painter.restore()

        indicator_y = h * 0.48
        indicator_area_h = h * 0.50
        painter.save()

        if self._is_full_moon:
            f = painter.font()
            f.setPixelSize(max(10, int(h * 0.22)))
            painter.setFont(f)
            painter.drawText(
                QRectF(0, indicator_y, w, indicator_area_h * 0.55),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                "\U0001F315",
            )
            indicator_y += indicator_area_h * 0.50

        if self._all_day_count > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.COL_ALLDAY_DOT)
            dot_r = max(2, int(w * 0.04))
            max_dots = min(self._all_day_count, 4)
            total_dot_w = max_dots * (dot_r * 2.5)
            start_x = (w - total_dot_w) / 2
            for i in range(max_dots):
                cx = start_x + i * (dot_r * 2.5) + dot_r
                painter.drawEllipse(QRectF(cx - dot_r, indicator_y + 2, dot_r * 2, dot_r * 2))
            indicator_y += dot_r * 2 + 4

        if self._timed_count > 0:
            f = painter.font()
            f.setPixelSize(9)
            painter.setFont(f)
            painter.setPen(self.COL_TIMED_DOT)
            painter.drawText(
                QRectF(0, indicator_y, w, indicator_area_h * 0.45),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                f"\u23F0 {self._timed_count}",
            )

        painter.restore()
        painter.end()


class CalendarHeader(QWidget):
    prev_month = Signal()
    next_month = Signal()
    today_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._prev_btn = QPushButton("\u25C0")
        self._prev_btn.setObjectName("calNavBtn")
        self._prev_btn.clicked.connect(self.prev_month.emit)

        self._month_label = QLabel()
        self._month_label.setObjectName("calMonthLabel")
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next_btn = QPushButton("\u25B6")
        self._next_btn.setObjectName("calNavBtn")
        self._next_btn.clicked.connect(self.next_month.emit)

        self._today_btn = QPushButton("Dzi\u015b")
        self._today_btn.setObjectName("calTodayBtn")
        self._today_btn.clicked.connect(self.today_clicked.emit)

        layout.addWidget(self._prev_btn)
        layout.addWidget(self._month_label, 1)
        layout.addWidget(self._next_btn)
        layout.addWidget(self._today_btn)

    def set_month_text(self, text: str) -> None:
        self._month_label.setText(text)


class CalendarGrid(QWidget):
    day_clicked = Signal(date)
    DAY_NAMES = ["Pn", "Wt", "\u015ar", "Cz", "Pt", "Sb", "Nd"]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._model: Optional[CalendarModel] = None
        self._cells: list[CalendarDayCell] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._grid_layout = QVBoxLayout(self)
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(4, 4, 4, 4)

        header_row = QHBoxLayout()
        header_row.setSpacing(2)
        for name in self.DAY_NAMES:
            lbl = QLabel(name)
            lbl.setObjectName("calDayHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(24)
            header_row.addWidget(lbl)
        self._grid_layout.addLayout(header_row)

        self._cell_layouts: list[QHBoxLayout] = []
        for _ in range(CalendarModel.MAX_WEEKS):
            row = QHBoxLayout()
            row.setSpacing(2)
            self._cell_layouts.append(row)
            self._grid_layout.addLayout(row)

        for week in range(CalendarModel.MAX_WEEKS):
            for _ in range(7):
                cell = CalendarDayCell()
                cell.clicked.connect(self.day_clicked.emit)
                self._cells.append(cell)
                self._cell_layouts[week].addWidget(cell)

    def set_model(self, model: CalendarModel) -> None:
        self._model = model

    def refresh(self) -> None:
        if self._model is None:
            return
        days = self._model.get_calendar_days()
        today = self._model.today
        selected = self._model.selected_date

        for i, day in enumerate(days):
            cell = self._cells[i]
            if day is not None:
                events = self._model.get_events_for_date(day)
                all_day_count = sum(1 for e in events if e.is_all_day)
                timed_count = sum(1 for e in events if not e.is_all_day)
                full_moon = self._model.is_full_moon_day(day)
                cell.set_data(day, today, selected, all_day_count, timed_count, full_moon)
            else:
                cell.set_data(None, today, selected)


class DailyEventList(QWidget):
    add_event = Signal(date)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header_layout = QHBoxLayout()
        self._date_label = QLabel("Wybierz dzie\u0144")
        self._date_label.setObjectName("dailyHeader")
        header_layout.addWidget(self._date_label)
        header_layout.addStretch()

        self._add_btn = QPushButton("+ Dodaj")
        self._add_btn.setObjectName("addEventBtn")
        header_layout.addWidget(self._add_btn)
        layout.addLayout(header_layout)

        self._event_list = QListWidget()
        self._event_list.setObjectName("dailyEventList")
        self._event_list.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._event_list)

    def set_date(self, dt: date, events: list) -> None:
        polish_months = [
            "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
            "lipca", "sierpnia", "wrze\u015bnia", "pa\u017adziernika",
            "listopada", "grudnia",
        ]
        weekday_names = [
            "Poniedzia\u0142ek", "Wtorek", "\u015aroda", "Czwartek",
            "Pi\u0105tek", "Sobota", "Niedziela",
        ]
        self._date_label.setText(
            f"{weekday_names[dt.weekday()]}, {dt.day} {polish_months[dt.month - 1]} {dt.year}"
        )
        self._event_list.clear()

        if not events:
            item = QListWidgetItem("Brak wydarze\u0144")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._event_list.addItem(item)
            return

        for event in events:
            time_str = ""
            if event.start_time:
                time_str = f" {event.start_time}"
                if event.end_time:
                    time_str += f" - {event.end_time}"

            repeat_tag = ""
            if event.recurrence_type != "none":
                names = {"daily": "codz.", "weekly": "co tydz.", "monthly": "co mies.", "yearly": "co rok"}
                repeat_tag = f" [{names.get(event.recurrence_type, '')} x{event.recurrence_interval}]"

            type_icon = "\u25CF" if event.is_all_day else "\u23F0"
            text = f"{type_icon}{time_str}  {event.title}{repeat_tag}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, event.id)
            item.setForeground(QColor(event.color))
            self._event_list.addItem(item)

    def connect_add_signal(self, slot) -> None:
        self._add_btn.clicked.connect(lambda: self.add_event.emit(date))
        self._add_btn.clicked.connect(slot)


class CalendarWidget(QWidget):
    day_selected = Signal(date)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._model = CalendarModel()
        self._current_daily_date: Optional[date] = None
        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = CalendarHeader()
        layout.addWidget(self._header)

        self._grid = CalendarGrid()
        self._grid.set_model(self._model)
        layout.addWidget(self._grid)

        self._daily_list = DailyEventList()
        layout.addWidget(self._daily_list)

    def _connect_signals(self) -> None:
        self._header.prev_month.connect(self._on_prev_month)
        self._header.next_month.connect(self._on_next_month)
        self._header.today_clicked.connect(self._on_today)
        self._grid.day_clicked.connect(self._on_day_clicked)

    @property
    def model(self) -> CalendarModel:
        return self._model

    def refresh(self) -> None:
        self._model.load_events()
        self._header.set_month_text(self._month_year_text())
        self._grid.refresh()
        if self._current_daily_date:
            self._show_daily_events(self._current_daily_date)

    def _month_year_text(self) -> str:
        months = [
            "Stycze\u0144", "Luty", "Marzec", "Kwiecie\u0144", "Maj",
            "Czerwiec", "Lipiec", "Sierpie\u0144", "Wrzesie\u0144",
            "Pa\u017adziernik", "Listopad", "Grudzie\u0144",
        ]
        return f"{months[self._model.month - 1]} {self._model.year}"

    def _on_prev_month(self) -> None:
        self._model.go_to_prev_month()
        self.refresh()

    def _on_next_month(self) -> None:
        self._model.go_to_next_month()
        self.refresh()

    def _on_today(self) -> None:
        self._model.go_to_today()
        self.refresh()
        self._show_daily_events(self._model.today)
        self.day_selected.emit(self._model.today)

    def _on_day_clicked(self, dt: date) -> None:
        self._model.selected_date = dt
        self._show_daily_events(dt)
        self.day_selected.emit(dt)

    def _show_daily_events(self, dt: date) -> None:
        self._current_daily_date = dt
        events = self._model.get_events_for_date(dt)
        self._daily_list.set_date(dt, events)
