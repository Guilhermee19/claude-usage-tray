# Claude Usage Tray

Ícone na bandeja do Windows (ao lado de volume/wifi/bateria) com o uso do plano Claude:
sessão de 5h e limite semanal — os mesmos números do `/usage` do Claude Code.

## Rodar

```powershell
pip install -r requirements.txt
pythonw main.pyw        # sem console (use `python main.pyw` para ver erros)
```

- **Clique esquerdo:** abre/fecha o popup com os detalhes (sessão 5h, semanal, status do serviço).
- **Clique direito:** Atualizar agora, Ícone da barra, Configurações…, Iniciar com o Windows, Sair.
- **Ícone da barra:** anel (padrão), bateria, barra, porcentagem ou ponto — cada um colorido
  (uso em verde sobre cinza) ou monocromático. Escolha pelo menu ou em Configurações.
  O ponto muda de cor por nível (verde < 50%, amarelo < 80%, vermelho ≥ 80%). Cinza = sem dados/token expirado.
- Atualiza a cada 2 min (`interval_seconds` em `%APPDATA%\ClaudeUsageTray\config.json`).

## Deixar sempre visível

O Windows 11 esconde ícones novos atrás da setinha `^`. Para fixar:
**Configurações → Personalização → Barra de tarefas → Outros ícones da bandeja → ativar "Python"/"Claude Usage"**,
ou simplesmente arraste o ícone da área oculta para a barra.

## Como funciona

Lê o token OAuth de `~/.claude/.credentials.json` (só leitura — nunca renova o token,
quem faz isso é o Claude Code) e consulta `https://api.anthropic.com/api/oauth/usage`.
Se o token expirar, abra o Claude Code uma vez que ele renova e o ícone volta sozinho.
# claude-usage-tray
