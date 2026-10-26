# Sincronização direta com o OneDrive (API Graph)

O app envia/baixa o banco (`data.sqlite3`) e a pasta `media/` direto do OneDrive pela
internet, **sem precisar do programa OneDrive instalado ou logado no PC**. Código em
`desktop/cloud_sync.py`; ligado em `desktop/launcher.py`. Decisão do usuário em 2026-10-26.

## Como funciona

| Momento | O que acontece |
|---|---|
| Abrir | login (1ª vez por PC) → checa lock remoto → compara banco da nuvem com o local → baixa se a nuvem for mais nova → backup → migrate |
| Aberto | a cada 1 min envia o banco SE mudou; a cada 2 min renova o lock; a cada 10 min sincroniza mídia |
| Fechar | backup → envia banco + mídia → libera o lock remoto |

- Os arquivos ficam na pasta privada do app: `OneDrive\Apps\<nome do app no Azure>\`
  (permissão mínima `Files.ReadWrite.AppFolder` — o app não enxerga o resto do OneDrive).
- **Nunca sobrescreve sem backup** (`desktop/backup.py`: `<home>\backups` e `%LOCALAPPDATA%\roll3d6\backups`).
- **Conflito** (nuvem e este PC mudaram): pergunta SIM (usa a nuvem) / NÃO (mantém este PC); nada é apagado.
- Sem internet ou erro do Graph: avisa e abre com a cópia local. Nunca derruba o app.
- Estado e tokens por PC: `%LOCALAPPDATA%\roll3d6\{cloud_token.json,sync_state.json}` (fora da pasta de dados).
- Logs: `<home>\logs\cloud_sync.log`.

## Configuração única (Azure) — ~5 min

1. Entre em <https://portal.azure.com> com a conta Microsoft pessoal (a do OneDrive).
2. **Microsoft Entra ID → Registros de aplicativo → Novo registro**.
   - Nome: `roll3d6`
   - Tipos de conta: **"Contas pessoais da Microsoft apenas"** (ou "qualquer diretório e contas pessoais").
   - URI de redirecionamento: deixe em branco → **Registrar**.
3. **Autenticação → Configurações avançadas → "Permitir fluxos de cliente público" = Sim → Salvar.**
4. **Permissões de API → Adicionar → Microsoft Graph → Permissões delegadas →** `Files.ReadWrite.AppFolder`
   (e `offline_access`, se não estiver) → Adicionar. Não precisa de consentimento de administrador.
5. Na página **Visão geral**, copie o **ID do aplicativo (cliente)**.
6. Salve esse ID em `desktop/cloud_client_id.txt` (uma linha) e gere o instalador de novo
   (`desktop\build.ps1`). O ID não é segredo. Alternativas: variável `ROLL3D6_MS_CLIENT_ID`
   ou `<home>\cloud.json` com `{"client_id": "..."}`.

Primeira abertura em cada PC: abre o navegador com um código (já copiado — Ctrl+V), você entra
na conta Microsoft e aceita. Depois não pede mais.

## Limites

- Um PC por vez (SQLite é um arquivo só). O lock remoto avisa quando outro PC está com o app aberto.
- Precisa de internet ao abrir/fechar para sincronizar.
- Se a pasta de dados (`%OneDrive%\roll3d6`) também for sincronizada pelo programa OneDrive, há
  dupla sincronização. Prefira desligar um dos dois (ou definir `ROLL3D6_DESKTOP_HOME` fora do OneDrive).
- Testado só contra um servidor Graph falso (`scratchpad/test_cloud.py`); o 1º teste real com a conta
  Microsoft é do usuário.
