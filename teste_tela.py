"""Teste de conexao com a tela Turing 3.5". Desenha um frame de validacao."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from driver.turing_screen import TuringScreen, Orientation, find_com_port


def build_frame(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (12, 14, 28))
    d = ImageDraw.Draw(img)
    # moldura
    d.rectangle([2, 2, w - 3, h - 3], outline=(0, 200, 255), width=3)
    # faixas de cor para validar RGB565
    for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255),
                               (255, 255, 0), (255, 255, 255)]):
        d.rectangle([20, 40 + i * 24, 20 + 120, 40 + i * 24 + 18], fill=color)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 34)
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font_big = ImageFont.load_default()
        font = ImageFont.load_default()
    d.text((160, 45), "UsbMonitor", font=font_big, fill=(0, 230, 255))
    d.text((160, 85), "Reborn", font=font_big, fill=(255, 255, 255))
    d.text((20, 180), "Driver OK - tela conectada", font=font, fill=(0, 255, 120))
    d.text((20, 210), f"{w} x {h} RGB565", font=font, fill=(200, 200, 200))
    return img


def main() -> None:
    port = find_com_port()
    print(f"Porta detectada: {port}")
    with TuringScreen(orientation=Orientation.LANDSCAPE) as screen:
        screen.set_orientation(Orientation.LANDSCAPE)
        screen.set_brightness(100)
        screen.clear()
        frame = build_frame(screen.width, screen.height)
        screen.display_image(frame)
        print(f"Frame {screen.width}x{screen.height} enviado com sucesso.")


if __name__ == "__main__":
    main()
