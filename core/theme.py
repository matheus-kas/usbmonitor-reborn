"""Modelo de tema: formato JSON editavel com widgets posicionaveis.

Um tema descreve o fundo e uma lista de widgets. Cada widget tem tipo,
posicao, fonte, cor e qual campo de sensor exibe. Muito mais simples e
editavel que o BinaryFormatter do app original.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Widget:
    type: str                      # "text" | "bar" | "ring" | "clock" | "label"
    x: int = 0
    y: int = 0
    # fonte de dado: nome de campo do Reading (ex.: "cpu_percent")
    field: str = ""
    label: str = ""                # rotulo fixo opcional
    unit: str = ""                 # sufixo (ex.: "%", "C", "MB/s")
    fmt: str = "{:.0f}"            # formato numerico
    font: str = "Segoe UI"
    size: int = 20
    bold: bool = False
    color: str = "#FFFFFF"
    align: str = "left"            # "left" | "center" | "right"
    # para bar/ring
    width: int = 120
    height: int = 14
    min_value: float = 0.0
    max_value: float = 100.0
    bg_color: str = "#333333"
    fill_color: str = "#00C8FF"


@dataclass
class Theme:
    name: str = "Novo tema"
    width: int = 480
    height: int = 320
    background_color: str = "#0C0E1C"
    background_image: str | None = None   # caminho para PNG de fundo
    widgets: list[Widget] = field(default_factory=list)

    # ---- serializacao -------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Theme":
        widgets = [Widget(**w) for w in d.get("widgets", [])]
        base = {k: v for k, v in d.items() if k != "widgets"}
        return cls(widgets=widgets, **base)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
                              encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Theme":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def default_theme() -> Theme:
    """Tema de exemplo com CPU, GPU, RAM, disco, rede e relogio."""
    t = Theme(name="Padrao Escuro")
    W = t.widgets
    # Relogio grande no topo
    W.append(Widget(type="clock", x=20, y=12, field="clock",
                    font="Segoe UI", size=44, bold=True, color="#00E6FF"))
    W.append(Widget(type="text", x=300, y=24, field="date",
                    size=20, color="#AAAAAA"))

    def block(y, label, field_val, field_bar, color):
        W.append(Widget(type="label", x=20, y=y, label=label, size=18,
                        bold=True, color="#FFFFFF"))
        W.append(Widget(type="text", x=180, y=y, field=field_val, unit="%",
                        size=18, color=color))
        W.append(Widget(type="bar", x=240, y=y + 2, field=field_bar,
                        width=210, height=14, fill_color=color))

    block(90, "CPU", "cpu_percent", "cpu_percent", "#00C8FF")
    block(130, "GPU", "gpu_percent", "gpu_percent", "#7CFC00")
    block(170, "RAM", "ram_percent", "ram_percent", "#FFB000")
    block(210, "DISCO", "disk_percent", "disk_percent", "#FF5C8A")

    # Rede
    W.append(Widget(type="label", x=20, y=250, label="REDE", size=16,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=90, y=250, field="net_down_kbps",
                    label="DL ", unit=" KB/s", fmt="{:.0f}", size=15, color="#8FD3FF"))
    W.append(Widget(type="text", x=250, y=250, field="net_up_kbps",
                    label="UL ", unit=" KB/s", fmt="{:.0f}", size=15, color="#FF9E9E"))
    # Uptime
    W.append(Widget(type="label", x=20, y=285, label="UPTIME", size=16,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=110, y=285, field="uptime",
                    size=16, color="#C9A0FF"))
    return t
