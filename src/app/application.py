from __future__ import annotations

import logging
import sys
from typing import Optional

from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtWidgets import QApplication

from src.config.settings import APP_NAME, APP_VERSION
from src.database.connection import db
from src.utils.icons import app_icon

logger = logging.getLogger(__name__)


class Application:
    _instance: Optional["Application"] = None

    def __init__(self) -> None:
        self._qt_app: Optional[QApplication] = None
        self._main_window = None
        Application._instance = self

    @classmethod
    def instance(cls) -> "Application":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def qt_app(self) -> QApplication:
        if self._qt_app is None:
            self._qt_app = QApplication(sys.argv)
            self._qt_app.setApplicationName(APP_NAME)
            self._qt_app.setOrganizationName("VibeGarden26")
            self._qt_app.setWindowIcon(app_icon())
        return self._qt_app

    def run(self) -> int:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

        db.init_schema()

        app = self.qt_app
        self._apply_stylesheet(app)

        from src.ui.main_window import MainWindow
        self._main_window = MainWindow()
        self._main_window.show()

        return app.exec()

    def quit(self) -> None:
        db.close()
        if self._qt_app:
            self._qt_app.quit()

    @staticmethod
    def _resource_dir() -> Path:
        import sys
        from pathlib import Path

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / "resources"

        return Path(__file__).parent.parent.parent / "resources"

    @staticmethod
    def _apply_stylesheet(app: QApplication) -> None:
        qss_path = Application._resource_dir() / "styles" / "main.qss"
        if qss_path.exists():
            with open(qss_path, encoding="utf-8") as f:
                app.setStyleSheet(f.read())
