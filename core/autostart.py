"""Iniciar com o Windows via chave de registro HKCU\\...\\Run."""
from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "UsbMonitorReborn"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command() -> str:
    """Comando que inicia o app com o pythonw do venv (sem console)."""
    root = Path(__file__).resolve().parent.parent
    pythonw = root / ".venv" / "Scripts" / "pythonw.exe"
    exe = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{exe}" "{root / "app.py"}"'


def is_enabled() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
        return True
    except OSError:
        return False
    except Exception:
        return False


def set_enabled(enabled: bool) -> None:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                        winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass
