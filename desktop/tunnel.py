"""Wrapper do Cloudflare Quick Tunnel (cloudflared).

Baixa o binário na primeira execução (~25 MB), sobe como subprocess apontando
pra http://127.0.0.1:<porta> e captura a URL pública aleatória que o
Cloudflare gera (algo.trycloudflare.com).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def cloudflared_path(home: Path) -> Path:
    """Caminho do cloudflared.exe.

    IMPORTANTE: este caminho é **per-PC**, nunca dentro do DESKTOP_HOME (que
    pode ser OneDrive). O cloudflared é uma ferramenta runtime, não user-data,
    e não deve ocupar sync na nuvem (são 50+ MB).

    - Frozen (.exe bundleado): retorna a cópia embarcada em _MEIPASS\\bin.
    - Dev: %LOCALAPPDATA%\\roll3d6\\bin\\cloudflared.exe (per-PC, persistente).

    O parâmetro ``home`` é mantido por compat de API mas ignorado.
    """
    _ = home  # API compat
    if getattr(sys, "frozen", False):
        bundled = _bundled_cloudflared()
        if bundled is not None:
            return bundled
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "roll3d6" / "bin" / "cloudflared.exe"
    return Path.home() / ".cache" / "roll3d6" / "cloudflared"


def _bundled_cloudflared() -> Optional[Path]:
    """No app frozen pelo PyInstaller, tenta achar cloudflared.exe embarcado."""
    if not getattr(sys, "frozen", False):
        return None
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return None
    candidate = Path(meipass) / "bin" / "cloudflared.exe"
    return candidate if candidate.exists() else None


def ensure_cloudflared(
    home: Path,
    progress: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """Garante que cloudflared.exe está em ``%APPDATA%\\roll3d6\\bin``.

    Ordem de tentativa:
    1. Já existe lá → retorna.
    2. Modo frozen e há uma cópia embarcada no bundle → copia.
    3. Cai pra download da release oficial do GitHub (~50 MB).
    """
    target = cloudflared_path(home)
    if target.exists() and target.stat().st_size > 0:
        return target

    # No modo frozen, cloudflared_path() já aponta direto pro bundle —
    # se chegou aqui é porque não está frozen OU o bundle sumiu.
    target.parent.mkdir(parents=True, exist_ok=True)
    bundled = _bundled_cloudflared()
    if bundled is not None:
        shutil.copy2(bundled, target)
        return target

    tmp = target.with_suffix(".exe.tmp")
    with urllib.request.urlopen(CLOUDFLARED_URL) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)
    tmp.replace(target)
    return target


class Tunnel:
    """Processo do cloudflared. Captura URL pública na stderr."""

    def __init__(self, home: Path, local_port: int):
        self.home = home
        self.local_port = local_port
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._on_url: Optional[Callable[[str], None]] = None

    def start(self, on_url: Optional[Callable[[str], None]] = None) -> None:
        """Sobe o cloudflared. ``on_url`` é chamado quando a URL aparece."""
        self._on_url = on_url
        exe = cloudflared_path(self.home)
        if not exe.exists():
            raise FileNotFoundError(
                f"cloudflared não encontrado em {exe}. "
                f"Chame ensure_cloudflared() antes."
            )
        cmd = [
            str(exe),
            "tunnel",
            "--no-autoupdate",
            "--url",
            f"http://127.0.0.1:{self.local_port}",
        ]
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )
        self._reader_thread = threading.Thread(
            target=self._read_output, daemon=True
        )
        self._reader_thread.start()

    def _read_output(self) -> None:
        assert self.process is not None
        log_path = self.home / "logs" / "cloudflared.log"
        with open(log_path, "a", encoding="utf-8") as log:
            for line in self.process.stdout or []:
                log.write(line)
                log.flush()
                if self.public_url:
                    continue
                match = TUNNEL_URL_RE.search(line)
                if match:
                    self.public_url = match.group(0)
                    if self._on_url:
                        try:
                            self._on_url(self.public_url)
                        except Exception:
                            pass

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
