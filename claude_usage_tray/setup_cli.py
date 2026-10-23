"""Cria/remove os atalhos do sistema. Chamado pelos scripts install-windows.bat e install-linux.sh."""
import argparse

from . import system


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m claude_usage_tray.setup_cli")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--install", action="store_true", help="cria o atalho no menu de aplicativos")
    action.add_argument("--uninstall", action="store_true", help="remove atalho do menu e início automático")
    parser.add_argument("--autostart", action="store_true", help="com --install: inicia junto com o sistema")
    args = parser.parse_args()

    if args.install:
        print(f"  atalho no menu: {system.install_menu_entry()}")
        if args.autostart:
            system.set_autostart(True)
            print("  início automático: ativado")
    else:
        system.remove_menu_entry()
        system.set_autostart(False)
        print("  atalhos removidos")


if __name__ == "__main__":
    main()
