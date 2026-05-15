# Session State — onde parei e como continuar

> **Última sessão:** 2026-05-15 (noite).
> **Fase 4 concluída ✅** — dados de produção GCP estão no OneDrive local, 14 users + 2 campanhas + 16 fichas + 2014 mensagens + 109 arquivos de mídia.
>
> **Próxima sessão sugerida:** decidir entre (a) **Fase 5 — sunset GCP** (desligar a VM definitivamente, mas sem prazo) ou (b) features novas no app desktop.
>
> Quando voltar, leia este documento primeiro.

---

## Pivô estrutural de 2026-05-14

O produto deixou de ser SaaS hospedado no GCP e virou **aplicativo desktop com dois cliques** (Windows). Detalhes em [`AGENT_PROMPT.md`](AGENT_PROMPT.md) e [`DESKTOP_DISTRIBUTION.md`](DESKTOP_DISTRIBUTION.md). Resumo das decisões:

| Decisão | Escolha |
|---|---|
| Banco do produto | SQLite (`%APPDATA%\roll3d6\data.sqlite3`) |
| Multiplayer | Cloudflare Quick Tunnel (URL rotária por sessão) |
| Channel layer | InMemoryChannelLayer (sem Redis) |
| Empacotamento | PyInstaller `--onedir --noconsole` + Inno Setup |
| UI do launcher | pywebview (HTML/CSS embutido) |
| Destino do SaaS GCP | Sunset gradual (congelado, desligado quando desktop maduro) |
| Assinatura de código | Adiada (SmartScreen na 1ª execução é aceito) |
| RAG | **Hibernado** — código preservado, comentado em INSTALLED_APPS e urls.py |

---

## Estado das fases

| Fase | Descrição | Status |
|---|---|---|
| 0 | Reset de documentação | ✅ concluída |
| 1 | venv Windows + Django/SQLite local funcionando | ✅ concluída, validada visualmente |
| 2 | Launcher (daphne + cloudflared + UI pywebview) | ✅ concluída, validada |
| 3 | Empacotamento PyInstaller (`dist\roll3d6\roll3d6.exe`) | ✅ concluída |
| 3.5 | Inno Setup → `roll3d6-setup.exe` | ✅ concluída + ícone dos 3 dados |
| 3.6 | OneDrive sync + lock file (`session.lock`) | ✅ concluída |
| 3.7 | Commits do trabalho (4 commits limpos em `main`) | ✅ concluída |
| 3.8 | Fix `/media/` em desktop mode (commit `e013ed6`) | ✅ concluída |
| 4 | Migração de dados GCP Postgres → SQLite desktop | ✅ concluída |
| 4.5 | Deletar bucket descartável `gs://onyx-antler-452215-k1-tmp` | 🟡 pendente (comando preparado, falta usuário rodar) |
| 5 | Sunset GCP (banner + export + desligar VM) | ⏳ não começado (sem prazo) |

---

## O que existe no repo hoje (uncommitted)

**Modificados:**
- `CLAUDE.md` — índice atualizado para o pivô desktop
- `requirements.txt` — removido `channels_redis`/`redis`, adicionado `pywebview`. Em UTF-8 sem BOM (era UTF-16 antes — armadilha que travou o pip).
- `project/settings.py` — múltiplas adições condicionais ao modo desktop (ver "Mudanças principais em settings.py" abaixo)
- `project/urls.py` — `rag.urls` comentado
- `docs/AGENT_PROMPT.md` — reescrito
- `docs/RAG_ARCHITECTURE.md` — prefixado com nota de hibernação
- `docs/SESSION_STATE.md` — este arquivo
- `.gitignore` — adicionada exceção `!desktop/roll3d6.spec` + `/build/` + `warn-*.txt` + `xref-*.html`

**Novos:**
- `docs/DESKTOP_DISTRIBUTION.md` — arquitetura completa do instalador
- `desktop/` — pacote do launcher (ver árvore abaixo)
- `static/` — gerado por `collectstatic`, **gitignored**
- `db.sqlite3` na raiz — banco do dev em modo `python manage.py runserver`, **gitignored**
- `%APPDATA%\roll3d6\` (FORA do repo) — banco do modo desktop com:
  - `data.sqlite3` (admin user: `admin` / senha `admin`)
  - `secret.key` — chave Django
  - `bin\cloudflared.exe` (~50 MB, baixado uma vez)
  - `logs\daphne.log`, `logs\cloudflared.log`

**Bundle pronto:**
- `dist\roll3d6\roll3d6.exe` — 18 MB, com pasta `_internal` de ~114 MB. Total ~132 MB. **Gitignored**, gerar com `desktop\build.ps1`.

### Árvore de `desktop/`

```
desktop/
├── __init__.py
├── launcher.py            # entry point: orquestra setup_django + server + tunnel + ui
├── runtime_config.py      # %APPDATA%\roll3d6, SECRET_KEY auto-gerada
├── server.py              # spawn de daphne (subprocess) — frozen-aware
├── tunnel.py              # cloudflared: bundle-first, fallback download
├── ui.py                  # janelinha pywebview com HTML+JS inline
├── roll3d6.spec           # PyInstaller spec (com django.setup() no header)
├── build.ps1              # collectstatic + pyinstaller num comando só
├── _smoketest.py          # teste manual: config + porta + download cloudflared
└── _e2e_test.py           # teste manual: pipeline E2E headless (sem UI)
```

Os arquivos `_smoketest.py` e `_e2e_test.py` são utilitários de debug — podem ser mantidos ou removidos, não rodam automaticamente.

---

## Mudanças principais em `project/settings.py`

Tudo controlado por **uma única env var**: `ROLL3D6_DESKTOP_HOME`. Quando setada (sempre que o launcher inicia), ativa o modo desktop.

```python
DESKTOP_HOME = Path(os.environ.get("ROLL3D6_DESKTOP_HOME") or "") or None
```

Comportamento condicional:

| Setting | Modo dev (sem var) | Modo desktop dev (var setada, não-frozen) | Modo bundleado (var + frozen) |
|---|---|---|---|
| `SECRET_KEY` | hardcoded | de `%APPDATA%\roll3d6\secret.key` | idem |
| `DEBUG` | True | False | False |
| `ALLOWED_HOSTS` | lista fixa | `["*"]` | `["*"]` |
| `DATABASES.default.NAME` | `BASE_DIR/db.sqlite3` | `%APPDATA%\roll3d6\data.sqlite3` | idem |
| `MEDIA_ROOT` | `BASE_DIR/media` | `%APPDATA%\roll3d6\media` | idem |
| `CHANNEL_LAYERS` | InMemory (default) | InMemory | InMemory |
| `STATICFILES_STORAGE` | manifest | `StaticFilesStorage`+`USE_FINDERS` | `CompressedStaticFilesStorage` |
| `STATIC_ROOT` | `BASE_DIR/static` | idem | `_MEIPASS/static` |
| `CSRF_TRUSTED_ORIGINS` | domínio prod | localhost + `ROLL3D6_TUNNEL_URL` se presente | idem |

Modo `gcp_legacy` (Redis): ativado por `ROLL3D6_MODE=gcp_legacy`. Não usado em dev/desktop.

---

## Como rodar / testar (cheat sheet)

```powershell
# Pré-requisito: estar em PROJETO-RPG-online com .venv ativada.
.\.venv\Scripts\Activate.ps1

# 1. Modo dev clássico (db.sqlite3 na raiz, DEBUG=True)
python manage.py runserver

# 2. Modo desktop em dev (não-bundleado) — sobe launcher com UI
python -m desktop.launcher

# 3. Teste E2E headless (sem UI) do pipeline launcher
python -m desktop._e2e_test

# 4. Rebuild do .exe completo
.\desktop\build.ps1
# saída: dist\roll3d6\roll3d6.exe

# 5. Rodar o .exe bundleado
Start-Process dist\roll3d6\roll3d6.exe
```

---

## Gotchas descobertos nesta sessão (não esquecer)

1. **PyInstaller + Django: `collect_submodules('gurps')` falha silenciosamente** se Django não está configurado quando o spec é avaliado. Sintoma: `App 'gurps' doesn't have a 'RegisterUser' model` no startup do bundle. **Fix:** o spec faz `django.setup()` no header antes de `collect_submodules`. **Plus** lista explícita de `gurps.*` como rede de segurança.
2. **`requirements.txt` UTF-16:** o arquivo veio de outra máquina em UTF-16-LE com BOM, pip parsava errado. Reescrito em UTF-8 puro. Se algum script futuro reescrever via PowerShell `Out-File`, **passar `-Encoding utf8`** ou usar `[System.IO.File]::WriteAllText` com `UTF8Encoding($false)`.
3. **Whitenoise + DEBUG=False sem collectstatic:** em modo dev-launcher (não-frozen), `WHITENOISE_USE_FINDERS=True` resolve. Em modo bundleado, precisa de `collectstatic` em **build-time** (o `build.ps1` cuida disso) e `STATIC_ROOT=_MEIPASS/static`.
4. **Sandbox do Claude Code não eleva UAC:** `Start-Process -Verb RunAs` falha silenciosa. Comandos que precisam de admin (WSL, certbot, etc.) o usuário tem que rodar manualmente.
5. **`*.spec` no .gitignore:** o template Python padrão ignora todos os `.spec`, mas precisamos do `desktop/roll3d6.spec` em commit. Adicionada exceção `!desktop/roll3d6.spec`.
6. **`daphne` subprocess no .exe frozen:** `sys.executable` aponta pro próprio `roll3d6.exe`. Subprocess passaria `--daphne` como flag — o `launcher.main()` detecta esse arg e executa `daphne.cli` em vez de abrir a UI de novo.
7. **`tar.exe` nativo do Windows corrompe nomes UTF-8:** ao extrair `.tar.gz` com nomes acentuados (Episódio, Guardião, etc.), arquivos ficam com mojibake (`Epis├│dio_01.jpg`) e o Django serve 404. **Fix:** usar `tarfile` do Python (que respeita UTF-8 nativo). Vale lembrar quando implementar import wizard (#21).
8. **GCP VM com OS Login ativo:** metadata SSH keys e arquivos `authorized_keys` são ignorados — auth força conta Google. Pra rodar `gcloud` com permissão de owner, fazer `gcloud auth login --no-launch-browser` na VM. Browser SSH funciona sempre.
9. **Browser SSH ⚙️ Download File** é uma flaky — popup pode fechar instantâneo sem erro visível, JSON abre inline em vez de baixar. Mais confiável: `gcloud storage cp` pra bucket descartável + download pelo Console UI.
10. **`/media/` em desktop mode com `DEBUG=False`:** Django não anexa rota automaticamente. Precisa de `django.views.static.serve` explícito em `urls.py` (commit `e013ed6`).

---

## Como ficou o fluxo de import (referência pro futuro — task #21)

Quando for hora de transformar isso num **fluxo automático no launcher** (botão "Importar backup" na UI):

1. UI pede um arquivo `.json` (Django dumpdata) e opcionalmente um `.tar.gz` (mídia).
2. Backup automático do `data.sqlite3` atual pra `data.sqlite3.bak_<timestamp>`.
3. `migrate` no banco atual (idempotente — só roda se faltar migration).
4. `loaddata <arquivo.json>` — usa `django.core.management.call_command`.
5. Extração do tar com **`tarfile` do Python** (não shell `tar.exe`, que corrompe UTF-8).
6. Mostra resumo (counts por model) e pergunta se manter ou reverter pro backup.

Esse fluxo escapa toda a dança do GCP que fizemos manualmente nesta sessão.

---

## Como retomar Fase 4 (HISTÓRICO — Fase 4 já concluída em 2026-05-15)

Mantido aqui caso precise refazer um import futuro do GCP enquanto a VM ainda existir.

### 1. Verificar primeiro se os arquivos já estão no PC

Antes de tudo, Claude deve checar:
```powershell
Get-ChildItem "$env:USERPROFILE\Downloads\roll3d6_*"
```
Se aparecer `roll3d6_dump.json` e `roll3d6_media.tar.gz` → pula direto pro item 4 (loaddata).
Se não aparecer → seguir 2 e 3.

### 2. Reabrir a VM no GCP Console e o Browser SSH

1. **console.cloud.google.com** → ☰ → **Compute Engine** → **VM instances**.
2. Se a VM `roll3d6rpgvm` estiver **Stopped** (provável, porque usuário desligou pra economizar): marca o checkbox dela → clica **▶ Start / Resume** → espera "Running" (~30s).
3. Anota o **External IP** atual (pode ter mudado).
4. Na linha da VM, clica em **SSH** (terceira coluna pela direita) → abre janelinha de Browser SSH.

### 3. Regenerar o dump (caso /tmp tenha sido limpo) e baixar

Cola este bloco no Browser SSH — primeiro confirma se os arquivos ainda existem; se não, refaz:

```bash
# Se /tmp ainda tem os arquivos da sessão anterior, pula direto pro download.
ls -lh /tmp/roll3d6_dump.json /tmp/roll3d6_media.tar.gz 2>&1

# Se NÃO encontrou, rode o script abaixo pra regenerar:
cd /home/marcosvrsdevmail/roll3d6rpgapp
for d in venv .venv env; do [ -f "$d/bin/activate" ] && source "$d/bin/activate" && break; done
python manage.py dumpdata \
  --natural-foreign --natural-primary --indent 2 \
  --exclude=contenttypes --exclude=auth.permission \
  --exclude=admin.logentry --exclude=sessions.session \
  --exclude=rag \
  > /tmp/roll3d6_dump.json && echo "dump OK"
[ -d media ] && tar czf /tmp/roll3d6_media.tar.gz media/ && echo "media OK"
ls -lh /tmp/roll3d6_dump.json /tmp/roll3d6_media.tar.gz
```

**Download (a parte que ficou pendente!):**

Na janela do Browser SSH, no canto **SUPERIOR DIREITO** tem ícone de **engrenagem (⚙️)**. Sequência:

1. Clica no ⚙️ → escolhe **"Download file"** no menu suspenso
2. Abre um campo de texto → digita `/tmp/roll3d6_dump.json` → clica **Download**
3. O browser baixa pro `Downloads\` (padrão do Chrome/Edge)
4. Repete pro segundo arquivo: ⚙️ → Download file → `/tmp/roll3d6_media.tar.gz` → Download

**Verificação:**
- Os 2 arquivos devem aparecer em `C:\Users\marco\Downloads\`
- `roll3d6_dump.json` ~ alguns MB (texto JSON)
- `roll3d6_media.tar.gz` ~ tamanho variável dependendo do volume de imagens

### 4. Importar no SQLite limpo de teste (Claude executa)

1. **Importar num SQLite limpo de teste primeiro** (não tocar no `%OneDrive%\roll3d6\data.sqlite3` ainda). Caminho sugerido: `%LOCALAPPDATA%\Temp\roll3d6_import_test\`.
2. Comandos esperados:
   ```powershell
   $env:ROLL3D6_DESKTOP_HOME = "$env:LOCALAPPDATA\Temp\roll3d6_import_test"
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py loaddata $env:USERPROFILE\Downloads\roll3d6_dump.json
   tar -xzf "$env:USERPROFILE\Downloads\roll3d6_media.tar.gz" -C "$env:ROLL3D6_DESKTOP_HOME"
   ```
3. Validar: subir runserver, abrir admin, conferir que usuários/fichas/campanhas vieram.
4. Se OK: ou faz o mesmo no `%OneDrive%\roll3d6\` real, ou implementa o fluxo "importar dados" na primeira execução do launcher (task #21).
5. Documentar o fluxo em `DESKTOP_DISTRIBUTION.md`.
6. Depois disso, **lembrar de pedir o usuário pra desligar a VM no Console** (economia GCP) já que a Fase 4 técnica estará concluída.

**Pontos de atenção previstos:**
- Conteúdo `contenttypes` foi excluído do dump — IDs no SQLite vão diferir do Postgres. Se algum modelo tem FK direta pra ContentType (raro), pode quebrar. Verificar.
- `AUTH_USER_MODEL = "gurps.RegisterUser"` precisa estar registrado antes do loaddata. O `migrate` garante isso.
- Senhas dos usuários antigos vêm hasheadas no dump — funcionam direto no SQLite (Django re-hidrata).
- Mídias com caminho absoluto da VM (`/home/marcosvrsdevmail/...`) precisam ser ajustadas pra `%OneDrive%\roll3d6\media\`. Verificar campos de imagem nos models e ajustar paths se necessário.

---

## Roadmap remanescente (depois da Fase 3.5)

### Fase 4 — Migração de dados GCP → desktop
- Script de export na VM: `python manage.py dumpdata --natural-foreign --natural-primary` filtrando por `gurps.*`.
- Copiar pasta `media/` da VM (avatars, mapas, fichas com upload).
- Fluxo de "primeira execução" no app desktop: opção "começar do zero" ou "importar dados exportados" (apontar para `.json` + pasta `media/`).
- Testar com dump real da produção.

### Fase 5 — Distribuição + sunset GCP
- Banner no site SaaS GCP avisando descontinuação + link do download.
- Botão de export por usuário no site SaaS (gera `.json` + zip de mídias do usuário).
- Acompanhar migrações.
- Após prazo (a definir): parar daphne na VM, desligar VM, liberar recursos GCP.

---

## Notas operacionais preservadas

- **GCP VM (`35.239.231.110`, banco `roll3d6_data_base`)** está congelada. Não evoluir, só patches críticos. SSH continua via chave cadastrada no metadata.
- **Chave OpenAI** no `~/.roll3d6_secrets` da VM GCP — não é usada hoje.
- **Banco de produção GCP** continua autoritativo até a migração da Fase 4.
- **Máquina local:** Windows 11 Pro, Python 3.13.7, GPU RTX 1000 Ada (não usada hoje, fica útil quando RAG voltar com SQLite-vss).
