"""Gera o executável standalone com PyInstaller (rodar da raiz: `python packaging/build.py`).

Windows: dist/ClaudeUsage.exe — um arquivo só, sem precisar de Python instalado.
No Linux prefira o install-linux.sh: o ícone de bandeja depende do PyGObject do sistema.
"""
import os
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = sys.platform == "win32"


def main() -> None:
    build_dir = ROOT / "build"
    args = [
        str(ROOT / "main.pyw"),
        "--name", "ClaudeUsage" if IS_WINDOWS else "claude-usage",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--icon", str(ROOT / "assets" / "icon.ico"),
        "--add-data", f"{ROOT / 'assets'}{os.pathsep}assets",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        # O pystray escolhe o backend em tempo de execução; o PyInstaller não enxerga sozinho.
        "--hidden-import", "pystray._win32" if IS_WINDOWS else "pystray._appindicator",
    ]
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
