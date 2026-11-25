import json

import pytest

from core.theme import Theme, Widget, default_theme


def test_roundtrip_dict():
    t = default_theme()
    assert Theme.from_dict(t.to_dict()) == t


def test_roundtrip_arquivo(tmp_path):
    t = default_theme()
    p = tmp_path / "t.json"
    t.save(p)
    assert Theme.load(p) == t


def test_widget_com_chave_desconhecida_falha():
    with pytest.raises(TypeError):
        Theme.from_dict({"widgets": [{"type": "text", "inexistente": 1}]})


def test_json_preserva_acentos(tmp_path):
    t = Theme(name="Tema Ação", widgets=[Widget(type="label", label="Ação")])
    p = tmp_path / "t.json"
    t.save(p)
    assert "Ação" in p.read_text(encoding="utf-8")
    assert json.loads(p.read_text(encoding="utf-8"))["name"] == "Tema Ação"


def test_temas_reais_carregam_sem_alterar():
    """Somente leitura dos temas versionados: todos devem carregar."""
    from pathlib import Path
    pasta = Path(__file__).resolve().parent.parent / "themes"
    arquivos = list(pasta.glob("*.json"))
    assert arquivos
    for a in arquivos:
        assert isinstance(Theme.load(a), Theme)
