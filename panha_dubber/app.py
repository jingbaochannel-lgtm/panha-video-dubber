"""QApplication entrypoint."""
from __future__ import annotations

import sys

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication

from . import APP_NAME
from .main_window import MainWindow
from .theme import app_qss


def main(argv: list[str] | None = None) -> int:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("jingbaochannel")
    app.setStyleSheet(app_qss())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
