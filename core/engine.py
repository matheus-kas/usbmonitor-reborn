"""Motor: loop que coleta sensores, renderiza o tema e envia para a tela.

Roda em thread propria para nao travar a UI. Thread-safe para troca de tema,
brilho e orientacao em tempo real.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

from PIL import Image, ImageDraw

from core.sensors import SensorHub, Reading
from core.theme import Theme
from core.renderer import Renderer
from driver.turing_screen import TuringScreen, Orientation


class DisplayEngine:
    def __init__(self, theme: Theme, fps: float = 1.0,
                 disk_path: str = "C:\\",
                 orientation: Orientation = Orientation.LANDSCAPE):
        self.hub = SensorHub(disk_path=disk_path)
        self.renderer = Renderer(theme)
        self.fps = fps
        self.orientation = orientation
        self.screen: TuringScreen | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._retention = threading.Event()      # ativo durante recuperacao
        self._retention_cancel = threading.Event()
        self._lock = threading.Lock()
        self._brightness = 100
        self._last_image: Image.Image | None = None
        # callback opcional para a UI mostrar o preview (recebe PIL.Image)
        self.on_frame: Callable[[Image.Image], None] | None = None

    # ---- controle -----------------------------------------------------
    def connect(self, com_port: str | None = None) -> None:
        self.screen = TuringScreen(com_port=com_port, orientation=self.orientation)
        self.screen.open()
        self.screen.set_orientation(self.orientation)
        self.screen.set_brightness(self._brightness)
        self.screen.clear_black()   # frame preto real, elimina ghosting

    def set_theme(self, theme: Theme) -> None:
        with self._lock:
            self.renderer.set_theme(theme)

    def set_brightness(self, percent: int) -> None:
        with self._lock:
            self._brightness = percent
            if self.screen:
                self.screen.set_brightness(percent)

    def set_orientation(self, orientation: Orientation) -> None:
        with self._lock:
            self.orientation = orientation
            if self.screen:
                self.screen.set_orientation(orientation)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self.screen:
            try:
                self.screen.clear_black()   # deixa a tela limpa ao sair
            except Exception:
                pass
            self.screen.close()
            self.screen = None

    # ---- loop ---------------------------------------------------------
    def _loop(self) -> None:
        period = 1.0 / self.fps
        while not self._stop.is_set():
            if self._retention.is_set():     # recuperacao em andamento: nao envia sensores
                self._stop.wait(0.2)
                continue
            t0 = time.monotonic()
            reading = self.hub.read()
            with self._lock:
                img = self.renderer.render(reading)
                self._last_image = img
                if self.screen:
                    try:
                        self.screen.display_image(img)
                    except Exception as exc:
                        print(f"[engine] erro ao enviar frame: {exc}")
            if self.on_frame:
                try:
                    self.on_frame(img)
                except Exception:
                    pass
            dt = time.monotonic() - t0
            self._stop.wait(max(0.0, period - dt))

    def render_once(self) -> Image.Image:
        """Renderiza um frame sem enviar (para preview na UI)."""
        reading = self.hub.read()
        return self.renderer.render(reading)

    # ---- recuperacao de retencao de imagem ----------------------------
    def start_retention_recovery(self, duration_s: int,
                                 on_progress: Callable[[float], None] | None = None,
                                 on_done: Callable[[], None] | None = None) -> None:
        """Roda, em thread, um ciclo que dissolve a imagem retida no painel.

        Alterna a tela entre branco, preto e as cores primarias, mais barras
        em movimento, exercitando todos os pixels por igual.
        """
        if not self.screen:
            raise RuntimeError("Conecte a tela antes de recuperar a retencao.")
        self._retention_cancel = threading.Event()
        t = threading.Thread(
            target=self._retention_worker,
            args=(duration_s, on_progress, on_done), daemon=True)
        t.start()

    def cancel_retention_recovery(self) -> None:
        cancel = getattr(self, "_retention_cancel", None)
        if cancel:
            cancel.set()

    def _retention_worker(self, duration_s, on_progress, on_done) -> None:
        self._retention.set()                 # pausa o envio normal de sensores
        colors = [(255, 255, 255), (0, 0, 0), (255, 0, 0),
                  (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        hold = 0.5
        w, h = self.screen.width, self.screen.height
        start = time.monotonic()
        idx = 0
        try:
            while time.monotonic() - start < duration_s:
                if self._retention_cancel.is_set():
                    break
                color = colors[idx % len(colors)]
                idx += 1
                with self._lock:
                    if self.screen:
                        self.screen.fill(color)
                # barras em movimento entre as cores solidas
                for off in range(0, w, max(1, w // 8)):
                    if self._retention_cancel.is_set() or \
                            time.monotonic() - start >= duration_s:
                        break
                    img = Image.new("RGB", (w, h), (0, 0, 0))
                    d = ImageDraw.Draw(img)
                    bar = max(8, w // 10)
                    for x in range(-bar + off, w, bar * 2):
                        d.rectangle([x, 0, x + bar, h], fill=color)
                    with self._lock:
                        if self.screen:
                            self.screen.display_image(img)
                    if on_progress:
                        on_progress(min(1.0, (time.monotonic() - start) / duration_s))
                    time.sleep(0.05)
                if on_progress:
                    on_progress(min(1.0, (time.monotonic() - start) / duration_s))
                time.sleep(hold)
        finally:
            with self._lock:
                if self.screen:
                    try:
                        self.screen.clear_black()
                    except Exception:
                        pass
            self._retention.clear()
            if on_done:
                on_done()
