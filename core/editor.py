"""Operacoes puras de edicao de tema (sem UI): widgets, propriedades e arquivos.

Regra do projeto: nome do tema = nome do arquivo (themes/<nome>.json).
Escrita em disco so por `Theme.save`; os diretorios vem de `theme_store.THEMES_DIR`
e de `root` (raiz do projeto), para que testes usem diretorios temporarios.
"""
from __future__ import annotations

import copy
import re
import shutil
from dataclasses import fields
from pathlib import Path

from core import theme_store as store
from core.renderer import PROJECT_ROOT
from core.sensors import Reading
from core.theme import Theme, Widget

WIDGET_TYPES = ("text", "label", "clock", "bar", "ring")
ALIGNS = ("left", "center", "right")
# campos de sensor oferecidos no painel (campos de Reading, sem o dicionario extra)
SENSOR_FIELDS = tuple(f.name for f in fields(Reading) if f.name != "extra")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}
_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_BAD_NAME_RE = re.compile(r'[\\/:*?"<>|]')


class EditorError(ValueError):
    """Operacao recusada; a mensagem e mostrada ao usuario."""


# ---- widgets ------------------------------------------------------------
def _check_index(theme: Theme, idx: int) -> None:
    if not 0 <= idx < len(theme.widgets):
        raise EditorError(f"Widget {idx} nao existe.")


def move_widget(theme: Theme, idx: int, x: int, y: int) -> None:
    """Move o widget; mantem a posicao dentro do quadro do tema."""
    _check_index(theme, idx)
    w = theme.widgets[idx]
    w.x = max(0, min(int(x), theme.width))
    w.y = max(0, min(int(y), theme.height))


def add_widget(theme: Theme, wtype: str, x: int = 20, y: int = 20, **props) -> int:
    if wtype not in WIDGET_TYPES:
        raise EditorError(f"Tipo de widget invalido: {wtype!r}.")
    w = Widget(type=wtype, x=x, y=y)
    if wtype == "label":
        w.label = "Rotulo"
    elif wtype in ("text", "bar", "ring"):
        w.field = "cpu_percent"
    elif wtype == "clock":
        w.field = "clock"
    theme.widgets.append(w)
    idx = len(theme.widgets) - 1
    try:
        for k, v in props.items():
            set_property(theme, idx, k, v)
    except EditorError:
        del theme.widgets[idx]
        raise
    return idx


def remove_widget(theme: Theme, idx: int) -> None:
    _check_index(theme, idx)
    del theme.widgets[idx]


def duplicate_widget(theme: Theme, idx: int, offset: int = 10) -> int:
    """Duplica logo apos o original, deslocado; devolve o indice da copia."""
    _check_index(theme, idx)
    dup = copy.deepcopy(theme.widgets[idx])
    dup.x += offset
    dup.y += offset
    theme.widgets.insert(idx + 1, dup)
    return idx + 1


# ---- propriedades -------------------------------------------------------
_INT_MIN = {"x": 0, "y": 0, "size": 1, "width": 1, "height": 1}
_FLOATS = ("min_value", "max_value")
_COLORS = ("color", "bg_color", "fill_color")


def validate_property(name: str, value):
    """Devolve o valor convertido ou levanta EditorError. Nao altera nada."""
    valid = {f.name for f in fields(Widget)}
    if name not in valid:
        raise EditorError(f"Propriedade desconhecida: {name!r}.")
    if name in _INT_MIN:
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise EditorError(f"{name}: informe um numero inteiro.") from None
        if v < _INT_MIN[name]:
            raise EditorError(f"{name}: minimo {_INT_MIN[name]}.")
        return v
    if name in _FLOATS:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise EditorError(f"{name}: informe um numero.") from None
    if name in _COLORS:
        if not isinstance(value, str) or not _COLOR_RE.match(value):
            raise EditorError(f"{name}: cor invalida, use #RRGGBB.")
        return value.upper()
    if name == "type":
        if value not in WIDGET_TYPES:
            raise EditorError(f"Tipo de widget invalido: {value!r}.")
        return value
    if name == "align":
        if value not in ALIGNS:
            raise EditorError("align: use left, center ou right.")
        return value
    if name == "font":
        if not isinstance(value, str) or not value.strip():
            raise EditorError("font: nao pode ser vazia.")
        return value.strip()
    if name == "bold":
        return bool(value)
    if name == "fmt":
        if not isinstance(value, str):
            raise EditorError("fmt: informe um texto.")
        try:
            value.format(1.0)
        except (ValueError, KeyError, IndexError):
            raise EditorError("fmt: formato invalido, ex.: {:.0f}.") from None
        return value
    if name == "field":
        if value and value not in SENSOR_FIELDS:
            raise EditorError(f"field: sensor desconhecido {value!r}.")
        return value
    return "" if value is None else str(value)   # label, unit


def set_property(theme: Theme, idx: int, name: str, value) -> None:
    """Valida e aplica; valor invalido nao altera o tema."""
    _check_index(theme, idx)
    setattr(theme.widgets[idx], name, validate_property(name, value))


# ---- temas: nome, arquivo -----------------------------------------------
def validate_theme_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise EditorError("O nome do tema nao pode ser vazio.")
    if _BAD_NAME_RE.search(n) or n in (".", "..") or n.endswith("."):
        raise EditorError("O nome do tema tem caracteres invalidos.")
    return n


def theme_path(name: str) -> Path:
    return store.THEMES_DIR / f"{name}.json"


def new_theme(name: str, base: Theme | None = None) -> Theme:
    """Tema novo em memoria (copia de `base` ou vazio). Nao grava; recusa nome existente."""
    n = validate_theme_name(name)
    if theme_path(n).exists():
        raise EditorError(f"Ja existe um tema chamado {n!r}.")
    t = copy.deepcopy(base) if base is not None else Theme()
    t.name = n
    return t


def save_theme(theme: Theme, overwrite: bool = False) -> Path:
    """Grava themes/<nome>.json. `overwrite` so para salvar o tema que ja se esta editando."""
    n = validate_theme_name(theme.name)
    theme.name = n
    path = theme_path(n)
    if path.exists() and not overwrite:
        raise EditorError(f"Ja existe um tema chamado {n!r}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    theme.save(path)
    return path


def rename_theme(theme: Theme, new_name: str) -> Path:
    """Troca nome e arquivo juntos. Recusa nome existente; nao sobrescreve outro tema."""
    n = validate_theme_name(new_name)
    old_name = theme.name
    old = theme_path(old_name)
    if n != old_name and theme_path(n).exists():
        raise EditorError(f"Ja existe um tema chamado {n!r}.")
    theme.name = n
    path = save_theme(theme, overwrite=True)
    if old.exists() and old != path:
        old.unlink()
    return path


# ---- fundo --------------------------------------------------------------
def import_background(theme: Theme, src: str | Path, root: Path | None = None) -> str:
    """Copia a imagem para <root>/assets/backgrounds e grava o caminho relativo no tema."""
    src = Path(src)
    if src.suffix.lower() not in IMAGE_EXTS or not src.is_file():
        raise EditorError("Escolha um arquivo de imagem (png, jpg ou bmp).")
    root = Path(root) if root else PROJECT_ROOT
    dest_dir = root / "assets" / "backgrounds"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists() and dest.resolve() != src.resolve():
        if dest.read_bytes() != src.read_bytes():
            i = 2
            while (dest_dir / f"{src.stem}_{i}{src.suffix}").exists():
                i += 1
            dest = dest_dir / f"{src.stem}_{i}{src.suffix}"
    if not dest.exists():
        shutil.copyfile(src, dest)
    rel = f"assets/backgrounds/{dest.name}"
    theme.background_image = rel
    return rel


def clear_background(theme: Theme) -> None:
    theme.background_image = None


def set_background_color(theme: Theme, color: str) -> None:
    if not _COLOR_RE.match(color or ""):
        raise EditorError("Cor invalida, use #RRGGBB.")
    theme.background_color = color.upper()
