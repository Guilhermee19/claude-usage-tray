"""Popup no estilo do menu bar extra do macOS, ancorado perto do ícone da bandeja."""
import math
import tkinter as tk

from .system import IS_WINDOWS, style_window, work_area
from .theme import (BG, BORDER, BRAND, CARD, FG, GREEN, HOVER, MUTED, RED, TRACK,
                    font, hex_color, hoverable, round_rect, scale_of)
from .tray_icon import color_for
from .usage_api import Window, format_reset

WIDTH = 320 if IS_WINDOWS else 350  # fontes do Linux (Ubuntu/DejaVu) são mais largas + botão ✕
PAD = 14
CARD_HEIGHT = 84
MARGIN = 12


class Popup:
    def __init__(self, root: tk.Tk, get_state, on_refresh, on_settings, on_quit):
        self.root = root
        self.get_state = get_state
        self.on_refresh = on_refresh
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.win: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None

    def is_open(self) -> bool:
        return self.win is not None and self.win.winfo_exists()

    def toggle(self) -> None:
        if self.is_open():
            self.close()
        else:
            self.show()

    def close(self) -> None:
        if self.is_open():
            self.win.destroy()
        self.win = None

    def refresh(self) -> None:
        if self.is_open():
            self._draw()

    def show(self) -> None:
        self.win = tk.Toplevel(self.root, bg=BG)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.s = scale_of(self.win)
        self.canvas = tk.Canvas(self.win, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.win.bind("<FocusOut>", lambda _e: self.root.after(150, self._close_if_unfocused))
        self.win.bind("<Escape>", lambda _e: self.close())
        self._draw()
        style_window(self.win)
        self.win.focus_force()

    def _close_if_unfocused(self) -> None:
        if self.is_open() and self.win.focus_get() is None:
            self.close()

    def _draw(self) -> None:
        usage, error, status = self.get_state()
        c, S = self.canvas, lambda v: v * self.s
        c.delete("all")
        y = self._header(usage, status)
        if error:
            text = c.create_text(S(PAD), S(y), text=error, fill=RED, font=font(9), anchor="nw",
                                 width=S(WIDTH - 2 * PAD))
            y = c.bbox(text)[3] / self.s + 8
        windows = [w for w in ((usage.session, usage.weekly, *usage.weekly_models) if usage else ()) if w]
        for window in windows:
            self._card(window, y)
            y += CARD_HEIGHT + 10
        y = self._footer(usage, y + 2)
        c.config(width=S(WIDTH), height=S(y))
        self._place()

    def _header(self, usage, status) -> int:
        c, S = self.canvas, lambda v: v * self.s
        c.create_arc(S(PAD), S(PAD + 2), S(PAD + 30), S(PAD + 32), start=40, extent=280,
                     style="arc", outline=BRAND, width=S(5))
        title = "Claude Usage" + (f" · {usage.plan}" if usage and usage.plan else "")
        c.create_text(S(PAD + 42), S(PAD), text=title, fill=FG, font=font(12, bold=True), anchor="nw")
        if status:
            color = GREEN if status.ok else RED
            text = c.create_text(S(PAD + 58), S(PAD + 33), text=status.text, fill=color,
                                 font=font(8), anchor="w")
            x1, y1, x2, y2 = c.bbox(text)
            pill = round_rect(c, S(PAD + 42), y1 - S(3), x2 + S(8), y2 + S(3), S(9),
                              fill="#1e3a26" if status.ok else "#3a1e1e", outline="")
            dot = c.create_oval(S(PAD + 48), S(PAD + 30), S(PAD + 54), S(PAD + 36), fill=color, outline="")
            c.tag_lower(pill, text)
            c.tag_raise(dot)

        if not IS_WINDOWS:
            # No GNOME (Ubuntu) janelas sem moldura muitas vezes não recebem foco, então "clicar fora"
            # e Esc podem não fechar — o ✕ garante.
            self._close_button(S(WIDTH - PAD - 48), S(PAD + 16))
        cx, cy, r = S(WIDTH - PAD - 14), S(PAD + 16), S(14)
        bg = c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=CARD, outline="")
        icon = c.create_text(cx, cy, text="↻", fill=FG, font=font(12))
        hoverable(c, (bg, icon), bg, self.on_refresh, normal=CARD, hover=HOVER)
        return PAD + 52

    def _close_button(self, cx: float, cy: float) -> None:
        c, S = self.canvas, lambda v: v * self.s
        r, d = S(14), S(4.5)
        bg = c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=CARD, outline="")
        lines = [c.create_line(cx - d, cy - d * sy, cx + d, cy + d * sy, fill=FG, width=S(1.6), capstyle="round")
                 for sy in (1, -1)]
        hoverable(c, (bg, *lines), bg, self.close, normal=CARD, hover=HOVER)

    def _card(self, window: Window, y: int) -> None:
        c, S = self.canvas, lambda v: v * self.s
        left, right = PAD, WIDTH - PAD
        round_rect(c, S(left), S(y), S(right), S(y + CARD_HEIGHT), S(12), fill=CARD, outline=BORDER)
        c.create_text(S(left + 14), S(y + 12), text=window.label, fill=FG, font=font(10, bold=True), anchor="nw")
        c.create_text(S(left + 14), S(y + 32), text=window.subtitle, fill=MUTED, font=font(8), anchor="nw")

        color = hex_color(color_for(window.percent))
        pct = c.create_text(S(right - 14), S(y + 22), text=f"{window.percent:.0f}%", fill=color,
                            font=font(11, bold=True), anchor="e")
        x1 = c.bbox(pct)[0]
        c.create_oval(x1 - S(20), S(y + 15), x1 - S(6), S(y + 29), fill=color, outline="")
        c.create_text(x1 - S(13), S(y + 22), text="✓", fill=CARD, font=font(7, bold=True))

        bar_y, bar_left, bar_right = S(y + 58), S(left + 14), S(right - 14)
        c.create_line(bar_left, bar_y, bar_right, bar_y, fill=TRACK, width=S(6), capstyle="round")
        if window.percent > 0:
            end = bar_left + (bar_right - bar_left) * min(window.percent, 100) / 100
            c.create_line(bar_left, bar_y, max(end, bar_left + 1), bar_y, fill=color, width=S(6), capstyle="round")
        c.create_text(S(right - 14), S(y + 70), text=format_reset(window.resets_at), fill=MUTED,
                      font=font(8), anchor="ne")

    def _footer(self, usage, y: int) -> int:
        c, S = self.canvas, lambda v: v * self.s
        c.create_line(S(PAD), S(y), S(WIDTH - PAD), S(y), fill=BORDER)
        y += 10
        buttons = (("Configurações", FG, self._open_settings, self._gear_icon),
                   ("Sair", RED, self.on_quit, self._power_icon))
        x = WIDTH / 2 - 62
        for text, color, command, draw_icon in buttons:
            # Ícones desenhados: as fontes padrão do Linux não têm os glifos ⚙/⏻.
            label = c.create_text(S(x + 9), S(y + 12), text=text, fill=color, font=font(9))
            x1, y1, x2, y2 = c.bbox(label)
            icon = draw_icon(x1 - S(16), (y1 + y2) / 2, color)
            bg = round_rect(c, x1 - S(26), y1 - S(4), x2 + S(10), y2 + S(4), S(8), fill=BG, outline="")
            c.tag_lower(bg, label)
            hoverable(c, (bg, label, *icon), bg, command)
            x += 130
        y += 30
        if usage:
            c.create_text(S(WIDTH / 2), S(y), text=f"Atualizado às {usage.fetched_at:%H:%M}", fill=MUTED,
                          font=font(7))
            y += 10
        return y + PAD - 4

    def _gear_icon(self, cx: float, cy: float, color: str) -> tuple[int, ...]:
        c, S = self.canvas, lambda v: v * self.s
        # Dentes como traços radiais: outline tracejado renderiza diferente no Windows e no X11.
        teeth = [
            c.create_line(cx + S(4) * math.cos(a), cy + S(4) * math.sin(a),
                          cx + S(7) * math.cos(a), cy + S(7) * math.sin(a), fill=color, width=S(2.2))
            for a in (i * math.pi / 4 for i in range(8))
        ]
        ring = c.create_oval(cx - S(4.5), cy - S(4.5), cx + S(4.5), cy + S(4.5), outline=color, width=S(2))
        hole = c.create_oval(cx - S(1.5), cy - S(1.5), cx + S(1.5), cy + S(1.5), outline=color, width=S(1))
        return (*teeth, ring, hole)

    def _power_icon(self, cx: float, cy: float, color: str) -> tuple[int, ...]:
        c, S = self.canvas, lambda v: v * self.s
        arc = c.create_arc(cx - S(6), cy - S(5), cx + S(6), cy + S(7), start=120, extent=300,
                           style="arc", outline=color, width=S(1.6))
        line = c.create_line(cx, cy - S(7), cx, cy, fill=color, width=S(1.6), capstyle="round")
        return arc, line

    def _open_settings(self) -> None:
        self.close()
        self.on_settings()

    def _place(self) -> None:
        self.win.update_idletasks()
        left, top, right, bottom = work_area(self.root)
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        m = int(MARGIN * self.s)
        if IS_WINDOWS:
            # Abre sobre o ícone clicado (o ponteiro está nele), do lado da barra de tarefas.
            px, py = self.root.winfo_pointerxy()
            x = min(max(px - w // 2, left + m), right - w - m)
            y = top + m if py < (top + bottom) / 2 else bottom - h - m
        else:
            # No Wayland (padrão do Ubuntu) o Tk não sabe onde o ponteiro está quando o menu é do
            # GNOME; ancora no canto direito, colado no painel — no Ubuntu, logo abaixo dos indicadores.
            panel_at_bottom = self.root.winfo_screenheight() - bottom > top
            x = right - w - m
            y = bottom - h - m if panel_at_bottom else top + m
        self.win.geometry(f"{w}x{h}+{x}+{y}")
