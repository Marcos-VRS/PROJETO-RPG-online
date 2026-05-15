# Arquitetura de distribuição desktop

> Documento vivo. Atualizar conforme decisões evoluírem. Pivô estrutural decidido em **2026-05-14**.

---

## Objetivo

Transformar o roll3d6 RPG em um aplicativo **desktop com instalação de dois cliques** para Windows. Qualquer pessoa baixa o `roll3d6-setup.exe`, dá dois cliques, espera instalar, e depois é só abrir o atalho que o site fica disponível — com **URL pública gerada automaticamente** que o mestre compartilha com os jogadores.

**Requisitos não-negociáveis:**
- Zero pré-requisitos no usuário final (sem Python, sem Postgres, sem Redis, sem nada).
- Zero terminal.
- Zero configuração de rede (port forwarding, firewall).
- Migração entre PCs = copiar uma pasta.

**Único atrito aceito:** SmartScreen do Windows na primeira execução (binário não-assinado). Resolução: usuário clica "Mais informações → Executar mesmo assim". Documentar no README do download.

---

## Arquitetura em camadas

```
┌──────────────────────────────────────────────────────────────────┐
│ roll3d6-setup.exe (instalador Inno Setup, ~150 MB)               │
│  ├─ bootstrap WebView2 Runtime (só se faltar — Win10)            │
│  ├─ copia roll3d6.exe + assets para %LOCALAPPDATA%\roll3d6\       │
│  ├─ cria atalho na área de trabalho + menu iniciar               │
│  └─ registra desinstalador                                       │
└──────────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ roll3d6.exe (PyInstaller --onefile --noconsole)                   │
│  Bundle:                                                          │
│  ├─ Python 3.13 runtime                                          │
│  ├─ Django 5.1 + daphne + channels + dependências                │
│  ├─ pywebview + WebView2 runtime hook                            │
│  ├─ Projeto roll3d6 (gurps/, project/, templates, static)         │
│  └─ cloudflared.exe (binário externo bundleado como recurso)      │
└──────────────────────────────────────────────────────────────────┘
                          ↓ (em runtime)
┌──────────────────────────────────────────────────────────────────┐
│ launcher.py (entry point)                                         │
│  1. Cria %APPDATA%\roll3d6\ se não existir                        │
│  2. Gera SECRET_KEY (primeira execução) → secret.key              │
│  3. python manage.py migrate (cria data.sqlite3 se não existir)   │
│  4. Cria superuser default na primeira execução                  │
│  5. Sobe daphne em 127.0.0.1:8000 (subprocess)                    │
│  6. Sobe cloudflared tunnel --url http://localhost:8000           │
│     captura URL pública da stdout (regex)                         │
│  7. Abre janelinha pywebview com status + URLs + botões           │
│  8. webbrowser.open('http://localhost:8000/')                     │
│  9. Loop: monitora daphne/cloudflared, mostra status, encerra     │
│     limpo no fechar janela                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de diretórios (em runtime na máquina do usuário)

```
%LOCALAPPDATA%\roll3d6\          ← instalado pelo setup, ImmutAvel pelo usuário
├── roll3d6.exe                   ← binário PyInstaller
└── unins000.exe                  ← desinstalador (gerado pelo Inno Setup)

%APPDATA%\roll3d6\                ← dados do usuário, ÚNICO ponto de backup
├── data.sqlite3                  ← banco completo (fichas, mesas, mensagens)
├── secret.key                    ← Django SECRET_KEY única por instalação
├── media/                        ← uploads (avatars, mapas, anexos)
│   ├── avatars/
│   └── mapas/
├── logs/                         ← logs do daphne e launcher
│   ├── daphne.log
│   └── launcher.log
└── config.json                   ← preferências (porta, abrir browser auto, etc.)
```

**Backup do usuário** = zipar `%APPDATA%\roll3d6\` inteiro. **Migração entre PCs** = restaurar esse zip no PC novo após instalar o app.

---

## Tooling escolhido

### Empacotamento Python → executável
**PyInstaller** (`--onefile --noconsole`).

- Motivo: maduro, documentação ampla, comunidade enorme, integra com pywebview/Django sem segredo.
- Alternativa considerada: **Briefcase** (BeeWare). Mais "app-oriented" mas menos suporte a Django + daphne; ecossistema menor. Reabrir se PyInstaller travar.
- Tamanho esperado do bundle: **80-150 MB** (Python + Django + deps + cloudflared).

### UI do launcher
**pywebview** (preliminar — confirmar em Fase 2).

- Motivo: usa o WebView2 nativo do Windows (já presente no Win11; bootstrap em Win10), dependência Python mínima, HTML/CSS pra layar a UI da janelinha.
- Alternativa: **PyQt6** (mais peso, ~50 MB extra, mas UI nativa); **Tkinter** (zero peso, UI feia mas funcional).
- Decisão final será tomada ao começar Fase 2 — pode mudar se pywebview der atrito com PyInstaller.

### Instalador
**Inno Setup** (gratuito, gera `.exe` instalador clássico Windows).

- Motivo: padrão de facto pra apps Windows não-corporativos, scripts simples (Pascal-like), suporta bootstrap de pré-requisitos (WebView2 Runtime), cria atalhos e desinstalador automaticamente.
- Alternativa: **WiX Toolset** (gera `.msi`, mais corporativo, curva de aprendizado maior).

### Túnel
**cloudflared** com Cloudflare Quick Tunnel.

- Comando: `cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate --metrics 127.0.0.1:0`.
- Saída na stderr inclui a URL pública (regex pra capturar: `https://[a-z-]+\.trycloudflare\.com`).
- Sem login, sem conta, sem token — URL aleatória por execução.
- Outbound-only: conexão sai da máquina do usuário pra Cloudflare; tráfego dos players entra de volta por essa mesma conexão. **Não passa por firewall de entrada.**

---

## Pipeline de build

```
1. .venv ativada
2. python -m PyInstaller desktop/roll3d6.spec
   gera dist/roll3d6.exe
3. iscc desktop/installer.iss
   gera dist/roll3d6-setup.exe
4. (Opcional, futuro) signtool sign /a dist/roll3d6-setup.exe
   exige certificado de assinatura
5. Distribuir dist/roll3d6-setup.exe
```

Tudo orquestrado por um script `desktop/build.ps1` (a criar em Fase 3) que executa os 4 passos em sequência.

---

## Mudanças necessárias no código Django

Mapeadas para Fase 1. Não-destrutivas (preservam o que existe):

1. **`project/settings.py`**
   - `SECRET_KEY` lido de `%APPDATA%\roll3d6\secret.key` no modo desktop (env var `ROLL3D6_MODE=desktop`).
   - `DATABASES.default.NAME` lido de `%APPDATA%\roll3d6\data.sqlite3` no modo desktop.
   - `MEDIA_ROOT` apontando pra `%APPDATA%\roll3d6\media`.
   - `CHANNEL_LAYERS` condicional: in-memory no modo desktop, Redis no modo legacy GCP.
   - `DEBUG=False` no modo desktop (é produto, não dev).
   - `ALLOWED_HOSTS=['*']` no modo desktop (necessário pro túnel) — segurança vem do fato de só quem tem a URL pública acessa.
   - `CSRF_TRUSTED_ORIGINS` populado dinamicamente com a URL do túnel quando capturada.

2. **Remover `rag` de `INSTALLED_APPS` e `project/urls.py`** (hibernação).

3. **`requirements.txt`**: remover `pgvector`, `psycopg`, `channels_redis`, `redis` (após confirmar que nada mais usa). Manter compatível com instalação no GCP legado até o sunset.

4. **Novo módulo `desktop/`**:
   - `desktop/launcher.py` — entry point.
   - `desktop/runtime_config.py` — gerencia `%APPDATA%`, SECRET_KEY, primeira execução.
   - `desktop/tunnel.py` — wraps `cloudflared`, captura URL.
   - `desktop/ui.py` — janelinha pywebview.
   - `desktop/roll3d6.spec` — spec do PyInstaller.
   - `desktop/installer.iss` — script Inno Setup.
   - `desktop/build.ps1` — orquestração.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| PyInstaller não consegue empacotar Django + templates corretamente | Spec explícito com `datas=` para `templates/`, `static/`, `media/templates iniciais`. Testar em VM limpa. |
| Cloudflare Tunnel rate-limit no Quick Tunnel | Documentar limite; pivô fácil pra túnel autenticado (sem mudança no código, só no comando). |
| WebView2 Runtime ausente no Win10 | Bootstrap incluído no Inno Setup baixa o instalador da MS se faltar. |
| Antivírus marcando `roll3d6.exe` como falso positivo (comum com PyInstaller) | Submeter ao Microsoft Defender e principais AVs pré-launch. Assinar binário quando tiver orçamento. |
| Conflito de porta 8000 (já em uso) | Launcher tenta 8000, fallback 8001, 8002, etc. Configurável em `config.json`. |
| Players atrás de NAT empresarial bloqueando `trycloudflare.com` | Documentar; raro mas possível em redes corporativas. Túnel autenticado com domínio próprio resolve. |
| SQLite locking sob concorrência alta | Ativar WAL mode no startup (`PRAGMA journal_mode=WAL`). Limita-se a ~10 conexões ativas (cenário típico). |
| Atualização do app no usuário final | Fase futura: auto-update via verificação de versão no startup, download de novo `roll3d6-setup.exe`. Por enquanto: re-instalar manual. |

---

## O que NÃO está nesta arquitetura (decisões adiadas)

- **Assinatura de código** — adiada até haver orçamento. SmartScreen permanece na primeira execução.
- **Auto-update** — primeira versão é manual (usuário baixa novo setup). Pode entrar como Fase 6 depois.
- **Mac / Linux** — primeira entrega é Windows-only. Mac/Linux entram só se demanda existir; arquitetura é compatível mas o tooling muda (Briefcase ou tooling nativo).
- **Versão "host na nuvem"** — o produto é desktop. Quem quiser hospedar fixo em VPS pessoal pode fazer manualmente, mas não é caminho oficial.
- **RAG (busca semântica de regras)** — em hibernação. Voltará com vector store SQLite-friendly (`sqlite-vss`, FAISS, ou alternativa).

Quando alguma dessas voltar à pauta, abrir documento de decisão próprio em `docs/` e linkar aqui.
