"""Backup obrigatório do banco SQLite do app desktop.

Roda sempre: ao abrir o app (ANTES do migrate), a cada 30 min enquanto aberto
e ao fechar. Usa a API de backup do SQLite (cópia consistente mesmo com o banco
em uso, ao contrário de copiar o arquivo).

Cada backup é gravado em DOIS lugares, pra não depender só do OneDrive:
  1. ``<home>\\backups``                    (sincroniza junto com o banco)
  2. ``%LOCALAPPDATA%\\roll3d6\\backups``     (só neste PC, fora do OneDrive)

Retenção: os 20 mais recentes + o último de cada dia dos últimos 30 dias.
Falha de backup nunca derruba o app, mas é registrada em ``logs\\backup.log``.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

DB_NAME = "data.sqlite3"
KEEP_RECENT = 20
KEEP_DAILY_DAYS = 30
INTERVAL_SECONDS = 30 * 60
_PREFIX = "data-"
_SUFFIX = ".sqlite3"


def _log(home: Path, msg: str) -> None:
    try:
        logs = home / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        with open(logs / "backup.log", "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except OSError:
        pass


def backup_dirs(home: Path) -> list[Path]:
    dirs = [home / "backups"]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "roll3d6" / "backups")
    return dirs


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshots(folder: Path) -> list[Path]:
    return sorted(folder.glob(f"{_PREFIX}*{_SUFFIX}"), key=lambda p: p.name, reverse=True)


def _prune(folder: Path) -> None:
    snaps = _snapshots(folder)  # mais novo primeiro
    keep = set(snaps[:KEEP_RECENT])
    cutoff = datetime.now() - timedelta(days=KEEP_DAILY_DAYS)
    seen_days: set[str] = set()
    for p in snaps:
        stamp = p.name[len(_PREFIX):-len(_SUFFIX)]  # YYYYmmdd-HHMMSS
        try:
            when = datetime.strptime(stamp, "%Y%m%d-%H%M%S")
        except ValueError:
            keep.add(p)  # nome estranho: não apaga
            continue
        if when >= cutoff and stamp[:8] not in seen_days:
            seen_days.add(stamp[:8])
            keep.add(p)
    for p in snaps:
        if p not in keep:
            try:
                p.unlink()
            except OSError:
                pass


def backup_now(home: Path, reason: str = "") -> bool:
    """Faz um backup do banco. Retorna True se ao menos um destino foi gravado
    (ou se nada mudou desde o último). Nunca levanta exceção."""
    src = home / DB_NAME
    try:
        if not src.exists() or src.stat().st_size == 0:
            return True  # nada a salvar (1ª execução)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        tmp = src.with_name(f".{DB_NAME}.backup.tmp")
        if tmp.exists():
            tmp.unlink()
        # Cópia consistente via API do SQLite (o banco pode estar em uso).
        con = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True, timeout=30)
        try:
            dst = sqlite3.connect(str(tmp))
            try:
                con.backup(dst)
            finally:
                dst.close()
        finally:
            con.close()
        digest = _sha(tmp)
        ok = False
        for folder in backup_dirs(home):
            try:
                folder.mkdir(parents=True, exist_ok=True)
                snaps = _snapshots(folder)
                if snaps and _sha(snaps[0]) == digest:
                    ok = True  # idêntico ao último: não duplica
                    continue
                target = folder / f"{_PREFIX}{stamp}{_SUFFIX}"
                with open(tmp, "rb") as fi, open(target, "wb") as fo:
                    while chunk := fi.read(1 << 20):
                        fo.write(chunk)
                _prune(folder)
                ok = True
                _log(home, f"OK {reason} -> {target}")
            except OSError as exc:
                _log(home, f"FALHA {reason} em {folder}: {exc}")
        try:
            tmp.unlink()
        except OSError:
            pass
        if not ok:
            _log(home, f"FALHA {reason}: nenhum destino gravado")
        return ok
    except Exception as exc:  # noqa: BLE001
        _log(home, f"FALHA {reason}: {exc!r}")
        return False


def start_periodic(home: Path) -> threading.Event:
    """Backup a cada 30 min em thread daemon. Retorna o Event que para a thread."""
    stop = threading.Event()

    def _loop() -> None:
        while not stop.wait(INTERVAL_SECONDS):
            backup_now(home, "periodico")

    threading.Thread(target=_loop, daemon=True, name="db-backup").start()
    return stop
