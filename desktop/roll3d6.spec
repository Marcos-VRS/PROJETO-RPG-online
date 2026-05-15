# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec do roll3d6 RPG (modo --onedir).

Build:  pyinstaller desktop/roll3d6.spec --clean --noconfirm
Saída:  dist/roll3d6/roll3d6.exe + DLLs e data files.

Notas:
- Modo onedir (não onefile): startup mais rápido, AV menos paranoico, debug
  mais fácil. O Inno Setup empacota a pasta inteira no instalador final.
- Inclui cópia local de cloudflared.exe (~50 MB) pra evitar download no
  primeiro launch. Se a cópia não existir em build time, o launcher cai
  no download por HTTP (rede necessária só na primeira execução nesse caso).
"""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

PROJECT_ROOT = Path(SPECPATH).parent.resolve()  # noqa: F821 (SPECPATH injetado pelo PyInstaller)

# ---------- Configura Django ANTES de collect_submodules ----------------------
# Sem isso, módulos como gurps.models e gurps.views falham ao importar (precisam
# de settings.INSTALLED_APPS configurado), e o collect_submodules os pula
# silenciosamente — bug silencioso clássico de Django + PyInstaller.
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
try:
    import django
    django.setup()
except Exception as exc:  # pragma: no cover
    print(f"[spec] aviso: django.setup() falhou — {exc}")

# ---------- Hidden imports ----------------------------------------------------
# Django descobre apps via INSTALLED_APPS em runtime; PyInstaller não enxerga
# essas importações estáticamente. Precisamos declarar tudo explicitamente.

hidden_imports: list[str] = []

# Rede de segurança: lista todos os submódulos do gurps na unha. Mesmo que
# collect_submodules retorne tudo, repetir aqui não machuca.
hidden_imports += [
    "gurps",
    "gurps.admin",
    "gurps.apps",
    "gurps.consumers",
    "gurps.forms",
    "gurps.models",
    "gurps.routing",
    "gurps.urls",
    "gurps.views",
]
for pkg in (
    "django",
    "channels",
    "daphne",
    "whitenoise",
    "allauth",
    "corsheaders",
    "django_htmx",
    "django_cleanup",
    "django_json_widget",
    "twisted",
    "autobahn",
    "gurps",
    "project",
):
    try:
        hidden_imports += collect_submodules(pkg)
    except Exception:  # pragma: no cover
        # Alguns pacotes podem ter submódulos com importação condicional;
        # ignoramos falhas e seguimos.
        pass

hidden_imports += [
    "project.settings",
    "project.urls",
    "project.asgi",
    "project.wsgi",
    "daphne.cli",
    "daphne.server",
    "channels.routing",
    "channels.layers",
    "channels.auth",
]

# ---------- Data files (templates, statics, migrations) -----------------------

datas: list[tuple[str, str]] = []

# Project-level templates e statics (referenciados via BASE_DIR no settings).
datas.append((str(PROJECT_ROOT / "base_templates"), "base_templates"))
datas.append((str(PROJECT_ROOT / "base_static"), "base_static"))

# Estáticos coletados em build-time. settings.py aponta STATIC_ROOT pra
# _MEIPASS\static no modo frozen; sem essa pasta, Whitenoise 404 em tudo.
# Gerar com:  python manage.py collectstatic --noinput --clear
collected_static = PROJECT_ROOT / "static"
if collected_static.exists():
    datas.append((str(collected_static), "static"))
else:
    print(f"[spec] AVISO: {collected_static} não existe. Rode `python manage.py collectstatic --noinput --clear` antes do build.")

# App gurps: templates, static, migrations, data fixtures.
for sub in ("templates", "static", "migrations", "data"):
    src = PROJECT_ROOT / "gurps" / sub
    if src.exists():
        datas.append((str(src), f"gurps/{sub}"))

# Migrations explícitas dos apps built-in do Django (collect_submodules nem
# sempre traz os arquivos .py das migrations como data; reforçamos aqui).
for pkg in (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
):
    try:
        datas += collect_data_files(pkg, subdir=None)
    except Exception:
        pass

# Templates do allauth (login, signup, etc.).
try:
    datas += collect_data_files("allauth", includes=["**/templates/**"])
except Exception:
    pass

# django-json-widget tem JS/CSS embutidos.
try:
    datas += collect_data_files("django_json_widget")
except Exception:
    pass

# cloudflared.exe — se existir no perfil do dev em build time, bundleia
# pra evitar download no primeiro launch.
import os
appdata = os.environ.get("APPDATA")
if appdata:
    cf_path = Path(appdata) / "roll3d6" / "bin" / "cloudflared.exe"
    if cf_path.exists():
        datas.append((str(cf_path), "bin"))

# ---------- Analysis ----------------------------------------------------------

a = Analysis(  # noqa: F821 (PyInstaller global)
    [str(PROJECT_ROOT / "desktop" / "launcher.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",     # usamos pywebview
        "rag",         # hibernado
        "pytest",
        "IPython",
        "jupyter",
        "notebook",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="roll3d6",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX comprime mas dispara false-positive em vários AVs.
    console=False,        # janela GUI; sem console preto atrás.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "desktop" / "icon.ico"),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="roll3d6",
)
