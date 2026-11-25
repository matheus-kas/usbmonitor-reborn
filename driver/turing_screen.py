"""
Driver para telas Turing Smart Screen Revisao A (3.5", 320x480).

Hardware identificado: USB\\VID_1A86&PID_5722\\USB35INCHIPSV2 (porta serial CDC).
Protocolo reimplementado a partir da especificacao publica (mathoudebine/
turing-smart-screen-python, GPL-3.0). Esta e uma reimplementacao limpa para
uso proprio com a tela que o usuario possui.

Protocolo Rev A:
- Serial 115200 8N1, controle de fluxo RTS/CTS.
- Comando = pacote de 6 bytes; o byte do comando e o ultimo (indice 5).
- Coordenadas x, y, ex, ey empacotadas em bits (10 bits cada) nos bytes 0..4.
- Bitmap enviado em RGB565 little-endian, linha a linha, apos o cabecalho.
"""
from __future__ import annotations

import time
from enum import IntEnum

import serial
import serial.tools.list_ports
from PIL import Image


SERIAL_ID = "USB35INCHIPSV2"
VID = 0x1A86
PID = 0x5722

# Dimensoes nativas do painel (em modo retrato).
NATIVE_WIDTH = 320
NATIVE_HEIGHT = 480


class Command(IntEnum):
    RESET = 101
    CLEAR = 102
    TO_BLACK = 103
    SCREEN_OFF = 108
    SCREEN_ON = 109
    SET_BRIGHTNESS = 110
    SET_ORIENTATION = 121
    DISPLAY_BITMAP = 197


class Orientation(IntEnum):
    PORTRAIT = 0
    REVERSE_PORTRAIT = 1
    LANDSCAPE = 2
    REVERSE_LANDSCAPE = 3


def find_com_port() -> str | None:
    """Localiza a porta COM da tela pelo serial string ou VID/PID."""
    for port in serial.tools.list_ports.comports():
        if port.serial_number == SERIAL_ID:
            return port.device
        if port.vid == VID and port.pid == PID:
            return port.device
    return None


def image_to_rgb565(img: Image.Image) -> bytes:
    """Converte uma imagem PIL para RGB565 little-endian, linha a linha."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    out = bytearray()
    for r, g, b in img.getdata():
        value = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out.append(value & 0xFF)          # byte baixo primeiro (little-endian)
        out.append((value >> 8) & 0xFF)
    return bytes(out)


class TuringScreen:
    def __init__(self, com_port: str | None = None,
                 orientation: Orientation = Orientation.LANDSCAPE):
        self.com_port = com_port or find_com_port()
        if not self.com_port:
            raise RuntimeError("Tela Turing 3.5\" nao encontrada em nenhuma porta COM.")
        self.orientation = orientation
        self.serial: serial.Serial | None = None

    # ---- ciclo de vida da conexao -------------------------------------
    def open(self) -> None:
        self.serial = serial.Serial(self.com_port, 115200, timeout=1, rtscts=True)
        self.screen_on()

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.serial = None

    def __enter__(self) -> "TuringScreen":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- dimensoes conforme a orientacao ------------------------------
    @property
    def width(self) -> int:
        if self.orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT):
            return NATIVE_WIDTH
        return NATIVE_HEIGHT

    @property
    def height(self) -> int:
        if self.orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT):
            return NATIVE_HEIGHT
        return NATIVE_WIDTH

    # ---- montagem de pacotes ------------------------------------------
    def _send_command(self, cmd: Command, x: int = 0, y: int = 0,
                       ex: int = 0, ey: int = 0) -> None:
        buf = bytearray(6)
        buf[0] = x >> 2
        buf[1] = ((x & 3) << 6) + (y >> 4)
        buf[2] = ((y & 15) << 4) + (ex >> 6)
        buf[3] = ((ex & 63) << 2) + (ey >> 8)
        buf[4] = ey & 0xFF
        buf[5] = int(cmd)
        assert self.serial is not None
        self.serial.write(bytes(buf))
        self.serial.flush()

    # ---- comandos de alto nivel ---------------------------------------
    def reset(self) -> None:
        self._send_command(Command.RESET)
        self.close()
        time.sleep(5)        # a tela reinicia; aguarda e reabre
        self.open()

    def clear(self) -> None:
        self._send_command(Command.CLEAR)

    def screen_on(self) -> None:
        self._send_command(Command.SCREEN_ON)

    def screen_off(self) -> None:
        self._send_command(Command.SCREEN_OFF)

    def set_brightness(self, percent: int) -> None:
        """percent 0..100 (100 = mais claro)."""
        percent = max(0, min(100, percent))
        level_absolute = int(255 - (percent / 100) * 255)  # 0 claro, 255 escuro
        self._send_command(Command.SET_BRIGHTNESS, level_absolute, 0, 0, 0)

    def set_orientation(self, orientation: Orientation) -> None:
        self.orientation = orientation
        buf = bytearray(16)
        buf[5] = int(Command.SET_ORIENTATION)
        buf[6] = int(orientation) + 100
        buf[7] = self.width >> 8
        buf[8] = self.width & 0xFF
        buf[9] = self.height >> 8
        buf[10] = self.height & 0xFF
        assert self.serial is not None
        self.serial.write(bytes(buf))

    def fill(self, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        """Pinta a tela inteira com uma cor solida (frame real, nao o CLEAR)."""
        self.display_image(Image.new("RGB", (self.width, self.height), color))

    def clear_black(self) -> None:
        """Limpa de verdade: preenche com preto para eliminar residuos/ghosting."""
        self.fill((0, 0, 0))

    def deghost(self) -> None:
        """Dissipa afterimage do painel IPS alternando branco e preto."""
        self.fill((255, 255, 255))
        time.sleep(0.4)
        self.fill((0, 0, 0))

    def display_image(self, img: Image.Image, x: int = 0, y: int = 0) -> None:
        """Envia uma imagem PIL para a posicao (x, y) da tela."""
        x0, y0 = x, y
        x1, y1 = x + img.width - 1, y + img.height - 1
        payload = image_to_rgb565(img)
        self._send_command(Command.DISPLAY_BITMAP, x0, y0, x1, y1)
        assert self.serial is not None
        chunk = self.width * 8
        for i in range(0, len(payload), chunk):
            self.serial.write(payload[i:i + chunk])
        self.serial.flush()
