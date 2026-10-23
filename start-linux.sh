#!/usr/bin/env bash
# Abre o Claude Usage Tray em segundo plano. Instala na primeira vez.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

if [[ ! -x .venv/bin/python ]]; then
    echo "Primeira execução: rodando o instalador ..."
    exec bash ./install-linux.sh
fi

# Saída do processo (inclusive erros de inicialização do GTK/Tk) vai para este arquivo.
log_dir="${XDG_STATE_HOME:-$HOME/.local/state}"
mkdir -p "$log_dir"
nohup .venv/bin/python main.pyw >>"$log_dir/claude-usage-tray.log" 2>&1 &
disown
echo "Claude Usage iniciado. Log: $log_dir/claude-usage-tray.log"
