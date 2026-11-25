"""Catalogo de temas: tema embutido + arquivos JSON em themes/.

Regra do projeto: nome do tema = nome do arquivo (themes/<nome>.json). Ao carregar,
o nome do arquivo manda; o campo `name` do JSON e ignorado.
"""
from __future__ import annotations

import re
from pathlib import Path

from core.theme import Theme, default_theme

THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"
THEMES_DIR.mkdir(exist_ok=True)

_BAD_NAME_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL",
             *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def is_safe_name(name: str) -> bool:
    """Nome de tema que e um nome de arquivo simples: sem caminho e sem nome reservado do Windows."""
    n = (name or "").strip()
    if not n or n != name or _BAD_NAME_RE.search(n) or n in (".", "..") or n.endswith("."):
        return False
    return n.split(".")[0].upper() not in _RESERVED


def _load_named(path: Path) -> Theme:
    """Carrega o arquivo e forca nome = nome do arquivo."""
    t = Theme.load(path)
    t.name = path.stem
    return t


def list_themes() -> list[Theme]:
    """Todos os temas disponiveis, com o padrao embutido primeiro."""
    themes: list[Theme] = []
    for path in sorted(THEMES_DIR.glob("*.json")):
        try:
            themes.append(_load_named(path))
        except Exception:
            continue
    if not any(t.name == "Padrao Escuro" for t in themes):
        themes.insert(0, default_theme())
    return themes


def load_theme(name: str) -> Theme:
    if not is_safe_name(name):
        return default_theme()
    path = THEMES_DIR / f"{name}.json"
    if path.exists():
        return _load_named(path)
    return default_theme()
