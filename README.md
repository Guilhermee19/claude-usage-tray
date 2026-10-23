<div align="center">

<img src="assets/icon.png" width="96" alt="Claude Usage Tray">

# Claude Usage Tray

**O uso do seu plano Claude sempre à vista — direto na bandeja do Windows e do Linux.**

Sessão de 5 horas, limite semanal e status do serviço, ao lado do relógio, como volume, Wi-Fi e bateria.

[![build](https://github.com/Guilhermee19/claude-usage-tray/actions/workflows/build.yml/badge.svg)](https://github.com/Guilhermee19/claude-usage-tray/actions/workflows/build.yml)
![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Ubuntu%20%7C%20Fedora%20%7C%20Arch-FCC624?logo=linux&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img src="docs/images/popup.png" width="320" alt="Popup com o uso da sessão e da semana">

</div>

---

## Recursos

- **Ícone vivo na bandeja** — mostra a % da sessão atual e atualiza sozinho a cada 2 minutos.
- **Popup no estilo macOS** — cards com a sessão (janela de 5 h), o limite semanal e o limite por modelo
  (quando o plano tem), com barra de progresso e horário exato do reset.
- **Status do serviço** — pílula verde quando todos os sistemas da Anthropic estão operacionais.
- **5 estilos de ícone × 2 cores** — anel, bateria, barra, porcentagem ou ponto; colorido ou monocromático.
- **Inicia com o sistema** — uma chave nas configurações.
- **Seguro com o seu login** — só *lê* o token do Claude Code; nunca o renova, altera ou envia para outro lugar.
- **Leve** — Python puro + [pystray](https://github.com/moses-palmer/pystray) + [Pillow](https://python-pillow.org); ~60 MB de RAM.

<div align="center">
<img src="docs/images/icon-styles.png" width="720" alt="Estilos de ícone disponíveis">
</div>

## Requisitos

- Uma conta Claude **Pro ou Max** logada no [Claude Code](https://docs.claude.com/en/docs/claude-code)
  (o app usa o mesmo login — precisa existir `~/.claude/.credentials.json`).
- **Windows 10/11** ou **Linux** com bandeja do sistema (KDE, XFCE, Cinnamon, MATE, GNOME com AppIndicator).
- **Python 3.10+** — exceto se você usar o `.exe` pronto.

## Instalação

### Windows

**Opção 1 — executável pronto (sem Python):** baixe o `ClaudeUsage.exe` na página de
[Releases](https://github.com/Guilhermee19/claude-usage-tray/releases) e dê dois cliques.

**Opção 2 — a partir do código:**

```powershell
git clone https://github.com/Guilhermee19/claude-usage-tray.git
cd claude-usage-tray
.\install-windows.bat
```

O instalador cria um ambiente virtual em `.venv`, instala as dependências, adiciona o **Claude Usage**
ao Menu Iniciar, pergunta se deve iniciar junto com o Windows e já abre o app.
Depois disso, use o Menu Iniciar ou `start-windows.bat`.

> **O ícone não apareceu?** O Windows 11 esconde ícones novos atrás da seta **^** da bandeja.
> Arraste-o para a barra, ou ative em *Configurações → Personalização → Barra de tarefas →
> Outros ícones da bandeja*.

### Linux

```bash
git clone https://github.com/Guilhermee19/claude-usage-tray.git
cd claude-usage-tray
bash install-linux.sh
```

O instalador detecta o gerenciador de pacotes (**apt**, **dnf**, **pacman** ou **zypper**) e instala o que
faltar — Tkinter, PyGObject, AyatanaAppIndicator e xprop (pede `sudo` só se precisar). Em seguida cria o
ambiente virtual, adiciona o app ao menu de aplicativos, pergunta sobre o início automático e abre o app.
Depois disso, use o menu de aplicativos ou `bash start-linux.sh`.

> **GNOME (Fedora, Debian…):** ícones de bandeja precisam da extensão
> [AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/). No Ubuntu ela já vem
> ativa. No Fedora: `sudo dnf install gnome-shell-extension-appindicator`, ative a extensão e reinicie a sessão.

## Uso

| Ação | Windows | Linux |
|---|---|---|
| Abrir o popup | clique esquerdo no ícone | menu do ícone → **Abrir** |
| Menu rápido | clique direito | clique no ícone |
| Ver os números sem abrir | passe o mouse (tooltip) | — |

No menu: **Atualizar agora**, **Ícone da barra** (estilo e monocromático), **Configurações…**,
**Iniciar com o sistema** e **Sair**. Pelo popup, `Esc` ou clicar fora fecha.

<div align="center">
<img src="docs/images/settings.png" width="420" alt="Janela de configurações">
</div>

### Cores

| | Significado |
|---|---|
| 🟢 Verde | uso da sessão (estilos anel, bateria, barra e porcentagem) |
| 🟡 / 🔴 | no estilo **ponto** e nos cards do popup: ≥ 50% e ≥ 80% |
| ⚪ Cinza | sem dados — sem internet ou token expirado |

### Configuração

As preferências ficam em `config.json`:

| Sistema | Pasta |
|---|---|
| Windows | `%APPDATA%\ClaudeUsageTray\` |
| Linux | `~/.config/claude-usage-tray/` |

```json
{
  "icon_style": "ring",
  "icon_mono": false,
  "interval_seconds": 120
}
```

`icon_style`: `ring`, `battery`, `bar`, `percent` ou `dot`. Erros vão para `app.log` na mesma pasta.

## Como funciona

```
~/.claude/.credentials.json ──(lê o token)──► api.anthropic.com/api/oauth/usage
                                                 │  five_hour · seven_day · seven_day_opus …
                                                 ▼
                         ícone na bandeja (Pillow) + popup (Tkinter)
```

O app consulta o mesmo endpoint que o comando `/usage` do Claude Code, então os números são idênticos.
O token **não é renovado** pelo app: renovar giraria o *refresh token* e poderia deslogar o Claude Code.
Quando ele expira, o ícone fica cinza com o aviso *"abra o Claude Code"* — basta usar o Claude Code uma vez
e o app volta sozinho na próxima atualização.

> Este endpoint não é uma API pública documentada e pode mudar sem aviso. Se os números pararem de aparecer,
> abra uma [issue](https://github.com/Guilhermee19/claude-usage-tray/issues).

## Desinstalar

```powershell
.\install-windows.bat --uninstall     # Windows
```

```bash
bash install-linux.sh --uninstall     # Linux
```

Remove os atalhos, o início automático e o `.venv`. As preferências ficam na pasta de configuração acima.

## Desenvolvimento

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt   # Windows: .venv\Scripts\pip
python -m claude_usage_tray                                          # roda com console, vendo erros
python packaging/build.py                                            # gera dist/ClaudeUsage.exe
python packaging/make_icons.py                                       # regera assets/icon.png e icon.ico
```

```
claude_usage_tray/
├── app.py         # orquestra bandeja, polling, popup e configurações
├── usage_api.py   # leitura do token + endpoint de uso + status do serviço
├── tray_icon.py   # desenha os 5 estilos de ícone
├── popup.py       # popup no estilo macOS
├── settings.py    # janela de configurações
├── theme.py       # cores e helpers de desenho
├── system.py      # tudo que é específico de Windows/Linux
└── setup_cli.py   # atalhos de menu/autostart usados pelos instaladores
```

**Publicar uma versão:** crie uma tag `v*` (ex.: `git tag v1.0.0 && git push --tags`). O GitHub Actions gera
o `ClaudeUsage.exe` e anexa ao Release automaticamente.

## Licença

[MIT](LICENSE). Projeto independente, sem afiliação com a Anthropic. "Claude" é marca da Anthropic, PBC.
