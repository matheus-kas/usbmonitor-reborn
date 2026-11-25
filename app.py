"""UsbMonitor Reborn - ponto de entrada da aplicacao desktop."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow

DARK_QSS = """
QWidget { background:#0f1118; color:#e6e8f0; font-size:13px;
          font-family:'Segoe UI'; }
QLabel#appTitle { font-size:20px; font-weight:700; color:#ffffff; }
QLabel#sectionTitle { font-size:15px; font-weight:600; color:#8fd3ff;
                      padding:2px 0; }
QLabel#preview { background:#000; border:1px solid #242842; border-radius:10px; }
QGroupBox { border:1px solid #242842; border-radius:10px; margin-top:12px;
            padding:10px; background:#141726; }
QGroupBox::title { subcontrol-origin: margin; left:12px; padding:0 6px;
                   color:#8fd3ff; font-weight:600; }
QPushButton { background:#1d2236; border:1px solid #2a2f45; border-radius:7px;
              padding:7px 12px; }
QPushButton:hover { background:#28304d; }
QPushButton#primary { background:#0f6fff; border-color:#0f6fff; font-weight:600; }
QPushButton#primary:hover { background:#2a84ff; }
QPushButton#primary:checked { background:#d9484e; border-color:#d9484e; }
QComboBox, QSpinBox { background:#1d2236; border:1px solid #2a2f45;
                      border-radius:7px; padding:5px; }
QComboBox QAbstractItemView { background:#1d2236; selection-background-color:#0f6fff; }
QCheckBox { spacing:8px; }
QSlider::groove:horizontal { height:6px; background:#2a2f45; border-radius:3px; }
QSlider::handle:horizontal { width:16px; background:#00c8ff; border-radius:8px;
                             margin:-6px 0; }
QScrollArea { border:1px solid #242842; border-radius:10px; background:#141726; }
QFrame#themeCard { background:#1a1e30; border:2px solid transparent;
                   border-radius:10px; }
QFrame#themeCard:hover { border-color:#3a4568; }
QFrame#themeCard[selected="true"] { border-color:#00c8ff; background:#17233a; }
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    win = MainWindow()
    win.resize(820, 420)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
