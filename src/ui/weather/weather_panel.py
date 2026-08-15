from __future__ import annotations

from math import cos, sin, radians
from typing import Optional

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models import WeatherData

WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def _degrees_to_direction(deg: float) -> str:
    idx = int(round(deg / 22.5)) % 16
    return WIND_DIRECTIONS[idx]


def _format_hour(label: str) -> str:
    if not label:
        return ""
    return label.split("T")[-1][:5] if "T" in label else label[:5]


class _ChartWidget(QWidget):
    def __init__(
        self,
        chart_type: str = "line",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._chart_type = chart_type
        self._times: list[str] = []
        self._values: list[float] = []
        self._label = ""
        self._unit = ""
        self._color = QColor(76, 175, 80)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def set_data(
        self,
        times: list[str],
        values: list[float],
        label: str = "",
        unit: str = "",
    ) -> None:
        self._times = times
        self._values = values
        self._label = label
        self._unit = unit
        self.update()

    def paintEvent(self, event) -> None:
        if not self._times or not self._values:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor("#2a2a2a")
        painter.fillRect(self.rect(), bg)

        margin_left = 38
        margin_right = 12
        margin_top = 24
        margin_bottom = 30

        plot_w = self.width() - margin_left - margin_right
        plot_h = self.height() - margin_top - margin_bottom

        if plot_w <= 0 or plot_h <= 0:
            painter.end()
            return

        n = len(self._values)
        vals = self._values
        vmin = min(vals) if vals else 0.0
        vmax = max(vals) if vals else 1.0
        if vmax == vmin:
            vmax = vmin + 1.0

        def tx(i: int) -> float:
            return margin_left + (i / (n - 1)) * plot_w if n > 1 else margin_left + plot_w / 2

        def ty(v: float) -> float:
            ratio = (v - vmin) / (vmax - vmin)
            return margin_top + plot_h - ratio * plot_h

        painter.setPen(QPen(QColor("#666"), 1))
        painter.drawLine(
            QPointF(margin_left, margin_top),
            QPointF(margin_left, margin_top + plot_h),
        )
        painter.drawLine(
            QPointF(margin_left, margin_top + plot_h),
            QPointF(margin_left + plot_w, margin_top + plot_h),
        )

        painter.setPen(QPen(QColor("#555"), 1, Qt.PenStyle.DotLine))
        for fraction in [0.25, 0.5, 0.75]:
            y = margin_top + plot_h - fraction * plot_h
            painter.drawLine(
                QPointF(margin_left, y),
                QPointF(margin_left + plot_w, y),
            )

        painter.setPen(QPen(QColor("#888"), 1))
        label_top = vmax
        label_bot = vmin
        painter.setFont(painter.font())
        f = painter.font()
        f.setPixelSize(9)
        painter.setFont(f)
        painter.drawText(
            QRectF(0, margin_top - 10, margin_left - 4, 20),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            f"{label_top:.0f}",
        )
        painter.drawText(
            QRectF(0, margin_top + plot_h - 10, margin_left - 4, 20),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            f"{label_bot:.0f}",
        )

        step = max(1, n // 6)
        for i in range(0, n, step):
            x = tx(i)
            h = _format_hour(self._times[i])
            painter.setPen(QPen(QColor("#888"), 1))
            painter.drawText(
                QRectF(x - 20, margin_top + plot_h + 2, 40, 14),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                h,
            )

        if self._chart_type == "line":
            self._draw_line(painter, tx, ty)
        elif self._chart_type == "bar":
            self._draw_bars(painter, tx, ty)

        if self._label:
            f2 = painter.font()
            f2.setPixelSize(10)
            painter.setFont(f2)
            painter.setPen(QPen(QColor("#4CAF50"), 1))
            painter.drawText(
                QRectF(margin_left, 2, plot_w, 20),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                self._label + (f" [{self._unit}]" if self._unit else ""),
            )

        painter.end()

    def _draw_line(self, painter: QPainter, tx, ty) -> None:
        color = QColor(76, 175, 80)
        painter.setPen(QPen(color, 2))
        path = QPainterPath()
        path.moveTo(tx(0), ty(self._values[0]))
        for i in range(1, len(self._values)):
            path.lineTo(tx(i), ty(self._values[i]))
        painter.drawPath(path)

        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(len(self._values)):
            painter.drawEllipse(QPointF(tx(i), ty(self._values[i])), 3, 3)

    def _draw_bars(self, painter: QPainter, tx, ty) -> None:
        n = len(self._values)
        bar_w = max(3.0, (self.width() - 50) / n * 0.7)
        baseline = ty(0)
        color = QColor(76, 175, 80)
        color_transparent = QColor(76, 175, 80, 100)
        painter.setPen(QPen(color, 1))
        for i in range(n):
            x = tx(i) - bar_w / 2
            v = self._values[i]
            top_y = ty(v)
            rect = QRectF(x, top_y, bar_w, baseline - top_y)
            painter.fillRect(rect, color_transparent)
            painter.drawRect(rect)

        f = painter.font()
        f.setPixelSize(9)
        painter.setFont(f)
        for i in range(n):
            v = self._values[i]
            if v > 0:
                painter.setPen(QPen(QColor("#ccc"), 1))
                painter.drawText(
                    QRectF(tx(i) - 15, ty(v) - 16, 30, 14),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                    f"{v:.1f}",
                )


class WeatherPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("weatherPanel")
        self._page_index = 0
        self._weather: Optional[WeatherData] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(4)

        title = QLabel("Pogoda")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()

        self._page_indicator = QLabel("1/3")
        self._page_indicator.setObjectName("pageIndicator")
        header.addWidget(self._page_indicator)

        self._prev_btn = QPushButton("◀")
        self._prev_btn.setObjectName("weatherNavBtn")
        self._prev_btn.setFixedSize(24, 24)
        self._prev_btn.clicked.connect(self._prev_page)
        header.addWidget(self._prev_btn)

        self._next_btn = QPushButton("▶")
        self._next_btn.setObjectName("weatherNavBtn")
        self._next_btn.setFixedSize(24, 24)
        self._next_btn.clicked.connect(self._next_page)
        header.addWidget(self._next_btn)

        layout.addLayout(header)

        self._stack = QStackedWidget()
        self._stack.setObjectName("weatherStack")

        self._stack.addWidget(self._build_page1())
        self._stack.addWidget(self._build_page2())
        self._stack.addWidget(self._build_page3())

        layout.addWidget(self._stack, 1)

    def _build_page1(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        self._location_label = QLabel("--")
        self._location_label.setObjectName("weatherLocation")
        self._location_label.setWordWrap(True)
        layout.addWidget(self._location_label)

        self._temp_label = QLabel("--°C")
        self._temp_label.setObjectName("weatherTemp")
        self._temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._temp_label)

        self._desc_label = QLabel("--")
        self._desc_label.setObjectName("weatherDesc")
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

        details = QFrame()
        details.setObjectName("weatherDetails")
        dl = QVBoxLayout(details)
        dl.setSpacing(4)

        self._humidity_label = self._make_detail()
        dl.addWidget(self._humidity_label)
        self._pressure_label = self._make_detail()
        dl.addWidget(self._pressure_label)
        self._uv_label = self._make_detail()
        dl.addWidget(self._uv_label)
        self._sunrise_label = self._make_detail()
        dl.addWidget(self._sunrise_label)
        self._sunset_label = self._make_detail()
        dl.addWidget(self._sunset_label)

        layout.addWidget(details)
        return page

    def _build_page2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        self._wind_speed_label = QLabel("Prędkość: -- km/h")
        self._wind_speed_label.setObjectName("weatherWindBig")
        self._wind_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._wind_speed_label)

        self._wind_dir_label = QLabel("Kierunek: --")
        self._wind_dir_label.setObjectName("weatherWindBig")
        self._wind_dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._wind_dir_label)

        self._wind_gusts_label = QLabel("Porywy: -- km/h")
        self._wind_gusts_label.setObjectName("weatherWindBig")
        self._wind_gusts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._wind_gusts_label)

        self._wind_chart = _ChartWidget(chart_type="line")
        layout.addWidget(self._wind_chart, 1)

        return page

    def _build_page3(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        info = QWidget()
        il = QVBoxLayout(info)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(4)

        self._p3_location_label = QLabel("--")
        self._p3_location_label.setObjectName("weatherLocation")
        self._p3_location_label.setWordWrap(True)
        il.addWidget(self._p3_location_label)

        self._p3_temp_label = QLabel("--°C")
        self._p3_temp_label.setObjectName("weatherTemp")
        self._p3_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(self._p3_temp_label)

        self._p3_desc_label = QLabel("--")
        self._p3_desc_label.setObjectName("weatherDesc")
        self._p3_desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._p3_desc_label.setWordWrap(True)
        il.addWidget(self._p3_desc_label)

        layout.addWidget(info)

        self._precip_chart = _ChartWidget(chart_type="bar")
        layout.addWidget(self._precip_chart, 1)

        return page

    @staticmethod
    def _make_detail() -> QLabel:
        lbl = QLabel("--")
        lbl.setObjectName("weatherDetail")
        return lbl

    def _prev_page(self) -> None:
        self._page_index = (self._page_index - 1) % 3
        self._switch_page()

    def _next_page(self) -> None:
        self._page_index = (self._page_index + 1) % 3
        self._switch_page()

    def _switch_page(self) -> None:
        self._stack.setCurrentIndex(self._page_index)
        self._page_indicator.setText(f"{self._page_index + 1}/3")
        self._prev_btn.setEnabled(True)
        self._next_btn.setEnabled(True)

    def update_weather(self, weather: Optional[WeatherData]) -> None:
        if weather is None:
            self.clear()
            return
        self._weather = weather
        name = weather.location_name or "Wybrana lokalizacja"

        self._location_label.setText(name)
        self._temp_label.setText(f"{weather.temperature:.1f}°C")
        self._desc_label.setText(weather.weather_description)
        self._humidity_label.setText(f"Wilgotność: {weather.humidity}%")
        self._pressure_label.setText(f"Ciśnienie: {weather.pressure:.0f} hPa")
        self._uv_label.setText(f"UV Index: {weather.uv_index:.1f}")
        if weather.sunrise:
            sr = weather.sunrise.split("T")[-1] if "T" in weather.sunrise else weather.sunrise
            self._sunrise_label.setText(f"Wschód: {sr}")
        if weather.sunset:
            ss = weather.sunset.split("T")[-1] if "T" in weather.sunset else weather.sunset
            self._sunset_label.setText(f"Zachód: {ss}")

        direction = _degrees_to_direction(weather.wind_direction)
        self._wind_speed_label.setText(f"Prędkość: {weather.wind_speed:.1f} km/h")
        self._wind_dir_label.setText(f"Kierunek: {direction} ({weather.wind_direction:.0f}°)")
        self._wind_gusts_label.setText(f"Porywy: {weather.wind_gusts:.1f} km/h")

        if weather.hourly_times:
            self._wind_chart.set_data(
                weather.hourly_times,
                weather.hourly_wind_speeds,
                label="Prędkość wiatru 24h",
                unit="km/h",
            )
            self._precip_chart.set_data(
                weather.hourly_times,
                weather.hourly_precipitation,
                label="Opady 24h",
                unit="mm",
            )

        self._p3_location_label.setText(name)
        self._p3_temp_label.setText(f"{weather.temperature:.1f}°C")
        self._p3_desc_label.setText(weather.weather_description)

    def clear(self) -> None:
        for lbl in [
            self._location_label, self._temp_label, self._desc_label,
            self._humidity_label, self._pressure_label, self._uv_label,
            self._sunrise_label, self._sunset_label,
            self._wind_speed_label, self._wind_dir_label, self._wind_gusts_label,
            self._p3_location_label, self._p3_temp_label, self._p3_desc_label,
        ]:
            if lbl:
                lbl.setText("--")
        self._temp_label.setText("--°C")
        self._p3_temp_label.setText("--°C")
