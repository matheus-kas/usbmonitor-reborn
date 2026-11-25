"""Gera os temas prontos em themes/ e salva previews renderizados."""
from pathlib import Path
from core.theme import default_theme
from core.theme_presets import ALL_PRESETS
from core.renderer import Renderer
from core.sensors import Reading

ROOT = Path(__file__).parent
THEMES = ROOT / "themes"; THEMES.mkdir(exist_ok=True)
PREV = ROOT / "assets" / "previews"; PREV.mkdir(parents=True, exist_ok=True)

r = Reading(cpu_percent=37, gpu_percent=62, ram_percent=48, disk_percent=71,
            cpu_temp_c=54, gpu_temp_c=58, gpu_mem_percent=40, gpu_fan_percent=45,
            gpu_name="RTX 3060", net_down_kbps=1234, net_up_kbps=321,
            uptime="2d 05:12", clock="14:35", date="24/11/2026")

for t in [default_theme()] + [p() for p in ALL_PRESETS]:
    t.save(THEMES / f"{t.name}.json")
    img = Renderer(t).render(r)
    img.save(PREV / f"{t.name}.png")
    print(f"OK {t.name:14} {t.width}x{t.height}")
print("gerado.")
