"""Testes do editor visual (offscreen, sem tela real e sem tocar themes/ ou assets/ reais)."""
import pytest
from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core import editor as ed
from core import theme_store as store
from core.renderer import Renderer
from core.theme import Theme, Widget, default_theme
from ui.editor import READING, EditorDialog, PropertyPanel, ThemeCanvas


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def tema():
    return Theme(name="T", widgets=[
        Widget(type="label", x=40, y=40, label="Ola", size=20),
        Widget(type="bar", x=40, y=100, field="cpu_percent", width=100, height=14),
        Widget(type="text", x=200, y=40, field="cpu_percent", align="right", unit="%"),
    ])


# A1
def test_dialogo_abre_com_tema_e_mostra_quadro(app):
    d = EditorDialog(default_theme(), original_name="Padrao Escuro")
    assert d.canvas.theme.name == "Padrao Escuro"
    assert d.wlist.count() == len(default_theme().widgets)
    assert d.canvas._pix_item.pixmap().width() == 480


# A2
def test_area_de_selecao_bate_com_widget_bbox(app):
    t = tema()
    c = ThemeCanvas(t)
    r = Renderer(t)
    for i, w in enumerate(t.widgets):
        assert c.selection_rect(i) == tuple(round(v) for v in r.widget_bbox(w, READING))


def test_selecionar_emite_sinal(app):
    c = ThemeCanvas(tema())
    vistos = []
    c.widget_selected.connect(vistos.append)
    c.select(1)
    assert vistos == [1] and c.selected == 1


# A3 / passo 4: arrastar com o mouse de verdade
def test_arrastar_muda_xy_e_re_renderiza(app):
    t = tema()
    c = ThemeCanvas(t)
    c.show()
    antes = c.renderer.render(READING).tobytes()
    x, y, w, h = c.selection_rect(1)
    ini = c.mapFromScene(x + w / 2, y + h / 2)
    fim = QPoint(ini.x() + 30, ini.y() + 20)
    QTest.mousePress(c.viewport(), Qt.LeftButton, Qt.NoModifier, ini)
    QTest.mouseMove(c.viewport(), fim)
    QTest.mouseRelease(c.viewport(), Qt.LeftButton, Qt.NoModifier, fim)
    QApplication.processEvents()
    QTest.qWait(30)   # o commit e adiado para fora do evento do mouse
    assert (t.widgets[1].x, t.widgets[1].y) == (70, 120)
    assert c.renderer.render(READING).tobytes() != antes


def test_commit_move_limita_ao_quadro(app):
    t = tema()
    c = ThemeCanvas(t)
    c.commit_move(0, -500, 0)
    assert t.widgets[0].x == 0


# passo 4: o JSON salvo reflete a posicao
def test_posicao_arrastada_vai_para_o_json(app, themes_dir):
    d = EditorDialog(ed.new_theme("Arr", tema()), original_name=None)
    d.canvas.commit_move(1, 15, 5)
    assert d.save()
    w = store.load_theme("Arr").widgets[1]
    assert (w.x, w.y) == (55, 105)


# A5 / passo 5
def test_painel_recusa_valor_invalido_sem_alterar(app):
    t = tema()
    p = PropertyPanel()
    p.set_widget(t, 0)
    antes = t.to_dict()
    assert p.apply("size", -3) is False
    assert p.apply("font", "") is False
    assert p.apply("color", "xyz") is False
    assert t.to_dict() == antes and p.error.text()


def test_painel_aplica_valor_valido_e_avisa(app):
    t = tema()
    p = PropertyPanel()
    p.set_widget(t, 0)
    avisos = []
    p.changed.connect(lambda: avisos.append(1))
    assert p.apply("size", 33) is True
    assert t.widgets[0].size == 33 and avisos == [1] and p.error.text() == ""


def test_painel_campo_texto_invalido_restaura_controle(app):
    t = tema()
    p = PropertyPanel()
    p.set_widget(t, 0)
    ctl = p._controls["font"]
    ctl.setText("")
    ctl.editingFinished.emit()
    assert ctl.text() == "Segoe UI" and t.widgets[0].font == "Segoe UI"


def test_painel_unidade_vazia_remove_percentual(app):
    t = tema()
    p = PropertyPanel()
    p.set_widget(t, 2)
    assert t.widgets[2].unit == "%"
    p.apply("unit", "")
    assert t.widgets[2].unit == ""


# widgets pelo dialogo (A4 na UI)
def test_dialogo_adicionar_duplicar_remover(app):
    d = EditorDialog(tema(), original_name=None)
    n = len(d.theme.widgets)
    d.type_combo.setCurrentText("ring")
    d._add()
    assert len(d.theme.widgets) == n + 1 and d.theme.widgets[-1].type == "ring"
    d._duplicate()
    assert len(d.theme.widgets) == n + 2
    d._remove()
    assert len(d.theme.widgets) == n + 1
    assert d.wlist.count() == n + 1


# A9 / passo 6 (assets simulado em tmp_path)
def test_fundo_copiado_e_relativo(app, tmp_path, monkeypatch):
    monkeypatch.setattr(ed, "PROJECT_ROOT", tmp_path / "proj")
    src = tmp_path / "bg.png"
    Image.new("RGB", (480, 320), "#336699").save(src)
    d = EditorDialog(tema(), original_name=None)
    assert d.set_background_image(src)
    assert d.theme.background_image == "assets/backgrounds/bg.png"
    assert (tmp_path / "proj" / d.theme.background_image).is_file()


def test_fundo_invalido_mostra_mensagem(app, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    d = EditorDialog(tema(), original_name=None)
    assert d.set_background_image(f) is False and d.msg.text()


# salvar / renomear pela UI (A6, A7, A8)
def test_salvar_tema_novo_e_recusar_nome_existente(app, themes_dir):
    d = EditorDialog(ed.new_theme("Um", tema()), original_name=None)
    assert d.save() and d.saved_name == "Um"
    d2 = EditorDialog(Theme(name="Dois"), original_name=None)
    d2.name_edit.setText("Um")
    assert d2.save() is False and d2.msg.text()
    assert len(store.load_theme("Um").widgets) == 3     # nao foi sobrescrito


def test_renomear_pelo_dialogo(app, themes_dir):
    t = ed.new_theme("Velho", tema())
    ed.save_theme(t)
    d = EditorDialog(store.load_theme("Velho"), original_name="Velho")
    d.name_edit.setText("Novo")
    assert d.save()
    assert not (themes_dir / "Velho.json").exists()
    assert store.load_theme("Novo").name == "Novo"


def test_editar_nao_altera_original_se_cancelar(app, themes_dir):
    ed.save_theme(ed.new_theme("Orig", tema()))
    d = EditorDialog(store.load_theme("Orig"), original_name="Orig")
    d.canvas.commit_move(0, 50, 50)
    d.reject()
    assert store.load_theme("Orig").widgets[0].x == 40
