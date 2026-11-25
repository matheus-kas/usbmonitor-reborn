"""Coleta de sensores do sistema: CPU, RAM, GPU (NVIDIA), disco, rede, relogio."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import psutil

try:
    import warnings
    warnings.filterwarnings("ignore", message=".*pynvml package is deprecated.*")
    import pynvml
    pynvml.nvmlInit()
    _NVML_OK = True
    _NVML_HANDLE = pynvml.nvmlDeviceGetHandleByIndex(0) if pynvml.nvmlDeviceGetCount() else None
except Exception:
    _NVML_OK = False
    _NVML_HANDLE = None


@dataclass
class Reading:
    """Leitura instantanea de todos os sensores."""
    cpu_percent: float = 0.0
    cpu_freq_mhz: float = 0.0
    cpu_temp_c: float | None = None
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    gpu_name: str = ""
    gpu_percent: float | None = None
    gpu_temp_c: float | None = None
    gpu_mem_percent: float | None = None
    gpu_fan_percent: float | None = None
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    net_up_kbps: float = 0.0
    net_down_kbps: float = 0.0
    net_adapter: str = ""
    uptime: str = ""
    uptime_seconds: float = 0.0
    clock: str = ""
    date: str = ""
    extra: dict = field(default_factory=dict)


class SensorHub:
    """Fonte central de leituras. Mantem estado para calcular deltas de rede."""

    def __init__(self, disk_path: str = "C:\\", net_adapter: str | None = None):
        self.disk_path = disk_path
        self.net_adapter = net_adapter   # None = soma de todos os adaptadores
        self._last_net = self._net_counters()
        self._last_net_t = time.monotonic()
        psutil.cpu_percent(interval=None)  # primeira chamada zera o baseline

    def _net_counters(self):
        """Contadores do adaptador selecionado, ou a soma de todos."""
        if self.net_adapter:
            per = psutil.net_io_counters(pernic=True)
            if self.net_adapter in per:
                return per[self.net_adapter]
        return psutil.net_io_counters()

    def read(self) -> Reading:
        r = Reading()

        # CPU
        r.cpu_percent = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        r.cpu_freq_mhz = freq.current if freq else 0.0
        r.cpu_temp_c = self._cpu_temp()

        # RAM
        vm = psutil.virtual_memory()
        r.ram_percent = vm.percent
        r.ram_used_gb = (vm.total - vm.available) / 1e9
        r.ram_total_gb = vm.total / 1e9

        # GPU (NVIDIA via NVML)
        if _NVML_OK and _NVML_HANDLE is not None:
            self._read_gpu(r)

        # Disco
        du = psutil.disk_usage(self.disk_path)
        r.disk_percent = du.percent
        r.disk_used_gb = du.used / 1e9
        r.disk_total_gb = du.total / 1e9

        # Rede (delta desde a ultima leitura), do adaptador selecionado
        now = time.monotonic()
        net = self._net_counters()
        dt = max(now - self._last_net_t, 1e-6)
        # bytes_sent/recv sao monotonicos; protege contra troca de adaptador
        up = max(0, net.bytes_sent - self._last_net.bytes_sent)
        down = max(0, net.bytes_recv - self._last_net.bytes_recv)
        r.net_up_kbps = up / dt / 1024
        r.net_down_kbps = down / dt / 1024
        r.net_adapter = self.net_adapter or "Todos"
        self._last_net = net
        self._last_net_t = now

        # Uptime
        up_s = max(0.0, time.time() - psutil.boot_time())
        r.uptime_seconds = up_s
        r.uptime = _format_uptime(up_s)

        # Relogio
        now_dt = datetime.now()
        r.clock = now_dt.strftime("%H:%M:%S")
        r.date = now_dt.strftime("%d/%m/%Y")
        return r

    def set_net_adapter(self, adapter: str | None) -> None:
        """Troca o adaptador monitorado e reinicia o baseline do delta."""
        self.net_adapter = adapter or None
        self._last_net = self._net_counters()
        self._last_net_t = time.monotonic()

    def _read_gpu(self, r: Reading) -> None:
        try:
            name = pynvml.nvmlDeviceGetName(_NVML_HANDLE)
            r.gpu_name = name.decode() if isinstance(name, bytes) else name
            util = pynvml.nvmlDeviceGetUtilizationRates(_NVML_HANDLE)
            r.gpu_percent = float(util.gpu)
            mem = pynvml.nvmlDeviceGetMemoryInfo(_NVML_HANDLE)
            r.gpu_mem_percent = mem.used / mem.total * 100 if mem.total else None
            r.gpu_temp_c = float(pynvml.nvmlDeviceGetTemperature(
                _NVML_HANDLE, pynvml.NVML_TEMPERATURE_GPU))
            try:
                r.gpu_fan_percent = float(pynvml.nvmlDeviceGetFanSpeed(_NVML_HANDLE))
            except Exception:
                r.gpu_fan_percent = None
        except Exception:
            pass

    def _cpu_temp(self) -> float | None:
        """Temperatura de CPU. psutil nao expoe no Windows; retorna None.

        No Windows a fonte confiavel e LibreHardwareMonitor/AIDA64. Fica como
        ponto de extensao (ver core/lhm.py futuramente).
        """
        try:
            temps = psutil.sensors_temperatures()
            for key in ("coretemp", "k10temp", "cpu_thermal"):
                if key in temps and temps[key]:
                    return temps[key][0].current
        except (AttributeError, NotImplementedError):
            pass
        return None


def _format_uptime(seconds: float) -> str:
    s = int(seconds)
    days, s = divmod(s, 86400)
    hours, s = divmod(s, 3600)
    minutes, s = divmod(s, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{s:02d}"
    return f"{hours:02d}:{minutes:02d}:{s:02d}"


def available_disks() -> list[str]:
    return [p.mountpoint for p in psutil.disk_partitions(all=False)]


def available_adapters() -> list[str]:
    """Adaptadores de rede ativos, mais a opcao 'Todos'."""
    names = ["Todos"]
    try:
        stats = psutil.net_if_stats()
        for name, counters in psutil.net_io_counters(pernic=True).items():
            # ignora loopback e interfaces sem trafego nem status
            if name.lower().startswith("loopback"):
                continue
            names.append(name)
    except Exception:
        pass
    return names
