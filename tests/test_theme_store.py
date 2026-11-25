from core import theme_store as store
from core.theme import Theme


def test_lista_inclui_padrao_embutido(themes_dir):
    nomes = [t.name for t in store.list_themes()]
    assert nomes == ["Padrao Escuro"]


def test_lista_le_arquivos_e_ignora_invalido(themes_dir):
    Theme(name="Um").save(themes_dir / "Um.json")
    (themes_dir / "quebrado.json").write_text("{nao e json", encoding="utf-8")
    nomes = [t.name for t in store.list_themes()]
    assert "Um" in nomes and "Padrao Escuro" in nomes
    assert len(nomes) == 2


def test_load_theme_por_nome_de_arquivo(themes_dir):
    Theme(name="Outro", background_color="#123456").save(themes_dir / "Outro.json")
    assert store.load_theme("Outro").background_color == "#123456"


def test_load_theme_inexistente_devolve_padrao(themes_dir):
    assert store.load_theme("nao-existe").name == "Padrao Escuro"


def test_load_theme_busca_pelo_arquivo_nao_pelo_campo_name(themes_dir):
    """Documenta o risco do plano: arquivo A.json com name='B' so carrega por 'A'."""
    Theme(name="B").save(themes_dir / "A.json")
    assert store.load_theme("A").name == "B"
    assert store.load_theme("B").name == "Padrao Escuro"
