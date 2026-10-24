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
import socket
import subprocess
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


def _run_as_imagegen_worker() -> int:
    """Modo subprocess: roda o worker do Estúdio de Imagem (ComfyUI). Chamado
    via `roll3d6.exe --imagegen-worker`. Chama o handle do management command
    direto (evita a descoberta de commands, que falha no app bundleado)."""
    runtime_config.bootstrap_env()
    import django  # noqa: WPS433

    django.setup()
    from gurps.management.commands.imagegen_worker import Command  # noqa: WPS433
    from gurps import comfyui_client  # noqa: WPS433

    try:
        Command().handle(
            interval=3.0, url=comfyui_client.DEFAULT_URL,
            ckpt=comfyui_client.DEFAULT_CKPT, timeout=300, once=False,
            claude="claude", model="sonnet",
        )
    except KeyboardInterrupt:
        pass
    return 0


def _run_as_videogen_worker() -> int:
    """Modo subprocess: roda o worker do Estúdio de Vídeo (AnimateDiff + ffmpeg).
    Chamado via `roll3d6.exe --videogen-worker`."""
    runtime_config.bootstrap_env()
    import django  # noqa: WPS433

    django.setup()
    from gurps.management.commands.videogen_worker import Command  # noqa: WPS433
    from gurps import comfyui_client  # noqa: WPS433

    try:
        Command().handle(
            interval=4.0, url=comfyui_client.DEFAULT_URL, timeout=900,
            claude="claude", model="sonnet", once=False,
        )
    except KeyboardInterrupt:
        pass
    return 0


def _spawn_worker(project_root: Path, home: Path, flag: str):
    """Sobe um worker como subprocess (ao lado do daphne). Genérico pro flag dado."""
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, flag]
    else:
        cmd = [sys.executable, "-m", "desktop.launcher", flag]
    env = dict(os.environ)
    env["ROLL3D6_DESKTOP_HOME"] = str(home)
    env.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        return subprocess.Popen(
            cmd, cwd=str(project_root), env=env, creationflags=creationflags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001
        return None


def _spawn_imagegen_worker(project_root: Path, home: Path):
    """Sobe o worker de imagem como subprocess (ao lado do daphne). Se o ComfyUI
    não estiver de pé, o worker só fica ocioso — não quebra nada."""
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--imagegen-worker"]
    else:
        cmd = [sys.executable, "-m", "desktop.launcher", "--imagegen-worker"]
    env = dict(os.environ)
    env["ROLL3D6_DESKTOP_HOME"] = str(home)
    env.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        return subprocess.Popen(
            cmd, cwd=str(project_root), env=env, creationflags=creationflags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001
        return None


def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _find_comfyui() -> "Path | None":
    """Acha a instalação portable do ComfyUI. Checa ROLL3D6_COMFYUI_HOME e os
    locais comuns. Precisa de python_embeded/python.exe + ComfyUI/main.py."""
    cands = []
    env = os.environ.get("ROLL3D6_COMFYUI_HOME")
    if env:
        cands.append(Path(env))
    userprofile = os.environ.get("USERPROFILE") or str(Path.home())
    cands += [
        Path(userprofile) / "ComfyUI_windows_portable",
        Path(userprofile) / "Desktop" / "ComfyUI_windows_portable",
        Path("C:/ComfyUI_windows_portable"),
    ]
    for c in cands:
        try:
            if (c / "python_embeded" / "python.exe").exists() and (c / "ComfyUI" / "main.py").exists():
                return c
        except Exception:  # noqa: BLE001
            continue
    return None


def _spawn_comfyui():
    """Sobe o ComfyUI junto do app (parte integrante). Se a porta 8188 já estiver
    em uso (ex. o usuário abriu o .bat), não duplica. Se não achar a instalação,
    só não sobe — os estúdios degradam pra 'offline' sem quebrar nada."""
    if _port_in_use(8188):
        return None
    comfy = _find_comfyui()
    if comfy is None:
        return None
    py = comfy / "python_embeded" / "python.exe"
    cmd = [str(py), "-s", str(comfy / "ComfyUI" / "main.py"),
           "--lowvram", "--port", "8188", "--disable-auto-launch"]
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        return subprocess.Popen(
            cmd, cwd=str(comfy), creationflags=creationflags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    # Modo daphne: o subprocess que serve HTTP.
    if len(sys.argv) >= 2 and sys.argv[1] == "--daphne":
        return _run_as_daphne()
    # Modo worker de imagem: subprocess que gera imagens via ComfyUI.
    if len(sys.argv) >= 2 and sys.argv[1] == "--imagegen-worker":
        return _run_as_imagegen_worker()
    # Modo worker de vídeo: subprocess que gera vídeos via AnimateDiff + ffmpeg.
    if len(sys.argv) >= 2 and sys.argv[1] == "--videogen-worker":
        return _run_as_videogen_worker()

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

    # ComfyUI como parte integrante: sobe junto do app (se instalado e não já
    # rodando). Fica idle até a 1ª geração; encerra no fim.
    comfy_proc = _spawn_comfyui()

    # Workers do Estúdio de Imagem e de Vídeo (ComfyUI). Ociosos se o ComfyUI
    # não estiver de pé.
    imagegen_proc = _spawn_imagegen_worker(project_root, home)
    videogen_proc = _spawn_worker(project_root, home, "--videogen-worker")

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
        for _proc in (imagegen_proc, videogen_proc, comfy_proc):
            if _proc is not None:
                try:
                    _proc.terminate()
                except Exception:  # noqa: BLE001
                    pass
        django_server.stop()
        session_lock.release()

    api.set_shutdown(_shutdown)

    # 6. UI bloqueia até janela fechar.
    ui.run_ui(api, on_close=_shutdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
