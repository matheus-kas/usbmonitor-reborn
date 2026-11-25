"""Catalogo de temas: tema embutido + arquivos JSON em themes/."""
from __future__ import annotations

from pathlib import Path

from core.theme import Theme, default_theme

THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"
THEMES_DIR.mkdir(exist_ok=True)


def list_themes() -> list[Theme]:
    """Todos os temas disponiveis, com o padrao embutido primeiro."""
    themes: list[Theme] = []
    seen: set[str] = set()
    for path in sorted(THEMES_DIR.glob("*.json")):
        try:
            t = Theme.load(path)
            themes.append(t)
            seen.add(t.name)
        except Exception:
            continue
    if not any(t.name == "Padrao Escuro" for t in themes):
        themes.insert(0, default_theme())
    return themes


def load_theme(name: str) -> Theme:
    path = THEMES_DIR / f"{name}.json"
    if path.exists():
        return Theme.load(path)
    return default_theme()
