#!/usr/bin/env bash
# Instala o Claude Usage Tray no Linux: pacotes do sistema (Tk + AppIndicator), ambiente virtual,
# atalho no menu de aplicativos e (opcional) início automático. Uso: ./install-linux.sh [--uninstall]
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m[aviso]\033[0m %s\n' "$*"; }
fail() { printf '\033[31m[erro]\033[0m %s\n' "$*" >&2; exit 1; }

if [[ "${1:-}" == "--uninstall" ]]; then
    pkill -f "$(pwd)/main.pyw" 2>/dev/null || true
    [[ -x .venv/bin/python ]] && .venv/bin/python -m claude_usage_tray.setup_cli --uninstall
    rm -rf .venv
    echo "Pronto. Suas configurações ficam em ~/.config/claude-usage-tray (pode apagar se quiser)."
    exit 0
fi

echo
bold "  Claude Usage Tray — instalação no Linux"
echo "  ========================================"
echo

# Tk desenha o popup; PyGObject + AppIndicator mostram o ícone na bandeja; xprop acha a área útil da tela.
deps_ok() {
    python3 -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>/dev/null &&
        python3 -c "import venv, tkinter" 2>/dev/null &&
        python3 -c "
import gi
for ns in ('AyatanaAppIndicator3', 'AppIndicator3'):
    try:
        gi.require_version(ns, '0.1'); break
    except ValueError:
        pass
else:
    raise SystemExit(1)
" 2>/dev/null &&
        command -v xprop >/dev/null
}

bold "[1/4] Verificando dependências do sistema ..."
if ! deps_ok; then
    sudo=""; [[ $EUID -ne 0 ]] && sudo="sudo"
    if command -v apt-get >/dev/null; then
        # Instalação anterior interrompida: o apt recusa tudo até o dpkg terminar o que ficou pela metade.
        if [[ -n "$(ls -A /var/lib/dpkg/updates 2>/dev/null)" ]]; then
            fail "Uma instalação de pacotes anterior foi interrompida e o apt está travado.
       Rode:  sudo dpkg --configure -a && sudo apt-get install -f
       Depois rode este instalador de novo."
        fi
        $sudo apt-get update -qq
        $sudo apt-get install -y python3 python3-venv python3-tk python3-gi gir1.2-ayatanaappindicator3-0.1 x11-utils
    elif command -v dnf >/dev/null; then
        $sudo dnf install -y python3 python3-tkinter python3-gobject libayatana-appindicator-gtk3 xprop
    elif command -v pacman >/dev/null; then
        $sudo pacman -S --needed --noconfirm python tk python-gobject libayatana-appindicator xorg-xprop
    elif command -v zypper >/dev/null; then
        $sudo zypper install -y python3 python3-tk python3-gobject typelib-1_0-AyatanaAppIndicator3-0_1 xprop
    else
        fail "Gerenciador de pacotes não reconhecido. Instale: Python 3.10+, Tkinter, PyGObject, AyatanaAppIndicator3 e xprop."
    fi
    deps_ok || fail "Dependências ainda faltando depois da instalação. Veja a seção Linux do README."
fi

bold "[2/4] Criando ambiente virtual e instalando pacotes Python ..."
# --system-site-packages: o PyGObject (gi) vem do sistema, não do pip.
[[ -x .venv/bin/python ]] || python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --disable-pip-version-check -q --upgrade pip
.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt

bold "[3/4] Criando atalhos ..."
autostart=""
read -rp "      Iniciar junto com o sistema? [S/n] " answer || answer=""
[[ "${answer,,}" =~ ^(n|nao|não|no)$ ]] || autostart="--autostart"
.venv/bin/python -m claude_usage_tray.setup_cli --install $autostart
chmod +x install-linux.sh start-linux.sh

if [[ "${XDG_CURRENT_DESKTOP:-}" == *GNOME* ]] && command -v gnome-extensions >/dev/null; then
    if ! gnome-extensions list --enabled 2>/dev/null | grep -qi appindicator; then
        warn "No GNOME o ícone só aparece com a extensão AppIndicator ativa."
        warn "Ubuntu: já vem instalada. Fedora: sudo dnf install gnome-shell-extension-appindicator"
        warn "Depois ative: gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com (e saia/entre na sessão)."
    fi
fi

bold "[4/4] Abrindo o Claude Usage ..."
bash ./start-linux.sh

echo
bold "  Pronto! O ícone está na bandeja/painel do sistema."
echo
