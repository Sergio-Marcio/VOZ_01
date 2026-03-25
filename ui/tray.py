"""
ui/tray.py — Ícone de bandeja do sistema para o Mari Presenter.

Estados:
  - Verde  (ouvindo ativamente)
  - Cinza  (pausado)
  - Amarelo (processando / inicializando)

Menu de contexto:
  - Pausar / Retomar
  - Encerrar Mari
"""

import threading
from PIL import Image, ImageDraw
import pystray


# ─── Criação dos ícones ───────────────────────────────────────────────────────
_SIZE = 64

def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (_SIZE, _SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Círculo sólido com borda branca
    margin = 4
    draw.ellipse(
        [margin, margin, _SIZE - margin, _SIZE - margin],
        fill=color,
        outline="white",
        width=3,
    )
    # Letra "M" centralizada (microfone)
    draw.text((_SIZE // 2 - 7, _SIZE // 2 - 10), "M", fill="white")
    return img


ICON_LISTENING  = _make_icon("#27ae60")   # verde
ICON_PAUSED     = _make_icon("#7f8c8d")   # cinza
ICON_STARTING   = _make_icon("#f39c12")   # amarelo


# ─── Classe TrayApp ───────────────────────────────────────────────────────────
class TrayApp:
    def __init__(self, pause_event: threading.Event, stop_event: threading.Event):
        """
        pause_event — quando set, o loop de voz não processa comandos.
        stop_event  — quando set, encerra tudo (voz + tray).
        """
        self._pause = pause_event
        self._stop  = stop_event
        self._tray  = None

    # ── Ações do menu ──────────────────────────────────────────────────────
    def _toggle_pause(self, icon, item):
        if self._pause.is_set():
            self._pause.clear()
            icon.icon  = ICON_LISTENING
            icon.title = "Mari Presenter — Ouvindo"
        else:
            self._pause.set()
            icon.icon  = ICON_PAUSED
            icon.title = "Mari Presenter — Pausado"
        icon.update_menu()

    def _quit(self, icon, item):
        self._stop.set()
        icon.stop()

    # ── Texto dinâmico do item "Pausar/Retomar" ────────────────────────────
    def _pause_label(self, item):
        return "▶ Retomar" if self._pause.is_set() else "⏸ Pausar"

    # ── Iniciar tray (bloqueante — rodar em thread) ────────────────────────
    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem(self._pause_label, self._toggle_pause, default=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✖ Encerrar Mari", self._quit),
        )
        self._tray = pystray.Icon(
            name="MariPresenter",
            icon=ICON_STARTING,
            title="Mari Presenter — Iniciando…",
            menu=menu,
        )
        self._tray.run()

    def set_listening(self):
        if self._tray:
            self._tray.icon  = ICON_LISTENING
            self._tray.title = "Mari Presenter — Ouvindo"

    def set_paused(self):
        if self._tray:
            self._tray.icon  = ICON_PAUSED
            self._tray.title = "Mari Presenter — Pausado"


# ─── Helper para uso externo ──────────────────────────────────────────────────
def start_tray(pause_event: threading.Event, stop_event: threading.Event) -> TrayApp:
    """
    Cria e inicia o tray em uma thread daemon.
    Retorna a instância TrayApp para controle posterior.
    """
    app = TrayApp(pause_event, stop_event)
    t = threading.Thread(target=app.run, daemon=True, name="MariTray")
    t.start()
    return app
