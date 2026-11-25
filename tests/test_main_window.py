"""Integracao da janela principal com o editor (offscreen; serial, registro e tela simulados)."""
import pytest
from PySide6.QtWidgets import QApplication

from core import autostart
from core import editor as ed
from core import theme_store as store
from core.theme import Theme, Widget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def janela(app, themes_dir, monkeypatch):
    import ui.main_window as mw
    monkeypatch.setattr(autostart, "is_enabled", lambda: False)
    monkeypatch.setattr(mw.serial.tools.list_ports, "comports", lambda: [])
    monkeypatch.setattr(mw, "find_com_port", lambda: None)
    w = mw.MainWindow()
    yield w
    w._preview_timer.stop()
    w.tray.hide()


def test_botoes_novo_e_editar_existem(janela):
    assert janela.btn_new_theme.text() == "Novo tema"
    assert janela.btn_edit_theme.text() == "Editar"


def test_editar_abre_editor_com_tema_atual(janela, monkeypatch):
    import ui.main_window as mw
    ed.save_theme(ed.new_theme("Meu", Theme(widgets=[Widget(type="label", label="x")])))
    janela._change_theme("Meu")
    abertos = []
    monkeypatch.setattr(mw.EditorDialog, "exec", lambda self: abertos.append(self) or 0)
    janela._edit_theme()
    d = abertos[0]
    assert d.original_name == "Meu" and d.theme.name == "Meu" and d.canvas.theme.widgets


def test_novo_tema_usa_nome_livre(janela, monkeypatch):
    import ui.main_window as mw
    ed.save_theme(ed.new_theme("Novo tema"))
    abertos = []
    monkeypatch.setattr(mw.EditorDialog, "exec", lambda self: abertos.append(self) or 0)
    janela._new_theme()
    assert abertos[0].original_name is None and abertos[0].theme.name == "Novo tema 2"


def test_salvar_no_editor_recarrega_galeria_e_aplica(janela, monkeypatch):
    import ui.main_window as mw

    def salva(self):
        self.name_edit.setText("Criado")
        assert self.save()
        return 1

    monkeypatch.setattr(mw.EditorDialog, "exec", salva)
    janela._new_theme()
    assert "Criado" in janela.gallery._cards
    assert janela.theme.name == "Criado" and (store.THEMES_DIR / "Criado.json").exists()


def test_cancelar_nao_muda_galeria(janela, monkeypatch):
    import ui.main_window as mw
    antes = set(janela.gallery._cards)
    monkeypatch.setattr(mw.EditorDialog, "exec", lambda self: 0)
    janela._new_theme()
    assert set(janela.gallery._cards) == antes


def test_importar_nao_sobrescreve_tema_existente(janela, monkeypatch, tmp_path):
    import ui.main_window as mw
    ed.save_theme(ed.new_theme("Existente", Theme(widgets=[Widget(type="label", label="x")])))
    src = tmp_path / "Existente.json"
    Theme(name="Existente", background_color="#010101").save(src)
    avisos = []
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(src), ""))
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: avisos.append(a[2]))
    janela._import_theme()
    assert avisos and len(store.load_theme("Existente").widgets) == 1


def test_importar_novo_tema_entra_na_galeria_com_nome_do_arquivo(janela, monkeypatch, tmp_path):
    import ui.main_window as mw
    src = tmp_path / "De Fora.json"
    Theme(name="outro nome").save(src)
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(src), ""))
    janela._import_theme()
    assert "De Fora" in janela.gallery._cards and "outro nome" not in janela.gallery._cards
