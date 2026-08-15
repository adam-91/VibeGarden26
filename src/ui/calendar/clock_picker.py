from __future__ import annotations

import re
from math import atan2, cos, degrees, radians, sin
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QRegularExpression, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _SelectAllLineEdit(QLineEdit):
    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)


class ClockDial(QWidget):
    hour_selected = Signal(int)
    minute_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mode = "hour"
        self._hour = 0
        self._minute = 0
        self.setMinimumSize(240, 240)

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.update()

    def set_hour(self, hour: int) -> None:
        self._hour = hour
        self.update()

    def set_minute(self, minute: int) -> None:
        self._minute = minute
        self.update()

    def _geometry(self) -> tuple[float, float, float]:
        w = self.width()
        h = self.height()
        size = min(w, h)
        return w / 2, h / 2, size / 2 - 14

    @staticmethod
    def _ring_point(cx: float, cy: float, r: float, value: int, total: int = 12):
        angle = radians((value % total) * (360.0 / total))
        return cx + r * sin(angle), cy - r * cos(angle)

    def _draw_number(self, painter: QPainter, x: float, y: float, text: str, selected: bool) -> None:
        if selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#4CAF50"))
            painter.drawEllipse(QPointF(x, y), 12, 12)
            painter.setPen(QColor("#111111"))
        else:
            painter.setPen(QColor("#dddddd"))
        painter.drawText(
            QRectF(x - 12, y - 9, 24, 18),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = self._geometry()

        painter.setPen(QPen(QColor("#444444"), 1))
        painter.setBrush(QColor("#2a2a2a"))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        inner_r = r * 0.55
        outer_r = r * 0.85
        font = painter.font()
        font.setPixelSize(11)
        painter.setFont(font)

        if self._mode == "hour":
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

            for v in range(1, 13):
                x, y = self._ring_point(cx, cy, inner_r, v)
                selected = 1 <= self._hour <= 12 and self._hour == v
                self._draw_number(painter, x, y, str(v), selected)

            for v in range(13, 25):
                x, y = self._ring_point(cx, cy, outer_r, v % 12)
                selected = (self._hour == 0 and v == 24) or (
                    13 <= self._hour <= 23 and self._hour == v
                )
                self._draw_number(painter, x, y, str(v), selected)
        else:
            for m in range(60):
                x1, y1 = self._ring_point(cx, cy, r * 0.95, m, 60)
                x0, y0 = self._ring_point(cx, cy, r * 0.88, m, 60)
                if m % 5 == 0:
                    painter.setPen(QPen(QColor("#bbbbbb"), 2))
                else:
                    painter.setPen(QPen(QColor("#555555"), 1))
                painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))

            for m in range(0, 60, 5):
                x, y = self._ring_point(cx, cy, r * 0.70, m, 60)
                self._draw_number(painter, x, y, f"{m:02d}", m == self._minute)

        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        cx, cy, r = self._geometry()
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > r:
            return
        angle = degrees(atan2(dx, -dy)) % 360

        if self._mode == "hour":
            boundary = (r * 0.55 + r * 0.85) / 2
            inner = dist <= boundary
            idx = round(angle / 30) % 12
            if inner:
                hour = 12 if idx == 0 else idx
            else:
                display = 24 if idx == 0 else idx + 12
                hour = 0 if display == 24 else display
            self.set_hour(hour)
            self.hour_selected.emit(hour)
        else:
            minute = round(angle / 6) % 60
            self.set_minute(minute)
            self.minute_selected.emit(minute)


class ClockPickerPopup(QWidget):
    time_chosen = Signal(int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._hour = 0
        self._minute = 0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "background-color: #252525;"
            "border: 1px solid #444444;"
            "border-radius: 8px;"
            "QLabel { color: #e0e0e0; }"
            "QPushButton {"
            " background-color: #4a4a4a;"
            " color: #e0e0e0;"
            " border: 1px solid #5a5a5a;"
            " border-radius: 6px;"
            " padding: 6px 14px;"
            "}"
            "QPushButton:hover { background-color: #5a5a5a; }"
            "QPushButton:checked { background-color: #4CAF50; color: #111111; }"
        )
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._time_label = QLabel("00:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        layout.addWidget(self._time_label)

        mode_row = QHBoxLayout()
        self._hour_btn = QPushButton("Godzina")
        self._hour_btn.setCheckable(True)
        self._hour_btn.setChecked(True)
        self._hour_btn.clicked.connect(lambda: self._set_mode("hour"))
        self._minute_btn = QPushButton("Minuta")
        self._minute_btn.setCheckable(True)
        self._minute_btn.clicked.connect(lambda: self._set_mode("minute"))
        mode_row.addWidget(self._hour_btn)
        mode_row.addWidget(self._minute_btn)
        layout.addLayout(mode_row)

        self._dial = ClockDial()
        self._dial.hour_selected.connect(self._on_hour)
        self._dial.minute_selected.connect(self._on_minute)
        layout.addWidget(self._dial)

        buttons = QHBoxLayout()
        cancel = QPushButton("Anuluj")
        cancel.clicked.connect(self.close)
        ok = QPushButton("OK")
        ok.clicked.connect(self._on_ok)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addLayout(buttons)

    def set_time(self, hour: int, minute: int) -> None:
        self._hour = hour
        self._minute = minute
        self._dial.set_hour(hour)
        self._dial.set_minute(minute)
        self._update_label()

    def _set_mode(self, mode: str) -> None:
        self._dial.set_mode(mode)
        self._hour_btn.setChecked(mode == "hour")
        self._minute_btn.setChecked(mode == "minute")

    def _on_hour(self, hour: int) -> None:
        self._hour = hour
        self._update_label()
        self._set_mode("minute")

    def _on_minute(self, minute: int) -> None:
        self._minute = minute
        self._update_label()

    def _update_label(self) -> None:
        self._time_label.setText(f"{self._hour:02d}:{self._minute:02d}")

    def _on_ok(self) -> None:
        self.time_chosen.emit(self._hour, self._minute)
        self.close()


class ClockTimeField(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._hour = 0
        self._minute = 0
        self._popup: Optional[ClockPickerPopup] = None
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._edit = _SelectAllLineEdit()
        self._edit.setMaxLength(5)
        self._edit.setPlaceholderText("HH:MM")
        self._edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit.setText("00:00")
        self._edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"\d{0,2}:?\d{0,2}")
            )
        )
        self._edit.editingFinished.connect(self._on_editing_finished)
        layout.addWidget(self._edit, 1)

        self._btn = QPushButton("\u23F1")
        self._btn.setObjectName("clockBtn")
        self._btn.setFixedWidth(34)
        self._btn.setToolTip("Wybierz z tarczy")
        self._btn.clicked.connect(self._open_popup)
        layout.addWidget(self._btn)

    def set_time(self, hour: int, minute: int) -> None:
        self._hour = hour
        self._minute = minute
        self._edit.setText(f"{hour:02d}:{minute:02d}")

    def time_parts(self) -> tuple[int, int]:
        return self._hour, self._minute

    def _on_editing_finished(self) -> None:
        text = self._edit.text()
        m = re.match(r"^(\d{2}):(\d{2})$", text)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                self._hour = hour
                self._minute = minute
                return
        self._edit.setText(f"{self._hour:02d}:{self._minute:02d}")

    def _open_popup(self) -> None:
        self._popup = ClockPickerPopup()
        self._popup.set_time(self._hour, self._minute)
        self._popup.time_chosen.connect(self.set_time)
        pos = self._btn.mapToGlobal(QPoint(0, self._btn.height()))
        self._popup.move(pos)
        self._popup.show()
