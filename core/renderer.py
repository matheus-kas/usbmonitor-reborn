"""Renderiza um Theme + Reading numa imagem PIL pronta para a tela."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.theme import Theme, Widget
from core.sensors import Reading

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_bg(path: str) -> Path:
    """Caminho do fundo; so aceita arquivos dentro de assets/ do projeto."""
    p = (PROJECT_ROOT / path).resolve()      # caminho absoluto no JSON substitui a base
    if not p.is_relative_to((PROJECT_ROOT / "assets").resolve()):
        raise ValueError("fundo fora de assets/")
    return p


@lru_cache(maxsize=64)
def _load_font(name: str, size: int, bold: bool) -> ImageFont.FreeTypeFont:
    # mapeia nomes comuns para arquivos do Windows
    candidates = []
    base = name.lower().replace(" ", "")
    if "segoe" in base:
        candidates = ["segoeuib.ttf" if bold else "segoeui.ttf"]
    elif "arial" in base:
        candidates = ["arialbd.ttf" if bold else "arial.ttf"]
    elif "consolas" in base or "mono" in base:
        candidates = ["consolab.ttf" if bold else "consola.ttf"]
    candidates += ["arialbd.ttf" if bold else "arial.ttf", "segoeui.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _get_value(reading: Reading, field: str):
    return getattr(reading, field, reading.extra.get(field)) if field else None


def _anchor(align: str) -> str:
    # anchor do PIL: primeiro char = horizontal, segundo = vertical (topo)
    return {"left": "la", "center": "ma", "right": "ra"}.get(align, "la")


class Renderer:
    def __init__(self, theme: Theme):
        self.theme = theme
        self._bg_cache: Image.Image | None = None

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self._bg_cache = None

    def _background(self) -> Image.Image:
        if self._bg_cache is not None:
            return self._bg_cache.copy()
        t = self.theme
        img = Image.new("RGB", (t.width, t.height), t.background_color)
        if t.background_image:
            try:
                bg = Image.open(_resolve_bg(t.background_image))
                bg = bg.resize((t.width, t.height))
                if bg.mode in ("RGBA", "LA", "P"):
                    bg = bg.convert("RGBA")
                    img = img.convert("RGBA")
                    img = Image.alpha_composite(img, bg).convert("RGB")
                else:
                    img.paste(bg.convert("RGB"), (0, 0))
            except Exception:
                pass
        self._bg_cache = img
        return img.copy()

    def render(self, reading: Reading) -> Image.Image:
        img = self._background()
        draw = ImageDraw.Draw(img)
        for w in self.theme.widgets:
            self._draw_widget(draw, w, reading)
        return img

    def _draw_widget(self, draw: ImageDraw.ImageDraw, w: Widget, reading: Reading) -> None:
        if w.type == "label":
            font = _load_font(w.font, w.size, w.bold)
            draw.text((w.x, w.y), w.label, font=font, fill=w.color,
                      anchor=_anchor(w.align))
            return

        if w.type in ("text", "clock"):
            font = _load_font(w.font, w.size, w.bold)
            val = _get_value(reading, w.field)
            if val is None:
                text = w.label + "--" + w.unit
            elif isinstance(val, str):
                text = w.label + val + w.unit
            else:
                try:
                    text = w.label + w.fmt.format(val) + w.unit
                except (ValueError, KeyError):
                    text = w.label + str(val) + w.unit
            draw.text((w.x, w.y), text, font=font, fill=w.color,
                      anchor=_anchor(w.align))
            return

        if w.type == "bar":
            val = _get_value(reading, w.field)
            frac = 0.0 if val is None else self._frac(float(val), w)
            draw.rectangle([w.x, w.y, w.x + w.width, w.y + w.height],
                           fill=w.bg_color)
            fill_w = int(w.width * frac)
            if fill_w > 0:
                draw.rectangle([w.x, w.y, w.x + fill_w, w.y + w.height],
                               fill=w.fill_color)
            return

        if w.type == "ring":
            val = _get_value(reading, w.field)
            frac = 0.0 if val is None else self._frac(float(val), w)
            box = [w.x, w.y, w.x + w.width, w.y + w.width]
            draw.arc(box, 0, 360, fill=w.bg_color, width=max(4, w.height))
            draw.arc(box, -90, -90 + int(360 * frac),
                     fill=w.fill_color, width=max(4, w.height))
            return

    @staticmethod
    def _frac(val: float, w: Widget) -> float:
        rng = (w.max_value - w.min_value) or 1.0
        return max(0.0, min(1.0, (val - w.min_value) / rng))

    def widget_bbox(self, w: Widget, reading: Reading) -> tuple[int, int, int, int]:
        """Retangulo (x, y, largura, altura) ocupado por um widget, para o editor."""
        if w.type in ("bar",):
            return (w.x, w.y, w.width, w.height)
        if w.type == "ring":
            return (w.x, w.y, w.width, w.width)
        # text / label / clock: mede o texto com a fonte e o alinhamento
        font = _load_font(w.font, w.size, w.bold)
        if w.type == "label":
            text = w.label
        else:
            val = _get_value(reading, w.field)
            if val is None:
                text = w.label + "--" + w.unit
            elif isinstance(val, str):
                text = w.label + val + w.unit
            else:
                try:
                    text = w.label + w.fmt.format(val) + w.unit
                except (ValueError, KeyError):
                    text = w.label + str(val) + w.unit
        dummy = Image.new("RGB", (1, 1))
        d = ImageDraw.Draw(dummy)
        l, t, r, b = d.textbbox((w.x, w.y), text or " ", font=font,
                                anchor=_anchor(w.align))
        return (int(l), int(t), max(4, int(r - l)), max(4, int(b - t)))
