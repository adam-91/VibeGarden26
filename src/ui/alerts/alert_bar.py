from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QFrame, QWidget

from src.config.settings import ALERT_COLORS, ALERT_TEXT_COLORS
from src.models import WeatherAlert

_SEVERITY_ORDER = {"yellow": 0, "orange": 1, "red": 2}
_SEPARATOR = "   \u2022   "
_TICK_INTERVAL_MS = 30
_TICK_SPEED = 1.2


class AlertBar(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("alertBar")
        self.setFixedHeight(28)
        self._alerts: list[WeatherAlert] = []
        self._scroll_offset = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self.hide()

    def set_alerts(self, alerts: list[WeatherAlert]) -> None:
        self._alerts = list(alerts)
        if not self._alerts:
            self._timer.stop()
            self.hide()
            return
        self._scroll_offset = float(self.width())
        if len(self._alerts) > 1:
            self._timer.start()
        else:
            self._timer.stop()
        self.show()
        self.update()

    def _on_tick(self) -> None:
        self._scroll_offset -= _TICK_SPEED
        text = self._full_text()
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(text)
        if text_width <= 0:
            text_width = self.width() or 1
        if self._scroll_offset <= -text_width:
            self._scroll_offset += text_width
        self.update()

    def _full_text(self) -> str:
        return _SEPARATOR.join(a.text for a in self._alerts)

    def _dominant_category(self) -> str:
        if not self._alerts:
            return "yellow"
        return max(self._alerts, key=lambda a: _SEVERITY_ORDER.get(a.category, 0)).category

    def paintEvent(self, event) -> None:
        if not self._alerts:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        category = self._dominant_category()
        background = QColor(ALERT_COLORS.get(category, "#FFC107"))
        text_color = QColor(ALERT_TEXT_COLORS.get(category, "#1a1a1a"))

        painter.fillRect(self.rect(), background)

        font = self.font()
        font.setBold(True)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(text_color)

        metrics = QFontMetrics(font)
        rect = self.rect().adjusted(10, 0, -10, 0)

        if len(self._alerts) == 1:
            elided = metrics.elidedText(
                self._alerts[0].text, Qt.TextElideMode.ElideRight, rect.width()
            )
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided
            )
            painter.end()
            return

        text = self._full_text()
        text_width = metrics.horizontalAdvance(text)
        if text_width <= 0:
            painter.end()
            return

        x = self._scroll_offset
        y = (self.height() + metrics.ascent() - metrics.descent()) / 2

        painter.setClipRect(self.rect())
        painter.drawText(int(x), int(y), text)
        painter.drawText(int(x + text_width), int(y), text)
        painter.end()
