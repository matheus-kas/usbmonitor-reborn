"""Roda o motor direto na tela, sem UI, por N segundos. Teste de integracao."""
from __future__ import annotations

import sys
import time

from core.engine import DisplayEngine
from core.theme import default_theme
from driver.turing_screen import Orientation


def main() -> None:
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    theme = default_theme()
    engine = DisplayEngine(theme, fps=1.0, orientation=Orientation.LANDSCAPE)
    print("Conectando a tela...")
    engine.connect()
    print("Conectado. Enviando stats reais por", seconds, "segundos.")
    engine.start()
    try:
        time.sleep(seconds)
    finally:
        engine.stop()
    print("Encerrado.")


if __name__ == "__main__":
    main()
