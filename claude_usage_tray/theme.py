"""Paleta e helpers visuais compartilhados (dark mode no estilo macOS)."""
import tkinter as tk

from .system import IS_WINDOWS

BG = "#1c1c1e"
CARD = "#2c2c2e"
BORDER = "#3a3a3c"
HOVER = "#3a3a3c"
FG = "#f5f5f7"
MUTED = "#8e8e93"
TRACK = "#48484a"
GREEN = "#30d158"
RED = "#ff453a"
BRAND = "#d97757"
TASKBAR = "#202020"


def font(size: int, bold: bool = False) -> tuple:
    if IS_WINDOWS:
        return ("Segoe UI Semibold" if bold else "Segoe UI", size)
    # No Linux o fontconfig resolve "sans-serif" para a fonte padrão do desktop.
    return ("sans-serif", size, "bold" if bold else "normal")


def hex_color(rgb: tuple[int, ...]) -> str:
    return "#%02x%02x%02x" % rgb[:3]


def scale_of(widget: tk.Misc) -> float:
    """Fator de escala do monitor (1.0 = 96 dpi); coordenadas de canvas não escalam sozinhas."""
    return widget.winfo_fpixels("1i") / 96


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kwargs) -> int:
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def hoverable(canvas: tk.Canvas, items, background: int, command, normal=BG, hover=HOVER) -> None:
    for item in items:
        canvas.tag_bind(item, "<Enter>", lambda _e: canvas.itemconfig(background, fill=hover) or canvas.config(cursor="hand2"))
        canvas.tag_bind(item, "<Leave>", lambda _e: canvas.itemconfig(background, fill=normal) or canvas.config(cursor=""))
        canvas.tag_bind(item, "<Button-1>", lambda _e: command())
