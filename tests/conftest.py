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


class _FakePsutil:
    """psutil simulado e deterministico; registra as chamadas em `calls`."""

    def __init__(self):
        self.calls = []

    def _n(self, nome):
        self.calls.append(nome)

    def cpu_percent(self, interval=None):
        self._n("cpu_percent")
        return 12.0

    def cpu_freq(self):
        self._n("cpu_freq")
        return None

    def virtual_memory(self):
        self._n("virtual_memory")
        return types.SimpleNamespace(percent=40.0, total=16e9, available=10e9)

    def disk_usage(self, path):
        self._n("disk_usage")
        return types.SimpleNamespace(percent=50.0, used=5e11, total=1e12)

    def boot_time(self):
        import time
        self._n("boot_time")
        return time.time() - 3600

    def sensors_temperatures(self):
        self._n("sensors_temperatures")
        return {}

    def disk_partitions(self, all=False):
        self._n("disk_partitions")
        return [types.SimpleNamespace(mountpoint="C:\\")]

    def net_if_stats(self):
        self._n("net_if_stats")
        return {"Ethernet": types.SimpleNamespace(isup=True)}

    def net_io_counters(self, pernic=False):
        self._n("net_io_counters")
        c = types.SimpleNamespace(bytes_sent=0, bytes_recv=0)
        return {"Ethernet": c} if pernic else c


@pytest.fixture(autouse=True)
def psutil_simulado(monkeypatch):
    """Nenhum teste chama o psutil real: core.sensors usa o falso e o real levanta erro."""
    import psutil
    import core.sensors as sensors
    fake = _FakePsutil()
    monkeypatch.setattr(sensors, "psutil", fake)

    def _proibido(nome):
        def _f(*a, **k):
            raise AssertionError(f"psutil real chamado em teste: {nome}")
        return _f

    for nome in ("cpu_percent", "cpu_freq", "virtual_memory", "disk_usage", "boot_time",
                 "sensors_temperatures", "disk_partitions", "net_if_stats",
                 "net_io_counters"):
        monkeypatch.setattr(psutil, nome, _proibido(nome), raising=False)
    return fake


@pytest.fixture
def themes_dir(tmp_path, monkeypatch):
    """Redireciona o catalogo de temas para um diretorio temporario."""
    import core.theme_store as store
    d = tmp_path / "themes"
    d.mkdir()
    monkeypatch.setattr(store, "THEMES_DIR", d)
    return d
