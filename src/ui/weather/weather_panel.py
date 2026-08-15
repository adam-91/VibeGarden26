from __future__ import annotations

from datetime import datetime
from math import cos, pi, sin
from typing import Optional

import pytz

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
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


def _wind_color(value: float) -> QColor:
    if value > 80:
        return QColor("#6A1B9A")
    if value > 45:
        return QColor("#F44336")
    if value > 30:
        return QColor("#FF9800")
    if value > 20:
        return QColor("#FFC107")
    return QColor("#4CAF50")


def _kmh_to_ms(value: float) -> float:
    return value / 3.6


def _temp_color(temp: float) -> QColor:
    if temp >= 38:
        return QColor("#800000")
    if temp >= 30:
        return QColor("#F44336")
    if temp >= 22:
        return QColor("#FF9800")
    if temp >= 18:
        return QColor("#FFC107")
    if temp >= 10:
        return QColor("#4CAF50")
    if temp >= 0:
        return QColor("#81D4FA")
    if temp >= -10:
        return QColor("#2196F3")
    if temp >= -20:
        return QColor("#1A237E")
    return QColor("#6A1B9A")


def _weather_emoji(code: int) -> str:
    if code in (0, 1):
        return "\u2600"
    if code == 2:
        return "\u26C5"
    if code == 3:
        return "\u2601"
    if code in (45, 48):
        return "\u2601"
    if 51 <= code <= 57:
        return "\u2614"
    if 61 <= code <= 67:
        return "\u2614"
    if 71 <= code <= 77:
        return "\u2744"
    if 80 <= code <= 82:
        return "\u2614"
    if 85 <= code <= 86:
        return "\u2744"
    if code >= 95:
        return "\u2614"
    return "\u2600"


def _is_fog(code: int) -> bool:
    return code in (45, 48)


def _is_storm(code: int) -> bool:
    return code in (95, 96, 99)


def _hourly_icon(code: int, is_night: bool) -> str:
    if is_night:
        if code in (0, 1):
            return "\u263E"
        if code == 2:
            return "\u2601"
    return _weather_emoji(code)


def _parse_hhmm(s: str) -> Optional[int]:
    if not s:
        return None
    t = s.split("T")[-1] if "T" in s else s
    try:
        h, m = t.split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, IndexError):
        return None


def _now_minutes(timezone: str) -> int:
    try:
        now = datetime.now(pytz.timezone(timezone))
    except Exception:
        now = datetime.now()
    return now.hour * 60 + now.minute


class _WindHourlyView(QWidget):
    COL_W = 44
    STRIP_H = 58

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._times: list[str] = []
        self._speeds: list[float] = []
        self._gusts: list[float] = []
        self._directions: list[float] = []
        self.setMinimumWidth(self.COL_W)

    def set_data(
        self,
        times: list[str],
        speeds: list[float],
        gusts: list[float],
        directions: list[float],
    ) -> None:
        self._times = list(times)
        self._speeds = list(speeds)
        self._gusts = list(gusts)
        self._directions = list(directions)
        self.setMinimumWidth(max(len(self._times), 1) * self.COL_W)
        self.update()

    def clear(self) -> None:
        self._times = []
        self._speeds = []
        self._gusts = []
        self._directions = []
        self.setMinimumWidth(self.COL_W)
        self.update()

    def paintEvent(self, event) -> None:
        if not self._times:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#252525"))

        n = len(self._times)
        speeds_ms = [
            _kmh_to_ms(self._speeds[i]) if i < len(self._speeds) else 0.0
            for i in range(n)
        ]
        gusts_ms = [
            _kmh_to_ms(self._gusts[i]) if i < len(self._gusts) else 0.0
            for i in range(n)
        ]
        all_vals = speeds_ms + gusts_ms
        max_ms = max(all_vals) if all_vals else 1.0
        if max_ms <= 0:
            max_ms = 1.0

        chart_h = max(40, self.height() - self.STRIP_H)
        top = 14.0
        bottom = chart_h - 4.0

        def y_for(v: float) -> float:
            ratio = v / max_ms
            return bottom - ratio * (bottom - top)

        font = painter.font()
        font.setPixelSize(9)
        painter.setFont(font)

        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(QPointF(0, bottom), QPointF(self.width(), bottom))

        for i in range(n):
            cx = i * self.COL_W + self.COL_W / 2
            speed = speeds_ms[i]
            gust = gusts_ms[i]
            direction = self._directions[i] if i < len(self._directions) else 0.0

            sy = y_for(speed)
            gy = y_for(gust)

            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(_wind_color(speed))
            painter.drawEllipse(QPointF(cx, sy), 4, 4)
            painter.setPen(QColor("#e0e0e0"))
            painter.drawText(
                QRectF(cx - self.COL_W / 2, sy + 5, self.COL_W, 12),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                f"{speed:.0f}",
            )

            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(_wind_color(gust))
            painter.drawEllipse(QPointF(cx, gy), 4, 4)
            painter.setPen(QColor("#bbbbbb"))
            painter.drawText(
                QRectF(cx - self.COL_W / 2, gy - 17, self.COL_W, 12),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                f"{gust:.0f}",
            )

            arrow_y = chart_h + 14
            painter.save()
            painter.translate(cx, arrow_y)
            painter.rotate(direction)
            painter.setPen(QPen(QColor("#e0e0e0"), 1.5))
            painter.setBrush(QColor("#e0e0e0"))
            painter.drawLine(QPointF(0, 5), QPointF(0, -4))
            painter.drawPolygon(
                QPolygonF([QPointF(0, -9), QPointF(-4, -2), QPointF(4, -2)])
            )
            painter.restore()

            painter.setPen(QColor("#cccccc"))
            painter.drawText(
                QRectF(cx - self.COL_W / 2, chart_h + 28, self.COL_W, 12),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                _degrees_to_direction(direction),
            )

            if i % 3 == 0:
                painter.setPen(QColor("#888888"))
                painter.drawText(
                    QRectF(cx - self.COL_W / 2, chart_h + 42, self.COL_W, 12),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    _format_hour(self._times[i])[:2],
                )

        painter.end()


class _HourlyWeatherView(QWidget):
    COL_W = 30

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._times: list[str] = []
        self._temps: list[float] = []
        self._codes: list[int] = []
        self._precip: list[float] = []
        self._sunrise = ""
        self._sunset = ""
        self.setMinimumWidth(self.COL_W)

    def set_data(
        self,
        times: list[str],
        temps: list[float],
        codes: list[int],
        precip: list[float],
        sunrise: str = "",
        sunset: str = "",
    ) -> None:
        self._times = list(times)
        self._temps = list(temps)
        self._codes = list(codes)
        self._precip = list(precip)
        self._sunrise = sunrise
        self._sunset = sunset
        self.setMinimumWidth(max(len(self._times), 1) * self.COL_W)
        self.update()

    def clear(self) -> None:
        self._times = []
        self._temps = []
        self._codes = []
        self._precip = []
        self._sunrise = ""
        self._sunset = ""
        self.setMinimumWidth(self.COL_W)
        self.update()

    def _is_night(self, minutes: Optional[int]) -> bool:
        if minutes is None:
            return False
        sr = _parse_hhmm(self._sunrise)
        ss = _parse_hhmm(self._sunset)
        if sr is None or ss is None or ss <= sr:
            return False
        return minutes < sr or minutes > ss

    def paintEvent(self, event) -> None:
        if not self._times:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#252525"))

        n = len(self._times)
        temps = [self._temps[i] if i < len(self._temps) else 0.0 for i in range(n)]
        precip = [self._precip[i] if i < len(self._precip) else 0.0 for i in range(n)]

        tmin = min(temps)
        tmax = max(temps)
        if tmax - tmin < 1.0:
            tmax = tmin + 1.0
        pmax = max(precip) if precip else 0.0
        if pmax <= 0:
            pmax = 1.0

        h = self.height()
        header_h = 30.0
        hour_label_h = 14.0
        base_bottom = h - hour_label_h
        divider = header_h + (base_bottom - header_h) * 0.62

        temp_top = header_h + 6.0
        temp_bottom = divider - 6.0
        precip_top = divider + 2.0
        precip_bottom = base_bottom - 2.0

        def y_temp(v: float) -> float:
            return temp_bottom - ((v - tmin) / (tmax - tmin)) * (temp_bottom - temp_top)

        def bar_h(v: float) -> float:
            return (v / pmax) * (precip_bottom - precip_top)

        icon_font = painter.font()
        icon_font.setPixelSize(13)
        temp_font = painter.font()
        temp_font.setPixelSize(9)
        temp_font.setBold(True)
        small_font = painter.font()
        small_font.setPixelSize(9)

        painter.setPen(QPen(QColor("#3a3a3a"), 1))
        painter.drawLine(QPointF(0, divider), QPointF(self.width(), divider))
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(QPointF(0, precip_bottom), QPointF(self.width(), precip_bottom))

        for i in range(n):
            cx = i * self.COL_W + self.COL_W / 2
            v = temps[i]
            p = precip[i]
            yy = y_temp(v)

            code = self._codes[i] if i < len(self._codes) else 0
            minutes = _parse_hhmm(self._times[i])
            is_night = self._is_night(minutes)
            icon = _hourly_icon(code, is_night)

            painter.setFont(icon_font)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                QRectF(cx - self.COL_W / 2, 0, self.COL_W, 14),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                icon,
            )

            painter.setFont(temp_font)
            painter.setPen(_temp_color(v))
            painter.drawText(
                QRectF(cx - self.COL_W / 2, 14, self.COL_W, 14),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                f"{v:.0f}\u00B0",
            )

            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(_temp_color(v))
            painter.drawEllipse(QPointF(cx, yy), 4, 4)

            bh = bar_h(p)
            if bh > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#2196F3"))
                bar_w = max(3.0, self.COL_W - 10)
                painter.drawRect(QRectF(cx - bar_w / 2, precip_bottom - bh, bar_w, bh))

            if i % 3 == 0:
                painter.setFont(small_font)
                painter.setPen(QColor("#888888"))
                painter.drawText(
                    QRectF(cx - self.COL_W / 2, h - 14, self.COL_W, 12),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    _format_hour(self._times[i])[:2],
                )

        painter.end()


class _PrecipHourlyView(QWidget):
    COL_W = 26

    RAIN = QColor("#2196F3")
    SNOW = QColor("#FFFFFF")
    HAIL = QColor("#6A1B9A")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._times: list[str] = []
        self._precip: list[float] = []
        self._rain: list[float] = []
        self._snow: list[float] = []
        self._hail: list[float] = []
        self._codes: list[int] = []
        self.setMinimumWidth(self.COL_W)

    def set_data(
        self,
        times: list[str],
        precip: list[float],
        rain: list[float],
        snow: list[float],
        hail: list[float],
        codes: list[int],
    ) -> None:
        self._times = list(times)
        self._precip = list(precip)
        self._rain = list(rain)
        self._snow = list(snow)
        self._hail = list(hail)
        self._codes = list(codes)
        self.setMinimumWidth(max(len(self._times), 1) * self.COL_W)
        self.update()

    def clear(self) -> None:
        self._times = []
        self._precip = []
        self._rain = []
        self._snow = []
        self._hail = []
        self._codes = []
        self.setMinimumWidth(self.COL_W)
        self.update()

    def paintEvent(self, event) -> None:
        if not self._times:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#252525"))

        n = len(self._times)
        rain = [self._rain[i] if i < len(self._rain) else 0.0 for i in range(n)]
        snow = [self._snow[i] if i < len(self._snow) else 0.0 for i in range(n)]
        hail = [self._hail[i] if i < len(self._hail) else 0.0 for i in range(n)]

        if not any(rain) and not any(snow) and not any(hail):
            rain = [self._precip[i] if i < len(self._precip) else 0.0 for i in range(n)]

        totals = [rain[i] + snow[i] + hail[i] for i in range(n)]
        max_tot = max(totals) if totals else 1.0
        if max_tot <= 0:
            max_tot = 1.0

        top = 18.0
        chart_h = max(34, self.height() - 18)
        bottom = chart_h - 2.0
        span = bottom - top

        def h_for(v: float) -> float:
            return (v / max_tot) * span

        font = painter.font()
        font.setPixelSize(9)
        painter.setFont(font)

        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(QPointF(0, bottom), QPointF(self.width(), bottom))

        for i in range(n):
            cx = i * self.COL_W + self.COL_W / 2
            bar_w = max(3.0, self.COL_W - 8)
            y = bottom
            for val, color in (
                (rain[i], self.RAIN),
                (snow[i], self.SNOW),
                (hail[i], self.HAIL),
            ):
                bh = h_for(val)
                if bh > 0:
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                    painter.setBrush(color)
                    painter.drawRect(QRectF(cx - bar_w / 2, y - bh, bar_w, bh))
                    y -= bh

            code = self._codes[i] if i < len(self._codes) else 0
            if code in (95, 96, 99):
                painter.setPen(QColor("#FFD54F"))
                painter.drawText(
                    QRectF(cx - bar_w / 2, 0, bar_w, 14),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    "\u26A1",
                )

            if i % 3 == 0:
                painter.setPen(QColor("#888888"))
                painter.drawText(
                    QRectF(cx - self.COL_W / 2, chart_h + 2, self.COL_W, 12),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    _format_hour(self._times[i])[:2],
                )

        painter.end()


class _SunPositionWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._sunrise = ""
        self._sunset = ""
        self._timezone = ""
        self.setMinimumHeight(120)

    def set_data(self, sunrise: str, sunset: str, timezone: str) -> None:
        self._sunrise = sunrise
        self._sunset = sunset
        self._timezone = timezone
        self.update()

    def clear(self) -> None:
        self._sunrise = ""
        self._sunset = ""
        self._timezone = ""
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#252525"))

        w = self.width()
        h = self.height()
        cx = w / 2
        horizon_y = h - 22
        r = max(10.0, min((w - 48) / 2, horizon_y - 8))

        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawLine(QPointF(8, horizon_y), QPointF(w - 8, horizon_y))

        painter.setPen(QPen(QColor("#cccccc"), 2.5))
        arc = []
        for k in range(61):
            t = pi - (k / 60) * pi
            arc.append(QPointF(cx + r * cos(t), horizon_y - r * sin(t)))
        painter.drawPolyline(arc)

        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)

        sr = _parse_hhmm(self._sunrise)
        ss = _parse_hhmm(self._sunset)
        if sr is not None:
            painter.setPen(QColor("#cccccc"))
            painter.drawText(
                QRectF(cx - r - 16, horizon_y + 2, 32, 12),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                _format_hour(self._sunrise),
            )
        if ss is not None:
            painter.setPen(QColor("#cccccc"))
            painter.drawText(
                QRectF(cx + r - 16, horizon_y + 2, 32, 12),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                _format_hour(self._sunset),
            )

        if sr is None or ss is None or ss <= sr:
            painter.end()
            return

        now_min = _now_minutes(self._timezone)
        if sr <= now_min <= ss:
            f = (now_min - sr) / (ss - sr)
            angle = pi * (1 - f)
            sx = cx + r * cos(angle)
            sy = horizon_y - r * sin(angle)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#FFD54F"))
            painter.drawEllipse(QPointF(sx, sy), 9, 9)

        painter.end()


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

        self._page_indicator = QLabel("1/4")
        self._page_indicator.setObjectName("pageIndicator")
        header.addWidget(self._page_indicator)

        self._prev_btn = QPushButton("\u25C0")
        self._prev_btn.setObjectName("weatherNavBtn")
        self._prev_btn.setFixedSize(24, 24)
        self._prev_btn.clicked.connect(self._prev_page)
        header.addWidget(self._prev_btn)

        self._next_btn = QPushButton("\u25B6")
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
        self._stack.addWidget(self._build_page4())

        layout.addWidget(self._stack, 1)

    def _build_icon_row(self):
        row = QHBoxLayout()
        row.setSpacing(6)
        icon = QLabel("")
        icon.setObjectName("weatherIconBig")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fog = QLabel("")
        fog.setObjectName("weatherBadge")
        storm = QLabel("")
        storm.setObjectName("weatherBadge")
        row.addStretch()
        row.addWidget(icon)
        row.addWidget(fog)
        row.addWidget(storm)
        row.addStretch()
        return row, icon, fog, storm

    def _build_page1(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        self._location_label = QLabel("--")
        self._location_label.setObjectName("weatherLocation")
        self._location_label.setWordWrap(True)
        layout.addWidget(self._location_label)

        icon_row, self._p1_icon, self._p1_fog, self._p1_storm = self._build_icon_row()
        layout.addLayout(icon_row)

        self._temp_label = QLabel("--\u00B0C")
        self._temp_label.setObjectName("weatherTemp")
        self._temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._temp_label)

        self._minmax_label = QLabel("-- / --")
        self._minmax_label.setObjectName("weatherMinMax")
        self._minmax_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._minmax_label)

        self._temp_view = _HourlyWeatherView()
        layout.addWidget(self._wrap_scroll(self._temp_view), 1)

        return page

    def _build_page2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        title = QLabel("Wiatr")
        title.setObjectName("weatherSectionTitle")
        layout.addWidget(title)

        header = QHBoxLayout()
        header.setSpacing(12)
        self._wind_now_label = QLabel("--")
        self._wind_now_label.setObjectName("weatherWindNow")
        self._wind_gusts_header_label = QLabel("Porywy: --")
        self._wind_gusts_header_label.setObjectName("weatherMinMax")
        header.addStretch()
        header.addWidget(self._wind_now_label)
        header.addWidget(self._wind_gusts_header_label)
        header.addStretch()
        layout.addLayout(header)

        self._wind_view = _WindHourlyView()
        layout.addWidget(self._wrap_scroll(self._wind_view), 1)

        return page

    def _build_page3(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        self._p3_location_label = QLabel("--")
        self._p3_location_label.setObjectName("weatherLocation")
        self._p3_location_label.setWordWrap(True)
        layout.addWidget(self._p3_location_label)

        icon_row, self._p3_icon, self._p3_fog, self._p3_storm = self._build_icon_row()
        layout.addLayout(icon_row)

        self._no_precip_label = QLabel("Brak opad\u00F3w przez najbli\u017Csze 24h")
        self._no_precip_label.setObjectName("noPrecipLabel")
        self._no_precip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_precip_label.setWordWrap(True)
        self._no_precip_label.hide()
        layout.addWidget(self._no_precip_label)

        self._precip_view = _PrecipHourlyView()
        layout.addWidget(self._wrap_scroll(self._precip_view), 1)

        return page

    def _build_page4(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        self._sun_view = _SunPositionWidget()
        layout.addWidget(self._sun_view)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        self._humidity_label = self._make_detail()
        self._pressure_label = self._make_detail()
        self._uv_label = self._make_detail()
        self._sunrise_label = self._make_detail()
        self._sunset_label = self._make_detail()
        self._wind_max_label = self._make_detail()
        self._gust_max_label = self._make_detail()
        self._precip_sum_label = self._make_detail()

        left = [
            ("Wilgotno\u015B\u0107", self._humidity_label),
            ("Ci\u015Bnienie", self._pressure_label),
            ("UV Index", self._uv_label),
            ("Wsch\u00F3d", self._sunrise_label),
        ]
        right = [
            ("Zach\u00F3d", self._sunset_label),
            ("Maks. wiatr", self._wind_max_label),
            ("Maks. porywy", self._gust_max_label),
            ("Opady (doba)", self._precip_sum_label),
        ]
        for r, (name, lbl) in enumerate(left):
            n = QLabel(name)
            n.setObjectName("weatherDetailName")
            grid.addWidget(n, r, 0)
            grid.addWidget(lbl, r, 1)
        for r, (name, lbl) in enumerate(right):
            n = QLabel(name)
            n.setObjectName("weatherDetailName")
            grid.addWidget(n, r, 2)
            grid.addWidget(lbl, r, 3)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        return scroll

    @staticmethod
    def _make_detail() -> QLabel:
        lbl = QLabel("--")
        lbl.setObjectName("weatherDetail")
        return lbl

    def _prev_page(self) -> None:
        self._page_index = (self._page_index - 1) % 4
        self._switch_page()

    def _next_page(self) -> None:
        self._page_index = (self._page_index + 1) % 4
        self._switch_page()

    def _switch_page(self) -> None:
        self._stack.setCurrentIndex(self._page_index)
        self._page_indicator.setText(f"{self._page_index + 1}/4")

    def _update_icons(self, code: int) -> None:
        main = _weather_emoji(code)
        fog = _is_fog(code)
        storm = _is_storm(code)
        pairs = [
            (self._p1_icon, self._p1_fog, self._p1_storm),
            (self._p3_icon, self._p3_fog, self._p3_storm),
        ]
        for icon, fog_lbl, storm_lbl in pairs:
            icon.setText(main)
            fog_lbl.setText("\u2261" if fog else "")
            fog_lbl.setVisible(fog)
            storm_lbl.setText("\u26A1" if storm else "")
            storm_lbl.setVisible(storm)

    def update_weather(self, weather: Optional[WeatherData]) -> None:
        if weather is None:
            self.clear()
            return
        self._weather = weather
        name = weather.location_name or "Wybrana lokalizacja"

        self._location_label.setText(name)
        self._p3_location_label.setText(name)
        self._temp_label.setText(f"{weather.temperature:.1f}\u00B0C")
        self._minmax_label.setText(
            f"\u2191{weather.daily_max_temp:.0f}\u00B0  "
            f"\u2193{weather.daily_min_temp:.0f}\u00B0"
        )
        self._wind_now_label.setText(f"{_kmh_to_ms(weather.wind_speed):.0f} m/s")
        self._wind_gusts_header_label.setText(
            f"Porywy: {_kmh_to_ms(weather.wind_gusts):.0f} m/s"
        )

        self._update_icons(weather.weather_code)

        if weather.hourly_times:
            self._temp_view.set_data(
                weather.hourly_times,
                weather.hourly_temperatures,
                weather.hourly_weather_codes,
                weather.hourly_precipitation,
                weather.sunrise,
                weather.sunset,
            )
            self._wind_view.set_data(
                weather.hourly_times,
                weather.hourly_wind_speeds,
                weather.hourly_wind_gusts,
                weather.hourly_wind_directions,
            )
            precip_args = (
                weather.hourly_times,
                weather.hourly_precipitation,
                weather.hourly_rain,
                weather.hourly_snowfall,
                weather.hourly_hail,
                weather.hourly_weather_codes,
            )
            self._precip_view.set_data(*precip_args)

            has_precip = any(p > 0 for p in weather.hourly_precipitation)
            self._no_precip_label.setVisible(not has_precip)
        else:
            self._no_precip_label.setVisible(False)

        self._humidity_label.setText(f"{weather.humidity}%")
        self._pressure_label.setText(f"{weather.pressure:.0f} hPa")
        self._uv_label.setText(f"{weather.uv_index:.1f}")
        if weather.sunrise:
            self._sunrise_label.setText(_format_hour(weather.sunrise))
        if weather.sunset:
            self._sunset_label.setText(_format_hour(weather.sunset))
        self._wind_max_label.setText(f"{_kmh_to_ms(weather.daily_max_wind_speed):.0f} m/s")
        self._gust_max_label.setText(f"{_kmh_to_ms(weather.daily_max_wind_gusts):.0f} m/s")
        self._precip_sum_label.setText(f"{weather.daily_precip_sum:.1f} mm")
        self._sun_view.set_data(weather.sunrise, weather.sunset, weather.timezone)

    def clear(self) -> None:
        for lbl in (self._location_label, self._p3_location_label):
            if lbl:
                lbl.setText("--")
        self._temp_label.setText("--\u00B0C")
        self._minmax_label.setText("-- / --")
        self._wind_now_label.setText("--")
        self._wind_gusts_header_label.setText("Porywy: --")
        self._update_icons(0)
        self._temp_view.clear()
        self._wind_view.clear()
        self._precip_view.clear()
        self._sun_view.clear()
        self._no_precip_label.setVisible(False)
        for lbl in (
            self._humidity_label, self._pressure_label, self._uv_label,
            self._sunrise_label, self._sunset_label,
            self._wind_max_label, self._gust_max_label, self._precip_sum_label,
        ):
            lbl.setText("--")
