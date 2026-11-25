"""Widgets reutilizaveis da UI: miniatura de tema e galeria."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from core.renderer import Renderer
from core.sensors import Reading

PREVIEWS = Path(__file__).resolve().parent.parent / "assets" / "previews"

# leitura ficticia para renderizar miniaturas quando nao ha preview salvo
_DEMO = Reading(cpu_percent=37, gpu_percent=62, ram_percent=48, disk_percent=71,
                cpu_temp_c=54, gpu_temp_c=58, gpu_mem_percent=40, gpu_fan_percent=45,
                gpu_name="RTX 3060", net_down_kbps=1234, net_up_kbps=321,
                uptime="2d 05:12", clock="14:35", date="24/11/2026")


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGB":
        img = img.convert("RGB")
    data = img.tobytes("raw", "RGB")
    qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


def _preview_stale(preview: Path, name: str) -> bool:
    """Preview salvo mais antigo que o JSON do tema: o tema foi editado, renderiza na hora."""
    from core.theme_store import THEMES_DIR
    src = THEMES_DIR / f"{name}.json"
    try:
        return src.stat().st_mtime > preview.stat().st_mtime
    except OSError:
        return False


def theme_thumbnail(theme, width: int = 200) -> QPixmap:
    """Miniatura de um tema: usa o preview salvo ou renderiza na hora."""
    preview = PREVIEWS / f"{theme.name}.png"
    if preview.exists() and not _preview_stale(preview, theme.name):
        pix = QPixmap(str(preview))
    else:
        pix = pil_to_qpixmap(Renderer(theme).render(_DEMO))
    return pix.scaledToWidth(width, Qt.SmoothTransformation)


class ThemeCard(QFrame):
    clicked = Signal(str)

    def __init__(self, theme):
        super().__init__()
        self.theme_name = theme.name
        self.setObjectName("themeCard")
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        thumb = QLabel()
        thumb.setPixmap(theme_thumbnail(theme, 190))
        thumb.setAlignment(Qt.AlignCenter)
        lay.addWidget(thumb)
        name = QLabel(theme.name)
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("font-weight:600;")
        lay.addWidget(name)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.theme_name)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class ThemeGallery(QScrollArea):
    """Grade rolavel de miniaturas de tema."""
    theme_selected = Signal(str)

    def __init__(self, columns: int = 2):
        super().__init__()
        self.columns = columns
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(10)
        self.setWidget(self._container)
        self._cards: dict[str, ThemeCard] = {}

    def set_themes(self, themes: list) -> None:
        # limpa
        for i in reversed(range(self._grid.count())):
            w = self._grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._cards.clear()
        for idx, theme in enumerate(themes):
            card = ThemeCard(theme)
            card.clicked.connect(self._on_click)
            self._grid.addWidget(card, idx // self.columns, idx % self.columns)
            self._cards[theme.name] = card

    def _on_click(self, name: str) -> None:
        self.select(name)
        self.theme_selected.emit(name)

    def select(self, name: str) -> None:
        for n, card in self._cards.items():
            card.set_selected(n == name)
