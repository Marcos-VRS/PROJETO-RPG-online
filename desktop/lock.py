"""Trinco digital pra prevenir abertura simultânea do app em dois PCs.

Modelo de uso (cenário típico — dois mestres, banco compartilhado via OneDrive):
- App grava ``session.lock`` no ``DESKTOP_HOME`` (que é sincronizado pra nuvem).
- A cada 2 min, faz heartbeat (re-grava o arquivo) — outro PC vê que app está vivo.
- Stale após 6 min sem heartbeat → assume que crashou/fechou e libera.
- Ao abrir, se o outro PC tem lock fresco: mostra MessageBox Yes/No nativo,
  usuário escolhe "Esperar" (sai) ou "Continuar mesmo assim" (força aquisição).

Limitações:
- OneDrive sincroniza arquivos com 5-60s de delay. Aberturas precisamente
  simultâneas dos dois PCs podem ambas pensar que o lock está livre.
  Honor system com cobertura razoável, não garantia transacional.
- Lock só protege contra colisão de escrita. Não impede dois apps lendo
  ao mesmo tempo (não é um problema).
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Optional

LOCK_FILENAME = "session.lock"
HEARTBEAT_INTERVAL_S = 120  # 2 min
STALE_AFTER_S = 360         # 6 min — se sem heartbeat por mais que isso, libera


def _pc_name() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "?"


def _user_name() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "?"


class SessionLock:
    """Lock cooperativo via arquivo no DESKTOP_HOME (compartilhado via cloud)."""

    def __init__(self, home: Path):
        self.home = home
        self.path = home / LOCK_FILENAME
        self.acquired = False
        self._stop_hb = threading.Event()
        self._hb_thread: Optional[threading.Thread] = None

    # ---- inspeção ------------------------------------------------------------

    def read_existing(self) -> Optional[dict]:
        """Lê o lock existente. Retorna None se não há lock ou se está stale."""
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            # Lock corrompido — trata como livre.
            return None

        last_hb = float(data.get("heartbeat") or 0)
        if time.time() - last_hb > STALE_AFTER_S:
            return None  # stale, livre

        # Se for nosso próprio lock (mesmo PC + mesmo PID), ignora.
        if data.get("pc") == _pc_name() and int(data.get("pid") or -1) == os.getpid():
            return None

        return data

    # ---- aquisição -----------------------------------------------------------

    def acquire(self, force: bool = False) -> bool:
        """Tenta adquirir o lock.

        Retorna True se conseguiu. Se force=False e outro PC tem lock fresco,
        retorna False. force=True sobrescreve sempre.
        """
        if not force:
            existing = self.read_existing()
            if existing is not None:
                return False

        self._write()
        self.acquired = True
        self._start_heartbeat()
        return True

    def _write(self) -> None:
        payload = {
            "pc": _pc_name(),
            "user": _user_name(),
            "pid": os.getpid(),
            "started": getattr(self, "_started_at", None) or time.time(),
            "heartbeat": time.time(),
        }
        self._started_at = payload["started"]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".lock.tmp")
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            # Conflito raro de I/O do OneDrive — ignora, próximo heartbeat tenta.
            pass

    def _start_heartbeat(self) -> None:
        def beat() -> None:
            while not self._stop_hb.wait(HEARTBEAT_INTERVAL_S):
                if self.acquired:
                    self._write()

        self._hb_thread = threading.Thread(target=beat, daemon=True, name="lock-heartbeat")
        self._hb_thread.start()

    # ---- liberação -----------------------------------------------------------

    def release(self) -> None:
        self._stop_hb.set()
        if not self.acquired:
            return
        self.acquired = False
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                # Só apaga se o lock ainda é nosso (outro PC pode ter forçado).
                if data.get("pc") == _pc_name() and int(data.get("pid") or -1) == os.getpid():
                    self.path.unlink()
        except Exception:
            pass


# ---- diálogo nativo Windows -------------------------------------------------

def _format_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s atrás"
    if seconds < 3600:
        return f"{int(seconds / 60)} min atrás"
    return f"{int(seconds / 3600)} h atrás"


def ask_user_about_existing_lock(existing: dict) -> bool:
    """Mostra MessageBox nativo. Retorna True se usuário escolher continuar."""
    pc = existing.get("pc", "?")
    user = existing.get("user", "?")
    started = float(existing.get("started") or 0)
    last_hb = float(existing.get("heartbeat") or 0)
    now = time.time()
    started_str = time.strftime("%H:%M de %d/%m", time.localtime(started)) if started else "?"
    hb_age = _format_age(now - last_hb) if last_hb else "?"

    body = (
        f"O app já está aberto em outro PC.\n\n"
        f"PC: {pc}\n"
        f"Usuário: {user}\n"
        f"Aberto desde: {started_str}\n"
        f"Última atividade: {hb_age}\n\n"
        f"Abrir aqui também pode CORROMPER o banco de dados durante a "
        f"sincronização do OneDrive.\n\n"
        f"Deseja continuar mesmo assim?"
    )

    if os.name != "nt":
        # Em dev no Linux/Mac (improvável) — apenas printa e assume "não".
        print(f"[lock] {body}")
        return False

    try:
        import ctypes

        # MB_YESNO=0x4 | MB_ICONWARNING=0x30 | MB_DEFBUTTON2=0x100 (default = NÃO)
        MB_FLAGS = 0x4 | 0x30 | 0x100
        IDYES = 6
        result = ctypes.windll.user32.MessageBoxW(
            0, body, "roll3d6 — App já está em uso", MB_FLAGS
        )
        return result == IDYES
    except Exception:
        return False
