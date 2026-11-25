import pytest
from PIL import Image

from core import editor as ed
from core import theme_store as store
from core.theme import Theme, Widget, default_theme


def tema():
    return Theme(name="T", widgets=[Widget(type="label", label="A"),
                                    Widget(type="label", label="B"),
                                    Widget(type="label", label="C")])


def rotulos(t):
    return [w.label for w in t.widgets]


# A3
def test_mover_altera_x_y():
    t = tema()
    ed.move_widget(t, 1, 100, 50)
    assert (t.widgets[1].x, t.widgets[1].y) == (100, 50)


def test_mover_limita_ao_quadro():
    t = tema()
    ed.move_widget(t, 0, -30, 9999)
    assert (t.widgets[0].x, t.widgets[0].y) == (0, t.height)


def test_indice_invalido():
    with pytest.raises(ed.EditorError):
        ed.move_widget(tema(), 7, 0, 0)


# A4
def test_adicionar_preserva_demais():
    t = tema()
    i = ed.add_widget(t, "bar", x=5, y=6)
    assert i == 3 and rotulos(t)[:3] == ["A", "B", "C"] and t.widgets[3].type == "bar"


def test_adicionar_tipo_invalido():
    with pytest.raises(ed.EditorError):
        ed.add_widget(tema(), "foto")


def test_adicionar_com_propriedade_invalida_nao_deixa_widget():
    t = tema()
    with pytest.raises(ed.EditorError):
        ed.add_widget(t, "text", size=-5)
    assert len(t.widgets) == 3


def test_remover_preserva_ordem():
    t = tema()
    ed.remove_widget(t, 1)
    assert rotulos(t) == ["A", "C"]


def test_duplicar_insere_apos_original_e_e_independente():
    t = tema()
    i = ed.duplicate_widget(t, 0)
    assert i == 1 and rotulos(t) == ["A", "A", "B", "C"]
    assert t.widgets[1].x == t.widgets[0].x + 10
    t.widgets[1].label = "Z"
    assert t.widgets[0].label == "A"


# A5
@pytest.mark.parametrize("nome,valor", [
    ("size", -1), ("size", "abc"), ("font", ""), ("font", "   "),
    ("color", "vermelho"), ("align", "topo"), ("fmt", "{:q}"),
    ("field", "nao_existe"), ("type", "foto"), ("inexistente", 1), ("width", 0),
])
def test_propriedade_invalida_nao_altera(nome, valor):
    t = tema()
    antes = t.to_dict()
    with pytest.raises(ed.EditorError):
        ed.set_property(t, 0, nome, valor)
    assert t.to_dict() == antes


def test_propriedade_valida_converte():
    t = tema()
    ed.set_property(t, 0, "size", "24")
    ed.set_property(t, 0, "color", "#ff00aa")
    ed.set_property(t, 0, "unit", "")
    assert t.widgets[0].size == 24 and t.widgets[0].color == "#FF00AA"


def test_campos_de_sensor_incluem_cpu_e_excluem_extra():
    assert "cpu_percent" in ed.SENSOR_FIELDS and "extra" not in ed.SENSOR_FIELDS


# A6
def test_salvar_roundtrip(themes_dir):
    t = default_theme()
    t.name = "Salvo"
    path = ed.save_theme(t)
    assert path.parent == themes_dir
    assert Theme.load(path) == t


def test_mover_e_salvar_reflete_no_json(themes_dir):
    t = ed.new_theme("Mov", tema())
    ed.move_widget(t, 0, 77, 88)
    ed.save_theme(t)
    w = store.load_theme("Mov").widgets[0]
    assert (w.x, w.y) == (77, 88)


# A7
def test_renomear_troca_nome_e_arquivo(themes_dir):
    t = ed.new_theme("Antigo", default_theme())
    ed.save_theme(t)
    ed.rename_theme(t, "Novo")
    assert not (themes_dir / "Antigo.json").exists()
    assert store.load_theme("Novo").name == "Novo"


def test_renomear_para_o_mesmo_nome_nao_apaga(themes_dir):
    t = ed.new_theme("Igual")
    ed.save_theme(t)
    ed.rename_theme(t, "Igual")
    assert (themes_dir / "Igual.json").exists()


# A8
def test_nome_duplicado_recusado(themes_dir):
    ed.save_theme(ed.new_theme("A"))
    with pytest.raises(ed.EditorError):
        ed.new_theme("A")
    outro = Theme(name="A", background_color="#111111")
    with pytest.raises(ed.EditorError):
        ed.save_theme(outro)
    assert store.load_theme("A").background_color != "#111111"


def test_renomear_para_nome_existente_recusado(themes_dir):
    a = ed.new_theme("A")
    ed.save_theme(a)
    b = ed.new_theme("B")
    ed.save_theme(b)
    with pytest.raises(ed.EditorError):
        ed.rename_theme(b, "A")
    assert b.name == "B" and (themes_dir / "B.json").exists()


@pytest.mark.parametrize("nome", ["", "  ", "a/b", "a\\b", "..", "x:y", "fim."])
def test_nome_invalido(themes_dir, nome):
    with pytest.raises(ed.EditorError):
        ed.new_theme(nome)


# A9
def test_importar_fundo_copia_e_caminho_relativo(tmp_path):
    src = tmp_path / "origem" / "meu fundo.png"
    src.parent.mkdir()
    Image.new("RGB", (10, 10), "#ff0000").save(src)
    root = tmp_path / "proj"
    t = Theme()
    rel = ed.import_background(t, src, root=root)
    assert rel == "assets/backgrounds/meu fundo.png" == t.background_image
    assert (root / rel).is_file()


def test_importar_fundo_nome_igual_conteudo_diferente_nao_sobrescreve(tmp_path):
    root = tmp_path / "proj"
    a = tmp_path / "a" / "f.png"
    a.parent.mkdir()
    b = tmp_path / "b" / "f.png"
    b.parent.mkdir()
    Image.new("RGB", (4, 4), "#ff0000").save(a)
    Image.new("RGB", (4, 4), "#00ff00").save(b)
    t = Theme()
    r1 = ed.import_background(t, a, root=root)
    r2 = ed.import_background(t, b, root=root)
    assert r1 != r2 and (root / r1).read_bytes() != (root / r2).read_bytes()


def test_importar_fundo_recusa_nao_imagem(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("oi")
    with pytest.raises(ed.EditorError):
        ed.import_background(Theme(), f, root=tmp_path / "proj")
    with pytest.raises(ed.EditorError):
        ed.import_background(Theme(), tmp_path / "nao_existe.png", root=tmp_path / "proj")


def test_cor_de_fundo():
    t = Theme()
    ed.set_background_color(t, "#abcdef")
    assert t.background_color == "#ABCDEF"
    with pytest.raises(ed.EditorError):
        ed.set_background_color(t, "azul")
