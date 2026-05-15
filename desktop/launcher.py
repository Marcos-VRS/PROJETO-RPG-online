"""Entry point do app desktop roll3d6 RPG.

Orquestra: configura paths, roda migrate, sobe daphne, sobe cloudflared,
abre a janelinha de bandeja com as URLs.

Uso em dev (com .venv ativada):
    python -m desktop.launcher

Uso bundleado (depois do PyInstaller):
    roll3d6.exe
"""
from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from desktop import lock, runtime_config, server, tunnel, ui


def _setup_django() -> None:
    """Importa Django, roda migrate, cria superuser default se DB vazio."""
    import django  # noqa: WPS433

    django.setup()

    from django.core.management import call_command  # noqa: WPS433

    call_command("migrate", "--noinput", verbosity=0)

    from django.contrib.auth import get_user_model  # noqa: WPS433

    User = get_user_model()
    if not User.objects.exists():
        # Superuser default — usuário muda a senha depois pelo admin.
        User.objects.create_superuser(
            username="admin",
            email="admin@local.test",
            password="admin",
        )


def _set_tunnel_url_in_settings(url: str) -> None:
    """Após capturar a URL pública, registra ela em CSRF/CORS trusted origins."""
    from django.conf import settings  # noqa: WPS433

    if url not in settings.CSRF_TRUSTED_ORIGINS:
        settings.CSRF_TRUSTED_ORIGINS.append(url)
    if url not in settings.CORS_ALLOWED_ORIGINS:
        settings.CORS_ALLOWED_ORIGINS.append(url)
    os.environ["ROLL3D6_TUNNEL_URL"] = url


def _run_as_daphne() -> int:
    """Modo subprocess: o próprio binário é re-invocado com --daphne pra
    rodar daphne sem precisar de python.exe externo. Necessário quando o
    app está bundleado pelo PyInstaller (sys.executable é o roll3d6.exe)."""
    # Strip "--daphne" pra daphne ver argv normal.
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    runtime_config.bootstrap_env()
    from daphne.cli import CommandLineInterface  # noqa: WPS433

    CommandLineInterface().run(sys.argv[1:])
    return 0


def main() -> int:
    # Modo daphne: o subprocess que serve HTTP.
    if len(sys.argv) >= 2 and sys.argv[1] == "--daphne":
        return _run_as_daphne()

    # 1. Bootstrap de paths e SECRET_KEY antes de importar Django.
    home = runtime_config.bootstrap_env()
    project_root = runtime_config.project_root()

    # 1.5. Trinco — previne abertura simultânea em outro PC que compartilha
    # o mesmo DESKTOP_HOME via OneDrive. Honor system com heartbeat.
    session_lock = lock.SessionLock(home)
    existing = session_lock.read_existing()
    if existing is not None:
        if not lock.ask_user_about_existing_lock(existing):
            return 0  # usuário escolheu esperar — sai limpo
        session_lock.acquire(force=True)
    else:
        session_lock.acquire()

    # 2. Configura Django, migra, cria admin.
    _setup_django()

    # 3. UI já visível durante boot (status "iniciando").
    api = ui.JsApi()
    api.home_path = str(home)
    api.cloud_sync = runtime_config.using_cloud_sync(home)

    # 4. Acha porta livre e sobe daphne.
    port = server.find_free_port(8000)
    local_url = f"http://127.0.0.1:{port}/"
    api.set_local_url(local_url)
    api.set_status("wait", f"iniciando servidor na porta {port}…")

    django_server = server.DjangoServer(project_root, home, port)
    django_server.start()

    def _boot_async():
        if not server.wait_ready(port, timeout=30):
            api.set_status("err", "servidor não respondeu em 30s")
            return
        api.set_status("wait", "baixando ferramenta de túnel…")
        try:
            tunnel.ensure_cloudflared(home)
        except Exception as exc:
            api.set_status("err", f"falha ao baixar cloudflared: {exc}")
            return
        api.set_status("wait", "criando túnel público…")

        t = tunnel.Tunnel(home, port)

        def _on_url(url: str) -> None:
            _set_tunnel_url_in_settings(url)
            api.set_public_url(url)

        t.start(on_url=_on_url)
        # Abre browser na URL local depois que tudo tá no ar.
        time.sleep(0.5)
        webbrowser.open(local_url)

        # Guarda o tunnel pra shutdown limpo.
        api._tunnel = t  # type: ignore[attr-defined]

    threading.Thread(target=_boot_async, daemon=True).start()

    # 5. Shutdown handler.
    def _shutdown() -> None:
        api.set_status("wait", "encerrando…")
        t = getattr(api, "_tunnel", None)
        if t is not None:
            t.stop()
        django_server.stop()
        session_lock.release()

    api.set_shutdown(_shutdown)

    # 6. UI bloqueia até janela fechar.
    ui.run_ui(api, on_close=_shutdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
