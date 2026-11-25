"""Editor visual de temas: canvas com preview, arrastar widgets e painel de propriedades.

O quadro mostrado e sempre o gerado por `Renderer.render` (Pillow). Sobre ele ficam
retangulos de selecao desenhados com `Renderer.widget_bbox`. Arrastar so re-renderiza
ao soltar o mouse. O editor altera apenas o `Theme` em memoria; a escrita em disco
acontece so ao salvar, via `core.editor`.
"""
from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QColorDialog, QDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from core import editor as ed
from core.renderer import Renderer
from core.theme import Theme
from ui.widgets import _DEMO, pil_to_qpixmap

READING = _DEMO   # leitura ficticia do preview


class _BBoxItem(QGraphicsRectItem):
    """Retangulo de um widget; arrastavel. Avisa o canvas ao soltar o mouse."""

    def __init__(self, idx: int, rect: QRectF, canvas: "ThemeCanvas"):
        super().__init__(rect)
        self.idx = idx
        self._canvas = canvas
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable)
        self.setPen(QPen(QColor(0, 200, 255, 160), 1, Qt.DashLine))
        self.setBrush(QBrush(QColor(0, 200, 255, 20)))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedHasChanged:
            sel = bool(value)
            self.setPen(QPen(QColor("#FFB000") if sel else QColor(0, 200, 255, 160),
                             2 if sel else 1, Qt.DashLine))
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        dx, dy = round(self.pos().x()), round(self.pos().y())
        if dx or dy:
            # adia: o refresh apaga este item, nao pode ocorrer dentro do proprio evento
            QTimer.singleShot(0, lambda i=self.idx: self._canvas.commit_move(i, dx, dy))


class ThemeCanvas(QGraphicsView):
    widget_selected = Signal(int)    # -1 = nenhum
    theme_changed = Signal()         # posicao mudou (arrastar)

    def __init__(self, theme: Theme):
        super().__init__()
        self.theme = theme
        self.renderer = Renderer(theme)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QGraphicsView.NoFrame)
        self._pix_item = None
        self._items: list[_BBoxItem] = []
        self._selected = -1
        self._scene.selectionChanged.connect(self._on_scene_selection)
        self.refresh()

    # ---- desenho -------------------------------------------------------
    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.renderer.set_theme(theme)
        self.refresh()

    def refresh(self, keep_selection: bool = True) -> None:
        """Re-renderiza o quadro e refaz os retangulos de selecao."""
        sel = self._selected if keep_selection else -1
        self.renderer.set_theme(self.theme)   # limpa o cache de fundo
        pix = pil_to_qpixmap(self.renderer.render(READING))
        self._scene.blockSignals(True)
        self._scene.clear()
        self._items = []
        self._pix_item = self._scene.addPixmap(pix)
        self._scene.setSceneRect(0, 0, self.theme.width, self.theme.height)
        for i, w in enumerate(self.theme.widgets):
            x, y, bw, bh = self.renderer.widget_bbox(w, READING)
            item = _BBoxItem(i, QRectF(x, y, bw, bh), self)
            self._scene.addItem(item)
            self._items.append(item)
        self._scene.blockSignals(False)
        self.setFixedSize(self.theme.width + 4, self.theme.height + 4)
        self._selected = -1
        if 0 <= sel < len(self._items):
            self.select(sel, emit=False)

    def selection_rect(self, idx: int) -> tuple[int, int, int, int]:
        """Retangulo (x, y, largura, altura) do item de selecao, na cena."""
        item = self._items[idx]
        r = item.rect().translated(item.pos())    # sem a espessura do contorno
        return (round(r.x()), round(r.y()), round(r.width()), round(r.height()))

    def select(self, idx: int, emit: bool = True) -> None:
        self._scene.blockSignals(True)
        self._scene.clearSelection()
        if 0 <= idx < len(self._items):
            self._items[idx].setSelected(True)
            self._selected = idx
        else:
            self._selected = -1
        self._scene.blockSignals(False)
        self._scene.update()
        if emit:
            self.widget_selected.emit(self._selected)

    @property
    def selected(self) -> int:
        return self._selected

    # ---- interacao -----------------------------------------------------
    def _on_scene_selection(self) -> None:
        items = self._scene.selectedItems()
        self._selected = items[0].idx if items else -1
        self.widget_selected.emit(self._selected)

    def commit_move(self, idx: int, dx: int, dy: int) -> None:
        w = self.theme.widgets[idx]
        ed.move_widget(self.theme, idx, w.x + dx, w.y + dy)
        self._selected = idx
        self.refresh()
        self.theme_changed.emit()


class PropertyPanel(QWidget):
    """Edita os campos do widget selecionado; valor invalido e recusado com mensagem."""
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.theme: Theme | None = None
        self.idx = -1
        self._loading = False
        self._controls: dict[str, QWidget] = {}
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        for name in ("type", "field", "label", "unit", "fmt", "font", "size", "bold",
                     "color", "align", "x", "y", "width", "height",
                     "min_value", "max_value", "bg_color", "fill_color"):
            ctl = self._make_control(name)
            self._controls[name] = ctl
            form.addRow(name, ctl)
        self.error = QLabel("")
        self.error.setStyleSheet("color:#ff6b6b;")
        self.error.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(form)
        lay.addWidget(self.error)
        self.setEnabled(False)

    def _make_control(self, name: str) -> QWidget:
        if name == "type":
            c = QComboBox()
            c.addItems(ed.WIDGET_TYPES)
            c.currentTextChanged.connect(lambda v, n=name: self.apply(n, v))
        elif name == "align":
            c = QComboBox()
            c.addItems(ed.ALIGNS)
            c.currentTextChanged.connect(lambda v, n=name: self.apply(n, v))
        elif name == "field":
            c = QComboBox()
            c.addItems(("",) + ed.SENSOR_FIELDS)
            c.currentTextChanged.connect(lambda v, n=name: self.apply(n, v))
        elif name in ("size", "x", "y", "width", "height"):
            c = QSpinBox()
            c.setRange(ed._INT_MIN[name], 2000)
            c.valueChanged.connect(lambda v, n=name: self.apply(n, v))
        elif name in ("min_value", "max_value"):
            c = QDoubleSpinBox()
            c.setRange(-1e6, 1e6)
            c.valueChanged.connect(lambda v, n=name: self.apply(n, v))
        elif name == "bold":
            c = QCheckBox()
            c.toggled.connect(lambda v, n=name: self.apply(n, v))
        else:   # texto livre (label, unit, fmt, font, cores)
            c = QLineEdit()
            c.editingFinished.connect(lambda n=name, w=c: self.apply(n, w.text()))
        return c

    def set_widget(self, theme: Theme, idx: int) -> None:
        self.theme, self.idx = theme, idx
        self.error.setText("")
        valid = 0 <= idx < len(theme.widgets)
        self.setEnabled(valid)
        if valid:
            self._load()

    def _load(self) -> None:
        w = self.theme.widgets[self.idx]
        self._loading = True
        for name, c in self._controls.items():
            v = getattr(w, name)
            if isinstance(c, QComboBox):
                c.setCurrentText(str(v))
            elif isinstance(c, QCheckBox):
                c.setChecked(bool(v))
            elif isinstance(c, (QSpinBox, QDoubleSpinBox)):
                c.setValue(v)
            else:
                c.setText(str(v))
        self._loading = False

    def apply(self, name: str, value) -> bool:
        """Aplica uma propriedade. Devolve False (e mostra o motivo) se for recusada."""
        if self._loading or self.theme is None or self.idx < 0:
            return True
        try:
            ed.set_property(self.theme, self.idx, name, value)
        except ed.EditorError as exc:
            self.error.setText(str(exc))
            self._load()     # volta o campo ao valor valido
            return False
        self.error.setText("")
        self.changed.emit()
        return True


class EditorDialog(QDialog):
    """Janela do editor. `original_name` e None para tema novo."""

    def __init__(self, theme: Theme, original_name: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de temas")
        self.theme = copy.deepcopy(theme)
        self.original_name = original_name
        self.saved_name: str | None = None
        self._build()
        self._fill_list()

    def _build(self) -> None:
        self.canvas = ThemeCanvas(self.theme)
        self.canvas.widget_selected.connect(self._on_canvas_selected)
        self.canvas.theme_changed.connect(self._on_changed)
        self.props = PropertyPanel()
        self.props.changed.connect(self._on_changed)

        self.name_edit = QLineEdit(self.theme.name)
        self.wlist = QListWidget()
        self.wlist.currentRowChanged.connect(self._on_list_selected)
        self.type_combo = QComboBox()
        self.type_combo.addItems(ed.WIDGET_TYPES)
        btn_add = QPushButton("Adicionar")
        btn_add.clicked.connect(self._add)
        btn_dup = QPushButton("Duplicar")
        btn_dup.clicked.connect(self._duplicate)
        btn_del = QPushButton("Remover")
        btn_del.clicked.connect(self._remove)

        btn_img = QPushButton("Imagem de fundo...")
        btn_img.clicked.connect(self._choose_image)
        btn_noimg = QPushButton("Sem imagem")
        btn_noimg.clicked.connect(self._clear_image)
        btn_col = QPushButton("Cor de fundo...")
        btn_col.clicked.connect(self._choose_color)

        self.msg = QLabel("")
        self.msg.setStyleSheet("color:#ff6b6b;")
        btn_save = QPushButton("Salvar")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self.save)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        left = QVBoxLayout()
        left.addWidget(self.canvas)
        bg = QHBoxLayout()
        for b in (btn_img, btn_noimg, btn_col):
            bg.addWidget(b)
        left.addLayout(bg)
        left.addStretch()

        right = QVBoxLayout()
        nm = QHBoxLayout()
        nm.addWidget(QLabel("Nome:"))
        nm.addWidget(self.name_edit, 1)
        right.addLayout(nm)
        right.addWidget(self.wlist, 1)
        row = QHBoxLayout()
        row.addWidget(self.type_combo)
        row.addWidget(btn_add)
        row.addWidget(btn_dup)
        row.addWidget(btn_del)
        right.addLayout(row)
        right.addWidget(self.props)
        right.addWidget(self.msg)
        row2 = QHBoxLayout()
        row2.addStretch()
        row2.addWidget(btn_cancel)
        row2.addWidget(btn_save)
        right.addLayout(row2)

        root = QHBoxLayout(self)
        root.addLayout(left)
        root.addLayout(right, 1)

    # ---- lista e selecao ----------------------------------------------
    def _label(self, i: int) -> str:
        w = self.theme.widgets[i]
        extra = w.label or w.field
        return f"{i + 1}. {w.type}" + (f" - {extra}" if extra else "")

    def _fill_list(self, select: int = -1) -> None:
        self.wlist.blockSignals(True)
        self.wlist.clear()
        for i in range(len(self.theme.widgets)):
            self.wlist.addItem(self._label(i))
        self.wlist.setCurrentRow(select)
        self.wlist.blockSignals(False)
        self.canvas.select(select, emit=False)
        self.props.set_widget(self.theme, select)

    def _on_canvas_selected(self, idx: int) -> None:
        self.wlist.blockSignals(True)
        self.wlist.setCurrentRow(idx)
        self.wlist.blockSignals(False)
        self.props.set_widget(self.theme, idx)

    def _on_list_selected(self, idx: int) -> None:
        self.canvas.select(idx, emit=False)
        self.props.set_widget(self.theme, idx)

    def _on_changed(self) -> None:
        if self.sender() is self.canvas:
            sel = self.canvas.selected          # o canvas ja re-renderizou
        else:
            sel = self.props.idx
            self.canvas.refresh()
        self._fill_list(sel)

    # ---- widgets -------------------------------------------------------
    def _add(self) -> None:
        idx = ed.add_widget(self.theme, self.type_combo.currentText())
        self.canvas.refresh(keep_selection=False)
        self._fill_list(idx)

    def _duplicate(self) -> None:
        i = self.props.idx
        if i < 0:
            return
        new = ed.duplicate_widget(self.theme, i)
        self.canvas.refresh(keep_selection=False)
        self._fill_list(new)

    def _remove(self) -> None:
        i = self.props.idx
        if i < 0:
            return
        ed.remove_widget(self.theme, i)
        self.canvas.refresh(keep_selection=False)
        self._fill_list(-1)

    # ---- fundo ---------------------------------------------------------
    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Imagem de fundo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.set_background_image(path)

    def set_background_image(self, path: str | Path) -> bool:
        try:
            ed.import_background(self.theme, path)
        except ed.EditorError as exc:
            self.msg.setText(str(exc))
            return False
        self.msg.setText("")
        self.canvas.refresh()
        return True

    def _clear_image(self) -> None:
        ed.clear_background(self.theme)
        self.canvas.refresh()

    def _choose_color(self) -> None:
        c = QColorDialog.getColor(QColor(self.theme.background_color), self, "Cor de fundo")
        if c.isValid():
            ed.set_background_color(self.theme, c.name())
            self.canvas.refresh()

    # ---- salvar --------------------------------------------------------
    def save(self) -> bool:
        """Grava em themes/. Recusa nome vazio, invalido ou de outro tema existente."""
        name = self.name_edit.text()
        try:
            if self.original_name is None:
                self.theme.name = name
                ed.save_theme(self.theme)
            elif name.strip() != self.original_name:
                ed.rename_theme(self.theme, name)
            else:
                ed.save_theme(self.theme, overwrite=True)
        except ed.EditorError as exc:
            self.theme.name = self.original_name or self.theme.name
            self.msg.setText(str(exc))
            return False
        self.saved_name = self.theme.name
        self.accept()
        return True
