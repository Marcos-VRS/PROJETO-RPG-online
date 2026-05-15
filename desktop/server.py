"""Gerencia o subprocess do daphne (servidor ASGI do Django)."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


def find_free_port(preferred: int = 8000, fallbacks: int = 10) -> int:
    """Tenta a porta preferida; cai pra próximas até achar uma livre."""
    for offset in range(fallbacks + 1):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"Nenhuma porta livre entre {preferred} e {preferred + fallbacks}."
    )


def wait_ready(port: int, timeout: float = 30.0) -> bool:
    """Espera daphne aceitar conexões em 127.0.0.1:porta."""
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                _ = resp.status
                return True
        except urllib.error.URLError:
            time.sleep(0.3)
        except Exception:
            time.sleep(0.3)
    return False


class DjangoServer:
    """Spawn do daphne via subprocess apontando pro projeto."""

    def __init__(self, project_root: Path, app_home: Path, port: int):
        self.project_root = project_root
        self.app_home = app_home
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self._log_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        env = os.environ.copy()
        env["ROLL3D6_DESKTOP_HOME"] = str(self.app_home)
        env["DJANGO_SETTINGS_MODULE"] = "project.settings"

        # Frozen (PyInstaller): sys.executable é o roll3d6.exe — re-invoca-se
        # com a flag --daphne, que launcher.py detecta e roda daphne diretamente.
        # Dev: usa `python -m daphne` normal.
        if getattr(sys, "frozen", False):
            cmd = [
                sys.executable,
                "--daphne",
                "-b",
                "127.0.0.1",
                "-p",
                str(self.port),
                "project.asgi:application",
            ]
        else:
            cmd = [
                sys.executable,
                "-m",
                "daphne",
                "-b",
                "127.0.0.1",
                "-p",
                str(self.port),
                "project.asgi:application",
            ]
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        self.process = subprocess.Popen(
            cmd,
            cwd=str(self.project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )
        self._log_thread = threading.Thread(target=self._pipe_log, daemon=True)
        self._log_thread.start()

    def _pipe_log(self) -> None:
        assert self.process is not None
        log_path = self.app_home / "logs" / "daphne.log"
        with open(log_path, "a", encoding="utf-8") as log:
            for line in self.process.stdout or []:
                log.write(line)
                log.flush()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
