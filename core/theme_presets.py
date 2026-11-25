"""Temas prontos extras, gerados para a pasta themes/."""
from __future__ import annotations

from core.theme import Theme, Widget


def _ring_block(widgets, x, y, size, field, label, color, unit="%"):
    widgets.append(Widget(type="ring", x=x, y=y, width=size, height=10,
                          field=field, bg_color="#242842", fill_color=color))
    widgets.append(Widget(type="text", x=x + size // 2 - 22, y=y + size // 2 - 14,
                          field=field, unit=unit, fmt="{:.0f}", size=20,
                          bold=True, color="#FFFFFF"))
    widgets.append(Widget(type="label", x=x + size // 2 - 18, y=y + size + 4,
                          label=label, size=15, bold=True, color=color))


def gamer_neon() -> Theme:
    t = Theme(name="Gamer Neon", background_color="#0A0014")
    W = t.widgets
    W.append(Widget(type="clock", x=18, y=10, field="clock", size=40,
                    bold=True, color="#FF2E97"))
    W.append(Widget(type="text", x=300, y=22, field="date", size=18, color="#00F0FF"))
    _ring_block(W, 20, 70, 110, "cpu_percent", "CPU", "#00F0FF")
    _ring_block(W, 185, 70, 110, "gpu_percent", "GPU", "#B14CFF")
    _ring_block(W, 350, 70, 110, "ram_percent", "RAM", "#39FF14")
    W.append(Widget(type="label", x=20, y=235, label="GPU", size=15,
                    bold=True, color="#B14CFF"))
    W.append(Widget(type="text", x=70, y=235, field="gpu_temp_c", unit=" C",
                    fmt="{:.0f}", size=15, color="#FFFFFF"))
    W.append(Widget(type="label", x=160, y=235, label="DISCO", size=15,
                    bold=True, color="#39FF14"))
    W.append(Widget(type="bar", x=230, y=238, field="disk_percent",
                    width=220, height=12, bg_color="#242842", fill_color="#39FF14"))
    W.append(Widget(type="label", x=20, y=268, label="REDE", size=14,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=75, y=268, field="net_down_kbps", label="v ",
                    unit=" KB/s", fmt="{:.0f}", size=14, color="#00F0FF"))
    W.append(Widget(type="text", x=230, y=268, field="net_up_kbps", label="^ ",
                    unit=" KB/s", fmt="{:.0f}", size=14, color="#FF2E97"))
    W.append(Widget(type="label", x=20, y=295, label="UP", size=14,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=60, y=295, field="uptime", size=14, color="#FFD166"))
    return t


def minimal_light() -> Theme:
    t = Theme(name="Minimal Claro", background_color="#F2F3F7")
    W = t.widgets
    W.append(Widget(type="clock", x=20, y=16, field="clock", size=48,
                    bold=True, color="#1A1C24"))
    W.append(Widget(type="text", x=320, y=34, field="date", size=18, color="#6A7080"))

    def row(y, label, fld, color):
        W.append(Widget(type="label", x=24, y=y, label=label, size=18,
                        bold=True, color="#1A1C24"))
        W.append(Widget(type="text", x=150, y=y, field=fld, unit="%",
                        fmt="{:.0f}", size=18, color=color))
        W.append(Widget(type="bar", x=210, y=y + 3, field=fld, width=240,
                        height=12, bg_color="#D7DAE3", fill_color=color))
    row(95, "CPU", "cpu_percent", "#2563EB")
    row(135, "GPU", "gpu_percent", "#16A34A")
    row(175, "RAM", "ram_percent", "#D97706")
    row(215, "DISCO", "disk_percent", "#DB2777")
    W.append(Widget(type="label", x=24, y=258, label="REDE", size=15,
                    bold=True, color="#1A1C24"))
    W.append(Widget(type="text", x=90, y=258, field="net_down_kbps", label="DL ",
                    unit=" KB/s", fmt="{:.0f}", size=14, color="#2563EB"))
    W.append(Widget(type="text", x=250, y=258, field="net_up_kbps", label="UL ",
                    unit=" KB/s", fmt="{:.0f}", size=14, color="#DB2777"))
    W.append(Widget(type="label", x=24, y=288, label="UPTIME", size=15,
                    bold=True, color="#1A1C24"))
    W.append(Widget(type="text", x=120, y=288, field="uptime", size=15, color="#6A7080"))
    return t


def focus_gpu() -> Theme:
    t = Theme(name="Foco GPU", background_color="#06130C")
    W = t.widgets
    W.append(Widget(type="text", x=20, y=14, field="gpu_name",
                    size=18, bold=True, color="#7CFC00"))
    W.append(Widget(type="ring", x=140, y=55, width=190, height=16,
                    field="gpu_percent", bg_color="#123020", fill_color="#7CFC00"))
    W.append(Widget(type="text", x=200, y=120, field="gpu_percent", unit="%",
                    fmt="{:.0f}", size=52, bold=True, color="#FFFFFF"))
    W.append(Widget(type="label", x=205, y=185, label="GPU", size=18,
                    bold=True, color="#7CFC00"))
    W.append(Widget(type="label", x=30, y=235, label="TEMP", size=15,
                    bold=True, color="#AAAAAA"))
    W.append(Widget(type="text", x=95, y=235, field="gpu_temp_c", unit=" C",
                    fmt="{:.0f}", size=15, color="#FF7043"))
    W.append(Widget(type="label", x=170, y=235, label="VRAM", size=15,
                    bold=True, color="#AAAAAA"))
    W.append(Widget(type="text", x=240, y=235, field="gpu_mem_percent", unit="%",
                    fmt="{:.0f}", size=15, color="#4FC3F7"))
    W.append(Widget(type="label", x=330, y=235, label="FAN", size=15,
                    bold=True, color="#AAAAAA"))
    W.append(Widget(type="text", x=385, y=235, field="gpu_fan_percent", unit="%",
                    fmt="{:.0f}", size=15, color="#FFD166"))
    W.append(Widget(type="clock", x=20, y=278, field="clock", size=22,
                    bold=True, color="#7CFC00"))
    W.append(Widget(type="text", x=330, y=283, field="uptime", size=16, color="#AAAAAA"))
    return t


def vertical_retrato() -> Theme:
    """Tema para orientacao retrato (320x480)."""
    t = Theme(name="Retrato", width=320, height=480, background_color="#0C0E1C")
    W = t.widgets
    W.append(Widget(type="clock", x=30, y=20, field="clock", size=40,
                    bold=True, color="#00E6FF"))
    W.append(Widget(type="text", x=70, y=70, field="date", size=18, color="#AAAAAA"))

    def block(y, label, fld, color):
        W.append(Widget(type="label", x=30, y=y, label=label, size=20,
                        bold=True, color="#FFFFFF"))
        W.append(Widget(type="text", x=200, y=y, field=fld, unit="%",
                        fmt="{:.0f}", size=20, color=color))
        W.append(Widget(type="bar", x=30, y=y + 30, field=fld, width=260,
                        height=16, bg_color="#242842", fill_color=color))
    block(120, "CPU", "cpu_percent", "#00C8FF")
    block(185, "GPU", "gpu_percent", "#7CFC00")
    block(250, "RAM", "ram_percent", "#FFB000")
    block(315, "DISCO", "disk_percent", "#FF5C8A")
    W.append(Widget(type="label", x=30, y=385, label="REDE", size=17,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=30, y=410, field="net_down_kbps", label="DL ",
                    unit=" KB/s", fmt="{:.0f}", size=15, color="#8FD3FF"))
    W.append(Widget(type="text", x=170, y=410, field="net_up_kbps", label="UL ",
                    unit=" KB/s", fmt="{:.0f}", size=15, color="#FF9E9E"))
    W.append(Widget(type="label", x=30, y=440, label="UPTIME", size=17,
                    bold=True, color="#FFFFFF"))
    W.append(Widget(type="text", x=130, y=440, field="uptime", size=16, color="#C9A0FF"))
    return t


def _val(x, y, field, color, size=22, unit="%", fmt="{:.0f}", bold=True):
    return Widget(type="text", x=x, y=y, field=field, unit=unit, fmt=fmt,
                  size=size, bold=bold, color=color, align="center")


def gradient() -> Theme:
    """Fundo com 5 aneis (extraido do app antigo). Valores no centro de cada anel."""
    t = Theme(name="Gradient", background_color="#FFFFFF",
              background_image="assets/backgrounds/Gradient_0_480x320.png")
    W = t.widgets
    # centros aproximados dos aneis do fundo
    W.append(_val(85, 64, "cpu_percent", "#E0218A"))
    W.append(Widget(type="label", x=85, y=140, label="CPU", size=14, bold=True,
                    color="#7A1FA2", align="center"))
    W.append(_val(395, 64, "gpu_percent", "#E0218A"))
    W.append(Widget(type="label", x=395, y=140, label="GPU", size=14, bold=True,
                    color="#7A1FA2", align="center"))
    W.append(_val(240, 138, "ram_percent", "#E0218A", size=18))
    W.append(Widget(type="label", x=240, y=188, label="RAM", size=12, bold=True,
                    color="#7A1FA2", align="center"))
    W.append(_val(85, 224, "disk_percent", "#E0218A"))
    W.append(Widget(type="label", x=85, y=300, label="DISCO", size=14, bold=True,
                    color="#7A1FA2", align="center"))
    W.append(_val(395, 210, "cpu_temp_c", "#E0218A", unit="C", size=18))
    W.append(Widget(type="text", x=395, y=240, field="clock", size=18, bold=True,
                    color="#7A1FA2", align="center"))
    W.append(Widget(type="text", x=395, y=300, field="uptime", size=13,
                    color="#7A1FA2", align="center"))
    return t


def magic_blue() -> Theme:
    """HUD futurista azul (extraido do app antigo)."""
    t = Theme(name="MagicBlue", background_color="#04121F",
              background_image="assets/backgrounds/LandscapeMagicBlue_0_480x320.png")
    W = t.widgets
    # NETWORK (topo esquerdo)
    # a arte ja traz o "M" da unidade: sem unit, valor alinhado a direita antes dele
    for y, fld in ((59, "net_up_kbps"), (81, "net_down_kbps")):
        w = _val(106, y, fld, "#59E0FF", unit="", fmt="{:.0f}", size=18, bold=True)
        w.align = "right"
        W.append(w)
    # caixas brancas (CPU nome/uso e GPU uso)
    W.append(_val(50, 130, "cpu_percent", "#04121F", unit="%", size=20))
    W.append(_val(430, 130, "gpu_percent", "#04121F", unit="%", size=20))
    # CPU TEMP (gauge esquerdo central)
    W.append(_val(50, 183, "cpu_temp_c", "#FFFFFF", unit="C", size=16))
    # RAM STATUS (barra inferior esquerda)
    W.append(_val(95, 250, "ram_percent", "#59E0FF", unit="%", size=18))
    # GPU RAM (barra inferior direita)
    W.append(_val(430, 250, "gpu_mem_percent", "#FF4FA3", unit="%", size=18))
    # relogio discreto no centro inferior
    W.append(Widget(type="clock", x=240, y=300, field="clock", size=14,
                    bold=True, color="#8FE8FF", align="center"))
    return t


def nzxt() -> Theme:
    """Cards translucidos sobre floresta (extraido do app antigo). Grade 2x3."""
    t = Theme(name="NZXT", background_color="#1C3B2E",
              background_image="assets/backgrounds/NZXT_BLUR_0_480x320.png")
    W = t.widgets
    # linha 1: CPU (card esq) | GPU (card dir)
    W.append(_val(135, 50, "cpu_percent", "#FFFFFF", unit="%", size=22))
    W.append(_val(315, 50, "gpu_percent", "#FFFFFF", unit="%", size=22))
    # linha 2: RAM (card esq) | SSD/disco (card dir)
    # a arte do card de RAM ja traz o "%": sem unit, valor alinhado a direita antes dele
    ram = _val(112, 150, "ram_percent", "#FFFFFF", unit="", size=22)
    ram.align = "right"
    W.append(ram)
    W.append(_val(318, 150, "disk_percent", "#FFFFFF", unit="%", size=22))
    # linha 3: UP (card esq) | DOWN (card dir)
    W.append(_val(118, 250, "net_up_kbps", "#FFFFFF", unit=" KB/s", fmt="{:.0f}",
                  size=18))
    W.append(_val(300, 250, "net_down_kbps", "#FFFFFF", unit=" KB/s", fmt="{:.0f}",
                  size=18))
    # relogio e uptime no canto inferior direito livre
    W.append(Widget(type="clock", x=430, y=120, field="clock", size=16,
                    bold=True, color="#FFFFFF", align="center"))
    W.append(Widget(type="text", x=430, y=145, field="uptime", size=12,
                    color="#E8F5E9", align="center"))
    return t


ALL_PRESETS = [gamer_neon, minimal_light, focus_gpu, vertical_retrato,
               gradient, magic_blue, nzxt]
