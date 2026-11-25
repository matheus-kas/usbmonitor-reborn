import pytest

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


def test_nome_do_arquivo_manda_sobre_o_campo_name(themes_dir):
    """Regra nome = arquivo: A.json com name='B' aparece e carrega como 'A'."""
    Theme(name="B").save(themes_dir / "A.json")
    assert store.load_theme("A").name == "A"
    assert store.load_theme("B").name == "Padrao Escuro"
    assert "A" in [t.name for t in store.list_themes()]
    assert "B" not in [t.name for t in store.list_themes()]


@pytest.mark.parametrize("nome", ["..\\fora", "../fora", "a/b", "CON", "nul", "COM1", "x\\y", ""])
def test_load_theme_recusa_nome_inseguro(themes_dir, nome):
    (themes_dir.parent / "fora.json").write_text(Theme(name="fora").to_dict().__repr__())
    assert store.load_theme(nome).name == "Padrao Escuro"


def test_is_safe_name():
    assert store.is_safe_name("Meu tema") and store.is_safe_name("NZXT")
    assert not store.is_safe_name("con.txt") and not store.is_safe_name(" espaco")


def test_psutil_real_nunca_e_chamado(psutil_simulado):
    import psutil
    import core.sensors as sensors
    assert sensors.psutil is psutil_simulado
    sensors.SensorHub().read()
    assert "cpu_percent" in psutil_simulado.calls
    try:
        psutil.cpu_percent()
    except AssertionError:
        pass
    else:
        raise AssertionError("o psutil real deveria estar bloqueado")
