"""Janela principal PySide6: preview ao vivo, galeria de temas, bandeja e controles."""
from __future__ import annotations

from pathlib import Path

import serial.tools.list_ports
from PIL import Image
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QInputDialog,
    QLabel, QMainWindow, QMenu, QMessageBox, QProgressDialog, QPushButton,
    QSlider, QSpinBox, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from core import autostart
from core.engine import DisplayEngine
from core.sensors import available_disks, available_adapters
from core import editor as theme_editor
from core.theme import Theme, default_theme
from core.theme_store import THEMES_DIR, list_themes, load_theme
from driver.turing_screen import Orientation, find_com_port
from ui.editor import EditorDialog
from ui.widgets import ThemeGallery, pil_to_qpixmap

ORIENTATIONS = {
    "Paisagem 480x320": Orientation.LANDSCAPE,
    "Paisagem invertida": Orientation.REVERSE_LANDSCAPE,
    "Retrato 320x480": Orientation.PORTRAIT,
    "Retrato invertido": Orientation.REVERSE_PORTRAIT,
}


def app_icon() -> QIcon:
    """Icone gerado: circulo ciano com um nucleo escuro."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#00C8FF"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(6, 6, 52, 52)
    p.setBrush(QColor("#121420"))
    p.drawEllipse(22, 22, 20, 20)
    p.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    frame_ready = Signal(object)
    retention_progress = Signal(float)
    retention_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UsbMonitor Reborn")
        self.setWindowIcon(app_icon())
        self.theme = default_theme()
        self.engine = DisplayEngine(self.theme, fps=1.0,
                                    orientation=Orientation.LANDSCAPE)
        self.engine.on_frame = lambda img: self.frame_ready.emit(img)
        self.frame_ready.connect(self._update_preview)
        self.retention_progress.connect(self._on_retention_progress)
        self.retention_done.connect(self._on_retention_done)
        self._retention_dialog: QProgressDialog | None = None
        self._force_quit = False
        self._build_ui()
        self._build_tray()
        self._refresh_ports()
        self._reload_gallery()
        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(self._preview_offline)
        self._preview_timer.start(1000)

    # ---- construcao da UI --------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        # ===== coluna esquerda =====
        left = QVBoxLayout()
        left.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("UsbMonitor Reborn")
        title.setObjectName("appTitle")
        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet("color:#8a90a6;font-size:16px;")
        self.status = QLabel("Desconectado")
        self.status.setStyleSheet("color:#8a90a6;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status_dot)
        header.addWidget(self.status)
        left.addLayout(header)

        self.preview = QLabel()
        self.preview.setFixedSize(480, 320)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setObjectName("preview")
        left.addWidget(self.preview)

        conn = QGroupBox("Conexao")
        cl = QHBoxLayout(conn)
        self.port_combo = QComboBox()
        btn_refresh = QPushButton("Atualizar")
        btn_refresh.clicked.connect(self._refresh_ports)
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setObjectName("primary")
        self.btn_connect.setCheckable(True)
        self.btn_connect.clicked.connect(self._toggle_connect)
        cl.addWidget(QLabel("Porta:"))
        cl.addWidget(self.port_combo, 1)
        cl.addWidget(btn_refresh)
        cl.addWidget(self.btn_connect)
        left.addWidget(conn)
        left.addStretch()
        root.addLayout(left)

        # ===== coluna direita =====
        right = QVBoxLayout()
        right.setSpacing(10)

        gal_label = QLabel("Temas")
        gal_label.setObjectName("sectionTitle")
        right.addWidget(gal_label)
        self.gallery = ThemeGallery(columns=2)
        self.gallery.theme_selected.connect(self._change_theme)
        right.addWidget(self.gallery, 1)
        gal_btns = QHBoxLayout()
        self.btn_new_theme = QPushButton("Novo tema")
        self.btn_new_theme.clicked.connect(self._new_theme)
        self.btn_edit_theme = QPushButton("Editar")
        self.btn_edit_theme.clicked.connect(self._edit_theme)
        gal_btns.addWidget(self.btn_new_theme)
        gal_btns.addWidget(self.btn_edit_theme)
        right.addLayout(gal_btns)

        disp = QGroupBox("Tela")
        dl = QVBoxLayout(disp)
        dl.addLayout(self._row("Orientacao:", self._make_orient_combo()))
        dl.addLayout(self._make_brightness_row())
        dl.addLayout(self._row("Atualizacao (FPS):", self._make_fps_spin()))
        dl.addLayout(self._row("Disco:", self._make_disk_combo()))
        dl.addLayout(self._row("Rede:", self._make_net_combo()))
        btn_recover = QPushButton("Recuperar retencao de imagem")
        btn_recover.clicked.connect(self._recover_retention)
        dl.addWidget(btn_recover)
        right.addWidget(disp)

        opt = QGroupBox("Opcoes")
        ol = QVBoxLayout(opt)
        self.chk_autostart = QCheckBox("Iniciar com o Windows")
        self.chk_autostart.setChecked(autostart.is_enabled())
        self.chk_autostart.toggled.connect(self._toggle_autostart)
        ol.addWidget(self.chk_autostart)
        self.chk_tray = QCheckBox("Minimizar para a bandeja ao fechar")
        self.chk_tray.setChecked(False)
        ol.addWidget(self.chk_tray)
        row_t = QHBoxLayout()
        btn_import = QPushButton("Importar tema (JSON)")
        btn_import.clicked.connect(self._import_theme)
        btn_folder = QPushButton("Abrir pasta de temas")
        btn_folder.clicked.connect(self._open_themes_folder)
        row_t.addWidget(btn_import)
        row_t.addWidget(btn_folder)
        ol.addLayout(row_t)
        right.addWidget(opt)

        root.addLayout(right)
        self.setCentralWidget(central)

    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        h = QHBoxLayout()
        h.addWidget(QLabel(label))
        h.addWidget(widget, 1)
        return h

    def _make_orient_combo(self) -> QComboBox:
        self.orient_combo = QComboBox()
        self.orient_combo.addItems(list(ORIENTATIONS.keys()))
        self.orient_combo.currentTextChanged.connect(self._change_orientation)
        return self.orient_combo

    def _make_brightness_row(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.addWidget(QLabel("Brilho:"))
        self.bright = QSlider(Qt.Horizontal)
        self.bright.setRange(0, 100)
        self.bright.setValue(100)
        self.bright.valueChanged.connect(self._change_brightness)
        self.bright_lbl = QLabel("100%")
        h.addWidget(self.bright, 1)
        h.addWidget(self.bright_lbl)
        return h

    def _make_fps_spin(self) -> QSpinBox:
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 10)
        self.fps_spin.setValue(1)
        self.fps_spin.valueChanged.connect(self._change_fps)
        return self.fps_spin

    def _make_disk_combo(self) -> QComboBox:
        self.disk_combo = QComboBox()
        self.disk_combo.addItems(available_disks() or ["C:\\"])
        self.disk_combo.currentTextChanged.connect(self._change_disk)
        return self.disk_combo

    def _make_net_combo(self) -> QComboBox:
        self.net_combo = QComboBox()
        self.net_combo.addItems(available_adapters())
        self.net_combo.currentTextChanged.connect(self._change_adapter)
        return self.net_combo

    # ---- bandeja ------------------------------------------------------
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip("UsbMonitor Reborn")
        menu = QMenu()
        act_show = QAction("Mostrar janela", self)
        act_show.triggered.connect(self._restore)
        act_quit = QAction("Sair", self)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._restore()

    def _restore(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self) -> None:
        self._force_quit = True
        self.close()

    # ---- acoes --------------------------------------------------------
    def _refresh_ports(self) -> None:
        self.port_combo.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports or ["(nenhuma)"])
        auto = find_com_port()
        if auto and auto in ports:
            self.port_combo.setCurrentText(auto)

    def _reload_gallery(self) -> None:
        self.gallery.set_themes(list_themes())
        self.gallery.select(self.theme.name)

    def _toggle_connect(self) -> None:
        if self.btn_connect.isChecked():
            try:
                port = self.port_combo.currentText()
                self.engine.hub.disk_path = self.disk_combo.currentText()
                adapter = self.net_combo.currentText()
                self.engine.hub.set_net_adapter(None if adapter == "Todos" else adapter)
                self.engine.connect(com_port=port if port.startswith("COM") else None)
                self.engine.start()
                self.btn_connect.setText("Desconectar")
                self.status.setText(f"Conectado ({port})")
                self.status.setStyleSheet("color:#4ade80;")
                self.status_dot.setStyleSheet("color:#4ade80;font-size:16px;")
                self._preview_timer.stop()
            except Exception as exc:
                self.btn_connect.setChecked(False)
                QMessageBox.critical(self, "Erro de conexao", str(exc))
        else:
            self.engine.stop()
            self.btn_connect.setText("Conectar")
            self.status.setText("Desconectado")
            self.status.setStyleSheet("color:#8a90a6;")
            self.status_dot.setStyleSheet("color:#8a90a6;font-size:16px;")
            self._preview_timer.start(1000)

    def _change_orientation(self, text: str) -> None:
        self.engine.set_orientation(ORIENTATIONS[text])

    def _change_brightness(self, value: int) -> None:
        self.bright_lbl.setText(f"{value}%")
        self.engine.set_brightness(value)

    def _change_fps(self, value: int) -> None:
        self.engine.fps = float(value)

    def _change_disk(self, mount: str) -> None:
        self.engine.hub.disk_path = mount

    def _change_adapter(self, name: str) -> None:
        self.engine.hub.set_net_adapter(None if name == "Todos" else name)

    def _change_theme(self, name: str) -> None:
        self.theme = load_theme(name)
        self.engine.set_theme(self.theme)
        self.gallery.select(name)
        if self.engine.screen is None:
            self._preview_offline()

    # ---- editor de temas -----------------------------------------------
    def _unique_theme_name(self) -> str:
        n, i = "Novo tema", 2
        while theme_editor.theme_path(n).exists():
            n, i = f"Novo tema {i}", i + 1
        return n

    def _new_theme(self) -> None:
        self._open_editor(Theme(name=self._unique_theme_name()), None)

    def _edit_theme(self) -> None:
        self._open_editor(self.theme, self.theme.name)

    def _open_editor(self, theme: Theme, original_name: str | None) -> str | None:
        """Abre o editor; se o usuario salvar, recarrega a galeria e aplica o tema."""
        dlg = EditorDialog(theme, original_name, self)
        dlg.exec()
        name = dlg.saved_name
        if name:
            self._reload_gallery()
            self._change_theme(name)
        return name

    def _toggle_autostart(self, enabled: bool) -> None:
        try:
            autostart.set_enabled(enabled)
        except Exception as exc:
            QMessageBox.warning(self, "Iniciar com o Windows", str(exc))

    def _recover_retention(self) -> None:
        if not self.engine.screen:
            QMessageBox.information(self, "Info", "Conecte a tela primeiro.")
            return
        minutes, ok = QInputDialog.getInt(
            self, "Recuperar retencao de imagem",
            "Duracao em minutos (quanto maior, melhor dissolve a marca):",
            2, 1, 30)
        if not ok:
            return
        self._retention_dialog = QProgressDialog(
            "Recuperando a tela... nao desconecte.", "Cancelar", 0, 100, self)
        self._retention_dialog.setWindowTitle("Recuperacao em andamento")
        self._retention_dialog.setWindowModality(Qt.WindowModal)
        self._retention_dialog.canceled.connect(self.engine.cancel_retention_recovery)
        self._retention_dialog.setValue(0)
        self._retention_dialog.show()
        self.engine.start_retention_recovery(
            minutes * 60,
            on_progress=lambda p: self.retention_progress.emit(p),
            on_done=lambda: self.retention_done.emit())

    def _on_retention_progress(self, p: float) -> None:
        if self._retention_dialog:
            self._retention_dialog.setValue(int(p * 100))

    def _on_retention_done(self) -> None:
        if self._retention_dialog:
            self._retention_dialog.setValue(100)
            self._retention_dialog.close()
            self._retention_dialog = None
        self.status.setText("Recuperacao concluida.")

    def _import_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar tema", str(THEMES_DIR), "JSON (*.json)")
        if path:
            dest = THEMES_DIR / Path(path).name
            if Path(path) != dest:
                dest.write_text(Path(path).read_text(encoding="utf-8"),
                                encoding="utf-8")
            self._reload_gallery()

    def _open_themes_folder(self) -> None:
        import os
        os.startfile(THEMES_DIR)  # noqa: S606 (abrir pasta do proprio app)

    # ---- preview ------------------------------------------------------
    def _update_preview(self, img: Image.Image) -> None:
        self.preview.setPixmap(pil_to_qpixmap(img))

    def _preview_offline(self) -> None:
        try:
            self._update_preview(self.engine.render_once())
        except Exception:
            pass

    def closeEvent(self, event) -> None:
        if not self._force_quit and self.chk_tray.isChecked() \
                and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "UsbMonitor Reborn", "Continua rodando na bandeja.",
                QSystemTrayIcon.Information, 2000)
            return
        try:
            self.engine.stop()
        except Exception:
            pass
        super().closeEvent(event)
