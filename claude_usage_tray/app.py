"""Orquestra ícone da bandeja, polling, popup e configurações."""
import json
import logging
import threading
import tkinter as tk

import pystray

from . import system, tray_icon
from .popup import Popup
from .settings import AUTOSTART_LABEL, Settings
from .system import APP_NAME
from .usage_api import RateLimited, ServiceStatus, Usage, UsageError, Window, fetch_status, fetch_usage, format_reset

CONFIG_PATH = system.config_dir() / "config.json"
DEFAULT_CONFIG = {"icon_style": "ring", "icon_mono": False, "panel_label": True, "interval_seconds": 120}
LEGACY_STYLES = {"number": "percent"}
MAX_BACKOFF_SECONDS = 900


def load_config() -> dict:
    try:
        config = {**DEFAULT_CONFIG, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)
    config["icon_style"] = LEGACY_STYLES.get(config["icon_style"], config["icon_style"])
    if config["icon_style"] not in tray_icon.STYLES:
        config["icon_style"] = DEFAULT_CONFIG["icon_style"]
    return config


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


class App:
    def __init__(self):
        system.enable_dpi_awareness()
        self.config = load_config()
        self.usage: Usage | None = None
        self.error: str | None = None
        self.status: ServiceStatus | None = None
        self.backoff = 0
        self.poll_job = None
        self.root = tk.Tk()
        self.root.withdraw()
        self.popup = Popup(self.root, get_state=lambda: (self.usage, self.error, self.status),
                           on_refresh=self.refresh_now, on_settings=self.open_settings, on_quit=self.quit)
        self.settings = Settings(self.root, get_config=lambda: self.config, on_icon_change=self.set_icon,
                                 get_autostart=system.autostart_enabled, on_autostart_toggle=self.toggle_autostart)
        self.icon = pystray.Icon("claude_usage", self._render_icon(), APP_NAME, self._menu())

    def _menu(self) -> pystray.Menu:
        item = pystray.MenuItem

        def style_item(style: str, name: str) -> pystray.MenuItem:
            # pystray inspeciona a aridade do callback, então nada de default args no lambda.
            return item(name, lambda: self._ui(self.set_icon, style, self.config["icon_mono"]),
                        radio=True, checked=lambda _i: self.config["icon_style"] == style)

        styles = [style_item(style, name) for style, name in tray_icon.STYLES.items()]
        mono = item("Monocromático", lambda: self._ui(self.set_icon, self.config["icon_style"], not self.config["icon_mono"]),
                    checked=lambda _i: self.config["icon_mono"])
        # Linhas só de leitura no topo: dá pra ver os números sem abrir o popup (no Linux não há tooltip).
        info = [
            item(lambda _i, n=n: (self._summary_lines() + ["", "", ""])[n], None, enabled=False,
                 visible=lambda _i, n=n: len(self._summary_lines()) > n)
            for n in range(3)
        ]
        panel_label = item("Mostrar % ao lado do ícone", lambda: self._ui(self.toggle_panel_label),
                           checked=lambda _i: self.config["panel_label"], visible=not system.IS_WINDOWS)
        return pystray.Menu(
            *info,
            pystray.Menu.SEPARATOR,
            item("Abrir", lambda: self._ui(self.popup.toggle), default=True),
            item("Atualizar agora", lambda: self._ui(self.refresh_now)),
            item("Ícone da barra", pystray.Menu(*styles, pystray.Menu.SEPARATOR, mono, panel_label)),
            item("Configurações…", lambda: self._ui(self.open_settings)),
            item(AUTOSTART_LABEL, lambda: self._ui(self.toggle_autostart),
                 checked=lambda _i: system.autostart_enabled()),
            pystray.Menu.SEPARATOR,
            item("Sair", lambda: self._ui(self.quit)),
        )

    def _ui(self, fn, *args) -> None:
        """Callbacks do pystray rodam em outra thread; tkinter só no thread principal."""
        self.root.after(0, fn, *args)

    def run(self) -> None:
        if system.IS_WINDOWS:
            self.icon.run_detached()
        else:
            # Nos backends GTK o run_detached não roda o loop do GLib (espera que o app rode);
            # sem ele o ícone nem aparece. O tkinter fica com o thread principal, o GLib com este.
            threading.Thread(target=self.icon.run, daemon=True).start()
        self.refresh_now()
        self.root.mainloop()

    def refresh_now(self) -> None:
        if self.poll_job:
            self.root.after_cancel(self.poll_job)
            self.poll_job = None
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self) -> None:
        try:
            result, error = fetch_usage(), None
        except UsageError as exc:
            result, error = None, exc
        status = fetch_status()
        self.root.after(0, self._apply, result, error, status)

    def _apply(self, usage: Usage | None, error: UsageError | None, status: ServiceStatus | None) -> None:
        interval = self.config["interval_seconds"]
        self.status = status
        if usage:
            self.usage, self.error, self.backoff = usage, None, 0
        else:
            self.error = str(error)
            if isinstance(error, RateLimited):
                self.backoff = min(max(self.backoff * 2, interval * 2), MAX_BACKOFF_SECONDS)
                interval = self.backoff
        self._update_icon()
        self.popup.refresh()
        self.poll_job = self.root.after(interval * 1000, self.refresh_now)

    def _session_percent(self) -> float | None:
        session = self.usage.session if self.usage else None
        return session.percent if session and not self.error else None

    def _render_icon(self):
        return tray_icon.render(self._session_percent(), self.config["icon_style"], self.config["icon_mono"])

    def _update_icon(self) -> None:
        self.icon.icon = self._render_icon()
        self.icon.title = self._tooltip()[:127]
        self.icon.update_menu()
        self._update_panel_label()

    def _summary_lines(self) -> list[str]:
        if self.error and not self.usage:
            return [self.error]

        def line(name: str, window: Window | None) -> list[str]:
            if not window:
                return []
            reset = format_reset(window.resets_at)
            return [f"{name}: {window.percent:.0f}%" + (f" — {reset[0].lower()}{reset[1:]}" if reset else "")]

        lines = (line("Sessão", self.usage.session) + line("Semana", self.usage.weekly)) if self.usage else []
        if self.error:
            lines.append(f"⚠ {self.error}")
        return lines or ["Carregando…"]

    def _update_panel_label(self) -> None:
        """Linux: texto ao lado do ícone no painel (GNOME/Unity/XFCE mostram; o KDE ignora)."""
        indicator = getattr(self.icon, "_appindicator", None)  # só existe no backend AppIndicator
        if indicator is None:
            return
        from gi.repository import GLib

        percent = self._session_percent()
        text = f"{percent:.0f}%" if self.config["panel_label"] and percent is not None else ""
        GLib.idle_add(indicator.set_label, text, "100%")  # GTK só pode ser tocado no thread dele

    def _tooltip(self) -> str:
        if self.error and not self.usage:
            return f"{APP_NAME} — {self.error}"
        parts = []
        if self.usage.session:
            parts.append(f"Sessão {self.usage.session.percent:.0f}%")
        if self.usage.weekly:
            parts.append(f"Semana {self.usage.weekly.percent:.0f}%")
        text = f"Claude — {' · '.join(parts) or 'sem dados'}"
        return f"{text}\n⚠ {self.error}" if self.error else text

    def open_settings(self) -> None:
        self.settings.show()

    def set_icon(self, style: str, mono: bool) -> None:
        self.config["icon_style"], self.config["icon_mono"] = style, mono
        save_config(self.config)
        self._update_icon()
        self.icon.update_menu()
        self.settings.draw()

    def toggle_panel_label(self) -> None:
        self.config["panel_label"] = not self.config["panel_label"]
        save_config(self.config)
        self._update_icon()

    def toggle_autostart(self) -> None:
        system.set_autostart(not system.autostart_enabled())
        self.icon.update_menu()
        self.settings.draw()

    def quit(self) -> None:
        self.icon.stop()
        self.root.quit()


def _setup_logging() -> None:
    """Sem console (pythonw/.exe/autostart) os erros sumiriam; vão para app.log na pasta de config."""
    system.log_path().parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=system.log_path(), level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    _setup_logging()
    if not system.acquire_single_instance():
        return  # já tem um ícone na bandeja; não abre um segundo
    try:
        app = App()
        app.root.report_callback_exception = lambda *exc: logging.error("erro na UI", exc_info=exc)
        app.run()
    except Exception:
        logging.exception("o app parou com erro")
        raise
