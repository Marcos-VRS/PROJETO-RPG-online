"""Configuração de runtime do app desktop.

Resolve onde ficam os dados do usuário (%APPDATA%\\roll3d6 no Windows), gera o
SECRET_KEY na primeira execução, e expõe paths para os outros módulos.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def project_root() -> Path:
    """Raiz do checkout do Django (onde manage.py vive)."""
    # Quando empacotado pelo PyInstaller, sys.frozen é True e _MEIPASS é a temp dir.
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def app_home() -> Path:
    """Diretório de dados do usuário (banco, mídia, logs, secret).

    Ordem de preferência:
    1. Override via env var ``ROLL3D6_DESKTOP_HOME`` (útil pra testes).
    2. ``%OneDrive%\\roll3d6`` no Windows quando OneDrive está configurado —
       sync automático na nuvem permite trocar de PC sem perder fichas/mesas.
    3. ``%APPDATA%\\roll3d6`` (Windows sem OneDrive).
    4. ``~/.roll3d6`` (Linux/Mac em dev).
    """
    override = os.environ.get("ROLL3D6_DESKTOP_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        onedrive = os.environ.get("OneDrive")
        if onedrive:
            od_path = Path(onedrive)
            if od_path.exists():
                return od_path / "roll3d6"
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "roll3d6"
    return Path.home() / ".roll3d6"


def using_cloud_sync(home: Path) -> bool:
    """Heurística: a home está dentro do OneDrive do usuário?

    Usado pra mostrar na UI se os dados estão sendo sincronizados na nuvem.
    """
    onedrive = os.environ.get("OneDrive")
    if not onedrive:
        return False
    try:
        home.resolve().relative_to(Path(onedrive).resolve())
        return True
    except ValueError:
        return False


def ensure_dirs(home: Path) -> None:
    """Cria a estrutura de diretórios em %APPDATA%\\roll3d6."""
    home.mkdir(parents=True, exist_ok=True)
    (home / "media").mkdir(exist_ok=True)
    (home / "logs").mkdir(exist_ok=True)
    (home / "bin").mkdir(exist_ok=True)


def ensure_secret_key(home: Path) -> str:
    """Lê ou gera ``secret.key``. Garante 50 chars urlsafe random."""
    path = home / "secret.key"
    if path.exists():
        key = path.read_text(encoding="utf-8").strip()
        if key:
            return key
    key = secrets.token_urlsafe(64)
    path.write_text(key, encoding="utf-8")
    # Permissões: no Windows o ACL default já restringe a HOME do usuário;
    # em outras plataformas, restringir explicitamente.
    if os.name != "nt":
        os.chmod(path, 0o600)
    return key


def bootstrap_env() -> Path:
    """Configura env vars que o Django precisa antes do ``django.setup()``.

    Retorna o ``app_home`` resolvido.
    """
    home = app_home()
    ensure_dirs(home)
    ensure_secret_key(home)
    os.environ["ROLL3D6_DESKTOP_HOME"] = str(home)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    # Adiciona a raiz do projeto ao sys.path pra `import project.settings` funcionar.
    root = project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return home
