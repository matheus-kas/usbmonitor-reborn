"""Fixtures: nada de hardware real e nada de escrita em themes/ ou assets/ reais."""
import os
import sys
import types
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# NVML simulado: core.sensors tenta nvmlInit na importacao; aqui sempre falha (sem GPU real).
_fake = types.ModuleType("pynvml")


def _fail(*a, **k):
    raise RuntimeError("NVML simulado: indisponivel em teste")


_fake.nvmlInit = _fail
sys.modules.setdefault("pynvml", _fake)

ROOT = Path(__file__).resolve().parent.parent


def _snapshot(path: Path):
    return sorted((str(p.relative_to(path)), p.stat().st_size, p.stat().st_mtime_ns)
                  for p in path.rglob("*") if p.is_file())


@pytest.fixture(scope="session", autouse=True)
def reais_intactos():
    """A11: themes/ e assets/ reais devem ser identicos antes e depois da suite."""
    antes = (_snapshot(ROOT / "themes"), _snapshot(ROOT / "assets"))
    yield
    depois = (_snapshot(ROOT / "themes"), _snapshot(ROOT / "assets"))
    assert antes == depois, "teste alterou themes/ ou assets/ reais"


@pytest.fixture
def themes_dir(tmp_path, monkeypatch):
    """Redireciona o catalogo de temas para um diretorio temporario."""
    import core.theme_store as store
    d = tmp_path / "themes"
    d.mkdir()
    monkeypatch.setattr(store, "THEMES_DIR", d)
    return d
