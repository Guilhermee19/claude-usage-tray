"""Tudo que depende do sistema operacional fica aqui — o resto do app é portável (Windows e Linux)."""
import ctypes
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
APP_ID = "claude-usage-tray"
APP_NAME = "Claude Usage"

PROJECT_DIR = Path(__file__).resolve().parent.parent
_BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_DIR))  # PyInstaller extrai os assets aqui
ASSETS_DIR = _BUNDLE_DIR / "assets"

_instance_handle = None  # mantém o mutex/lock vivo enquanto o processo existir


def config_dir() -> Path:
    if IS_WINDOWS:
        return Path(os.environ.get("APPDATA", Path.home())) / "ClaudeUsageTray"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_ID


def enable_dpi_awareness() -> None:
    if IS_WINDOWS:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def acquire_single_instance() -> bool:
    """False se já existe outra instância rodando."""
    global _instance_handle
    if IS_WINDOWS:
        _instance_handle = ctypes.windll.kernel32.CreateMutexW(None, False, f"Local\\{APP_ID}")
        return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS
    import fcntl

    lock_path = config_dir() / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    _instance_handle = open(lock_path, "w")
    try:
        fcntl.flock(_instance_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def work_area(root: tk.Misc) -> tuple[int, int, int, int]:
    """Área útil da tela (sem barra de tarefas/painéis): left, top, right, bottom."""
    if IS_WINDOWS:
        from ctypes import wintypes

        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
        return rect.left, rect.top, rect.right, rect.bottom
    try:
        out = subprocess.run(["xprop", "-root", "_NET_WORKAREA"], capture_output=True, text=True, timeout=2).stdout
        x, y, w, h = (int(v) for v in out.split("=", 1)[1].replace(",", " ").split()[:4])
        return x, y, x + w, y + h
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def style_window(win: tk.Misc, dark_titlebar: bool = False) -> None:
    """Cantos arredondados + sombra do Windows 11 (DWM). No Linux quem decide é o window manager."""
    if not IS_WINDOWS:
        return
    win.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
    dwm = ctypes.windll.dwmapi
    dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)  # DWMWCP_ROUND
    if dark_titlebar:
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)  # IMMERSIVE_DARK_MODE


def _launch_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    python = Path(sys.executable)
    if IS_WINDOWS and python.with_name("pythonw.exe").exists():
        python = python.with_name("pythonw.exe")
    return [str(python), str(PROJECT_DIR / "main.pyw")]


def log_path() -> Path:
    return config_dir() / "app.log"


def _start_menu_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def _autostart_path() -> Path:
    if IS_WINDOWS:
        return _start_menu_dir() / "Startup" / "Claude Usage Tray.lnk"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart" / f"{APP_ID}.desktop"


def _menu_entry_path() -> Path:
    if IS_WINDOWS:
        return _start_menu_dir() / f"{APP_NAME}.lnk"
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_home / "applications" / f"{APP_ID}.desktop"


def _write_launcher(path: Path) -> None:
    command = _launch_command()
    if IS_WINDOWS:
        _create_shortcut(path, command)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(command), encoding="utf-8")


def autostart_enabled() -> bool:
    return _autostart_path().exists()


def set_autostart(enabled: bool) -> None:
    if enabled:
        _write_launcher(_autostart_path())
    else:
        _autostart_path().unlink(missing_ok=True)


def install_menu_entry() -> Path:
    path = _menu_entry_path()
    _write_launcher(path)
    return path


def remove_menu_entry() -> None:
    _menu_entry_path().unlink(missing_ok=True)


def _create_shortcut(path: Path, command: list[str]) -> None:
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK);"
        "$s.TargetPath=$env:TARGET;$s.Arguments=$env:ARGS;$s.WorkingDirectory=$env:WORKDIR;"
        "if(Test-Path $env:ICON){$s.IconLocation=$env:ICON};$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        env={**os.environ, "LINK": str(path), "TARGET": command[0],
             "ARGS": " ".join(f'"{arg}"' for arg in command[1:]),
             "WORKDIR": str(Path(command[-1]).parent), "ICON": str(ASSETS_DIR / "icon.ico")},
        creationflags=subprocess.CREATE_NO_WINDOW, check=True,
    )


def desktop_entry(command: list[str]) -> str:
    exec_line = " ".join(f'"{arg}"' for arg in command)
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        "Comment=Uso do plano Claude na bandeja do sistema\n"
        f"Exec={exec_line}\n"
        f"Icon={ASSETS_DIR / 'icon.png'}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
