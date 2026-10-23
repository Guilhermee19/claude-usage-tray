"""Janela de configurações: escolha do ícone da barra (estilo × cor) e início automático."""
import tkinter as tk

from PIL import ImageTk

from . import tray_icon
from .system import APP_NAME, ASSETS_DIR, IS_WINDOWS, style_window
from .theme import BG, BORDER, CARD, FG, GREEN, MUTED, TASKBAR, TRACK, font, round_rect, scale_of

WIDTH = 460
PAD = 18
TILE_HEIGHT = 58
PREVIEW_PERCENT = 49
ROWS = (("Colorido", False), ("Monocromático", True))
AUTOSTART_LABEL = "Iniciar com o Windows" if IS_WINDOWS else "Iniciar com o sistema"
HINT = (
    "Dica: o Windows esconde ícones novos atrás da seta ^ da bandeja. "
    "Arraste o ícone para a barra para deixá-lo sempre visível."
    if IS_WINDOWS else
    "Dica: no GNOME, ícones de bandeja precisam da extensão AppIndicator "
    "(já vem no Ubuntu). KDE, XFCE e Cinnamon funcionam direto."
)


class Settings:
    def __init__(self, root: tk.Tk, get_config, on_icon_change, get_autostart, on_autostart_toggle):
        self.root = root
        self.get_config = get_config
        self.on_icon_change = on_icon_change
        self.get_autostart = get_autostart
        self.on_autostart_toggle = on_autostart_toggle
        self.win: tk.Toplevel | None = None
        self.images: list[ImageTk.PhotoImage] = []

    def show(self) -> None:
        if self.win is not None and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return
        self.win = tk.Toplevel(self.root, bg=BG)
        self.win.title(f"{APP_NAME} — Configurações")
        self.win.resizable(False, False)
        icon = ASSETS_DIR / "icon.png"
        if icon.exists():
            self.window_icon = tk.PhotoImage(master=self.win, file=icon)
            self.win.iconphoto(False, self.window_icon)
        self.s = scale_of(self.win)
        self.canvas = tk.Canvas(self.win, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.draw()
        style_window(self.win, dark_titlebar=True)
        self.win.focus_force()

    def draw(self) -> None:
        if self.win is None or not self.win.winfo_exists():
            return
        c, S = self.canvas, lambda v: v * self.s
        c.delete("all")
        self.images.clear()
        config = self.get_config()

        y = PAD
        c.create_text(S(PAD), S(y), text="Ícone da barra", fill=FG, font=font(12, bold=True), anchor="nw")
        c.create_text(S(PAD), S(y + 24), text="Como o uso da sessão aparece na barra de tarefas",
                      fill=MUTED, font=font(9), anchor="nw")
        y += 54
        for label, mono in ROWS:
            c.create_text(S(PAD), S(y), text=label, fill=MUTED, font=font(8), anchor="nw")
            y += 18
            y = self._tile_row(config, mono, y) + 14

        c.create_text(S(PAD), S(y), text="Geral", fill=FG, font=font(12, bold=True), anchor="nw")
        y += 30
        y = self._toggle_row(AUTOSTART_LABEL, self.get_autostart(), self._toggle_autostart, y) + 14

        text = c.create_text(S(PAD), S(y), text=HINT, fill=MUTED, font=font(8), anchor="nw",
                             width=S(WIDTH - 2 * PAD))
        height = c.bbox(text)[3] + S(PAD)
        c.config(width=S(WIDTH), height=height)

    def _tile_row(self, config: dict, mono: bool, y: int) -> int:
        c, S = self.canvas, lambda v: v * self.s
        round_rect(c, S(PAD), S(y), S(WIDTH - PAD), S(y + TILE_HEIGHT + 34), S(12), fill=CARD, outline=BORDER)
        gap, inner = 8, 10
        tile_w = (WIDTH - 2 * PAD - 2 * inner - gap * (len(tray_icon.STYLES) - 1)) / len(tray_icon.STYLES)
        icon_px = int(S(30))
        for i, (style, name) in enumerate(tray_icon.STYLES.items()):
            x = PAD + inner + i * (tile_w + gap)
            selected = config["icon_style"] == style and config["icon_mono"] == mono
            tile = round_rect(c, S(x), S(y + inner), S(x + tile_w), S(y + inner + TILE_HEIGHT - 6), S(10),
                              fill=TASKBAR, outline=GREEN if selected else TASKBAR, width=S(2))
            image = ImageTk.PhotoImage(tray_icon.render(PREVIEW_PERCENT, style, mono, size=icon_px))
            self.images.append(image)
            icon = c.create_image(S(x + tile_w / 2), S(y + inner + (TILE_HEIGHT - 6) / 2), image=image)
            caption = c.create_text(S(x + tile_w / 2), S(y + inner + TILE_HEIGHT + 6), text=name,
                                    fill=FG if selected else MUTED, font=font(8))
            for item in (tile, icon, caption):
                c.tag_bind(item, "<Button-1>", lambda _e, st=style, mo=mono: self._select(st, mo))
                c.tag_bind(item, "<Enter>", lambda _e: c.config(cursor="hand2"))
                c.tag_bind(item, "<Leave>", lambda _e: c.config(cursor=""))
        return y + TILE_HEIGHT + 34

    def _toggle_row(self, label: str, on: bool, command, y: int) -> int:
        c, S = self.canvas, lambda v: v * self.s
        height = 46
        round_rect(c, S(PAD), S(y), S(WIDTH - PAD), S(y + height), S(12), fill=CARD, outline=BORDER)
        c.create_text(S(PAD + 14), S(y + height / 2), text=label, fill=FG, font=font(10), anchor="w")
        right, cy = WIDTH - PAD - 14, y + height / 2
        track = round_rect(c, S(right - 40), S(cy - 11), S(right), S(cy + 11), S(11),
                           fill=GREEN if on else TRACK, outline="")
        knob_x = right - 11 if on else right - 29
        knob = c.create_oval(S(knob_x - 9), S(cy - 9), S(knob_x + 9), S(cy + 9), fill="#ffffff", outline="")
        for item in (track, knob):
            c.tag_bind(item, "<Button-1>", lambda _e: command())
        return y + height

    def _select(self, style: str, mono: bool) -> None:
        self.on_icon_change(style, mono)
        self.draw()

    def _toggle_autostart(self) -> None:
        self.on_autostart_toggle()
        self.draw()
