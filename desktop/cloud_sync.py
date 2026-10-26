"""Sincronização do banco e da mídia com o OneDrive via Microsoft Graph.

Não depende do programa OneDrive instalado/logado no PC: o app fala direto com a
API. Usa a pasta privada do app (``approot`` = ``OneDrive\\Apps\\<nome do app>``),
com a permissão mínima ``Files.ReadWrite.AppFolder``.

Fluxo (ver ``launcher.main``):
  abrir  -> ensure_login -> acquire_remote_lock -> pull -> (backup, migrate...)
  aberto -> a cada 1 min envia o banco se mudou; a cada 2 min renova o lock; a cada 10 min sincroniza mídia
  fechar -> push -> release_remote_lock

Configuração (opcional — sem client_id o módulo fica desligado e o app segue local):
  - env ``ROLL3D6_MS_CLIENT_ID`` ou ``<home>\\cloud.json`` {"client_id": "..."}
  Estado e tokens ficam em ``%LOCALAPPDATA%\\roll3d6`` (por PC, FORA da pasta sincronizada).

Regras de segurança dos dados:
  - Nunca sobrescreve o banco local sem antes fazer backup (desktop.backup).
  - Conflito (nuvem e PC mudaram) -> pergunta ao usuário; nada é apagado.
  - Falha de rede/Graph nunca derruba o app: loga e abre com a cópia local.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from desktop import backup

GRAPH = "https://graph.microsoft.com/v1.0"
AUTH = "https://login.microsoftonline.com/consumers/oauth2/v2.0"
SCOPES = "Files.ReadWrite.AppFolder offline_access"
DB_NAME = backup.DB_NAME
LOCK_NAME = "session.lock"
MEDIA_DIR = "media"
LOCK_STALE_S = 360
LOCK_BEAT_S = 60          # tique do loop: renova o lock (a cada 2 ticks) e envia o banco se mudou
MEDIA_EVERY_S = 10 * 60
SIMPLE_UPLOAD_MAX = 4 * 1024 * 1024
CHUNK = 320 * 1024 * 10  # múltiplo de 320 KiB, exigido pelo Graph


class CloudError(Exception):
    pass


def _local_state_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    d = Path(base) / "roll3d6"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _log(home: Path, msg: str) -> None:
    try:
        logs = home / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        with open(logs / "cloud_sync.log", "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except OSError:
        pass


def _message_box(title: str, body: str, yes_no: bool = False) -> bool:
    """MessageBox nativo. Retorna True para "Sim" (ou sempre True se não for yes_no)."""
    if os.name != "nt":
        print(f"[cloud] {title}: {body}")
        return False
    try:
        import ctypes

        flags = (0x4 | 0x20 | 0x100) if yes_no else (0x0 | 0x40)
        return ctypes.windll.user32.MessageBoxW(0, body, title, flags) in (6, 1)
    except Exception:  # noqa: BLE001
        return False


# ============================ autenticação ====================================

def _post_form(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:  # noqa: BLE001
            raise CloudError(f"HTTP {e.code} em {url}")


class TokenStore:
    """Tokens OAuth (device code) guardados por PC em %LOCALAPPDATA%."""

    def __init__(self, client_id: str, path: Optional[Path] = None):
        self.client_id = client_id
        self.path = path or (_local_state_dir() / "cloud_token.json")
        self._data: dict = {}
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            self._data = {}

    def logged_in(self) -> bool:
        return bool(self._data.get("refresh_token"))

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data), encoding="utf-8")

    def _apply(self, tok: dict) -> None:
        self._data = {
            "access_token": tok["access_token"],
            "refresh_token": tok.get("refresh_token") or self._data.get("refresh_token", ""),
            "expires_at": time.time() + int(tok.get("expires_in", 3600)),
        }
        self._save()

    def access_token(self) -> str:
        if self._data.get("access_token") and time.time() < self._data.get("expires_at", 0) - 120:
            return self._data["access_token"]
        rt = self._data.get("refresh_token")
        if not rt:
            raise CloudError("não logado no OneDrive")
        tok = _post_form(f"{AUTH}/token", {
            "client_id": self.client_id, "grant_type": "refresh_token",
            "refresh_token": rt, "scope": SCOPES})
        if "access_token" not in tok:
            self._data = {}
            self._save()
            raise CloudError(f"sessão do OneDrive expirou: {tok.get('error_description', tok)}")
        self._apply(tok)
        return self._data["access_token"]

    def login_device_code(self, home: Path) -> None:
        """Login único por PC: mostra um código, abre o navegador e espera."""
        dc = _post_form(f"{AUTH}/devicecode", {"client_id": self.client_id, "scope": SCOPES})
        if "device_code" not in dc:
            raise CloudError(f"falha ao iniciar login: {dc.get('error_description', dc)}")
        code, uri = dc["user_code"], dc["verification_uri"]
        try:  # copia o código pra área de transferência
            subprocess.run(["clip"], input=code.encode(), timeout=5, check=False)
        except Exception:  # noqa: BLE001
            pass
        webbrowser.open(uri)
        threading.Thread(target=_message_box, daemon=True, args=(
            "roll3d6 — conectar ao OneDrive",
            f"No navegador que abriu ({uri}), digite o código:\n\n{code}\n\n"
            f"(já copiado para a área de transferência — cole com Ctrl+V).\n"
            f"Entre com a sua conta Microsoft e aceite. Esta janela pode ser fechada.")).start()
        deadline = time.time() + int(dc.get("expires_in", 900))
        interval = int(dc.get("interval", 5))
        while time.time() < deadline:
            time.sleep(interval)
            tok = _post_form(f"{AUTH}/token", {
                "client_id": self.client_id,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": dc["device_code"]})
            if "access_token" in tok:
                self._apply(tok)
                _log(home, "login OneDrive concluído")
                return
            err = tok.get("error")
            if err == "slow_down":
                interval += 5
            elif err != "authorization_pending":
                raise CloudError(f"login recusado: {tok.get('error_description', err)}")
        raise CloudError("tempo esgotado esperando o login")


# ============================== Graph =========================================

class GraphClient:
    def __init__(self, token_provider: Callable[[], str], base: Optional[str] = None):
        self._token = token_provider
        self.base = base or GRAPH

    def _req(self, method, url, data=None, headers=None, auth=True, ok=(200, 201, 202, 204), retries=3):
        for attempt in range(retries):
            h = dict(headers or {})
            if auth:
                h["Authorization"] = "Bearer " + self._token()
            req = urllib.request.Request(url, data=data, method=method, headers=h)
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                body = e.read()
                if e.code == 404:
                    return 404, body
                if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise CloudError(f"Graph {method} {e.code}: {body[:200]!r}")
            except urllib.error.URLError as e:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise CloudError(f"sem conexão com o OneDrive: {e.reason}")
        raise CloudError("falha após tentativas")

    def _item(self, path: str) -> str:
        return f"{self.base}/me/drive/special/approot:/{urllib.parse.quote(path, safe='/')}"

    def meta(self, path: str) -> Optional[dict]:
        st, body = self._req("GET", self._item(path))
        return None if st == 404 else json.loads(body)

    def download(self, path: str, dest: Path) -> None:
        st, body = self._req("GET", self._item(path) + ":/content")
        if st == 404:
            raise CloudError(f"{path} não existe na nuvem")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)

    def upload(self, path: str, src: Path) -> dict:
        size = src.stat().st_size
        if size <= SIMPLE_UPLOAD_MAX:
            _, body = self._req("PUT", self._item(path) + ":/content", data=src.read_bytes(),
                                headers={"Content-Type": "application/octet-stream"})
            return json.loads(body)
        _, body = self._req("POST", self._item(path) + ":/createUploadSession",
                            data=json.dumps({"item": {"@microsoft.graph.conflictBehavior": "replace"}}).encode(),
                            headers={"Content-Type": "application/json"})
        url = json.loads(body)["uploadUrl"]
        result = b""
        with open(src, "rb") as fh:
            pos = 0
            while pos < size:
                chunk = fh.read(CHUNK)
                end = pos + len(chunk) - 1
                _, result = self._req("PUT", url, data=chunk, auth=False, headers={
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {pos}-{end}/{size}"})
                pos += len(chunk)
        return json.loads(result) if result else {}

    def delete(self, path: str) -> None:
        self._req("DELETE", self._item(path))

    def list_files(self, folder: str) -> dict[str, int]:
        """{caminho relativo à approot: tamanho} de todos os arquivos sob ``folder``."""
        out: dict[str, int] = {}
        stack = [folder]
        while stack:
            cur = stack.pop()
            url = self._item(cur) + ":/children?$top=200"
            while url:
                st, body = self._req("GET", url)
                if st == 404:
                    break
                data = json.loads(body)
                for it in data.get("value", []):
                    rel = f"{cur}/{it['name']}"
                    if "folder" in it:
                        stack.append(rel)
                    else:
                        out[rel] = int(it.get("size", 0))
                url = data.get("@odata.nextLink")
        return out


# ============================ orquestração ====================================

class CloudSync:
    def __init__(self, home: Path, client: GraphClient, tokens: Optional[TokenStore] = None,
                 state_path: Optional[Path] = None,
                 ask: Callable[[str, str], bool] = lambda t, b: _message_box(t, b, yes_no=True)):
        self.home = home
        self.client = client
        self.tokens = tokens
        self.ask = ask
        self.state_path = state_path or (_local_state_dir() / "sync_state.json")
        self._stop = threading.Event()
        self._push_lock = threading.Lock()
        self._pc = socket.gethostname()

    # ---- construção ---------------------------------------------------------

    @classmethod
    def from_env(cls, home: Path) -> Optional["CloudSync"]:
        """CloudSync pronto, ou None se não configurado (client_id ausente)."""
        cid = os.environ.get("ROLL3D6_MS_CLIENT_ID", "").strip()
        if not cid:  # client_id embutido no instalador (não é segredo: app "public client")
            try:
                from desktop import runtime_config
                cid = (runtime_config.project_root() / "desktop" / "cloud_client_id.txt").read_text(
                    encoding="utf-8").strip()
            except Exception:  # noqa: BLE001
                cid = ""
        if not cid:
            try:
                cid = json.loads((home / "cloud.json").read_text(encoding="utf-8")).get("client_id", "").strip()
            except Exception:  # noqa: BLE001
                cid = ""
        if not cid:
            _log(home, "desligado: sem client_id (ROLL3D6_MS_CLIENT_ID ou cloud.json)")
            return None
        tokens = TokenStore(cid)
        return cls(home, GraphClient(tokens.access_token), tokens)

    def ensure_login(self) -> bool:
        if self.tokens is None or self.tokens.logged_in():
            return True
        try:
            self.tokens.login_device_code(self.home)
            return True
        except CloudError as e:
            _log(self.home, f"login falhou: {e}")
            _message_box("roll3d6 — OneDrive", f"Não foi possível conectar ao OneDrive:\n{e}\n\n"
                         "O app abrirá com a cópia local, SEM sincronizar.")
            return False

    # ---- estado local -------------------------------------------------------

    def _load_state(self) -> Optional[dict]:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def _save_state(self, etag: str, snap_sha: str) -> None:
        self.state_path.write_text(json.dumps({"remote_etag": etag, "snapshot_sha": snap_sha}), encoding="utf-8")

    def _snapshot(self) -> Optional[Path]:
        """Cópia consistente do banco local (API de backup do SQLite) numa pasta temporária."""
        src = self.home / DB_NAME
        if not src.exists() or src.stat().st_size == 0:
            return None
        tmp = _local_state_dir() / "upload.snapshot.sqlite3"
        if tmp.exists():
            tmp.unlink()
        con = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True, timeout=30)
        try:
            dst = sqlite3.connect(str(tmp))
            try:
                con.backup(dst)
            finally:
                dst.close()
        finally:
            con.close()
        return tmp

    # ---- lock remoto --------------------------------------------------------

    def acquire_remote_lock(self) -> bool:
        """False se outro PC está com o app aberto e o usuário escolheu esperar."""
        try:
            m = self.client.meta(LOCK_NAME)
            if m:
                tmp = _local_state_dir() / "remote.lock"
                self.client.download(LOCK_NAME, tmp)
                data = json.loads(tmp.read_text(encoding="utf-8"))
                fresh = time.time() - float(data.get("heartbeat") or 0) <= LOCK_STALE_S
                if fresh and data.get("pc") != self._pc:
                    from desktop import lock  # import tardio: evita ciclo
                    if not lock.ask_user_about_existing_lock(data):
                        return False
            self._write_remote_lock()
        except CloudError as e:
            _log(self.home, f"lock remoto indisponível: {e}")
        return True

    def _write_remote_lock(self) -> None:
        tmp = _local_state_dir() / "local.lock"
        tmp.write_text(json.dumps({"pc": self._pc, "user": os.environ.get("USERNAME", "?"),
                                   "pid": os.getpid(), "started": time.time(),
                                   "heartbeat": time.time()}), encoding="utf-8")
        self.client.upload(LOCK_NAME, tmp)

    def release_remote_lock(self) -> None:
        try:
            self.client.delete(LOCK_NAME)
        except CloudError as e:
            _log(self.home, f"não liberou lock remoto: {e}")

    # ---- pull ---------------------------------------------------------------

    def pull(self) -> str:
        """Traz o banco da nuvem se for o caso. Retorna o que fez (pra log/testes)."""
        try:
            return self._pull()
        except CloudError as e:
            _log(self.home, f"pull falhou: {e}")
            _message_box("roll3d6 — OneDrive", f"Não foi possível sincronizar:\n{e}\n\n"
                         "O app abrirá com a cópia local deste PC.")
            return "erro"

    def _pull(self) -> str:
        remote = self.client.meta(DB_NAME)
        if remote is None:
            return "nuvem vazia"
        local = self.home / DB_NAME
        state = self._load_state()
        etag = remote.get("eTag", "")
        has_local = local.exists() and local.stat().st_size > 0
        snap = self._snapshot() if has_local else None
        local_sha = _sha_file(snap) if snap else None
        remote_changed = state is None or state.get("remote_etag") != etag
        local_changed = has_local and (state is None or state.get("snapshot_sha") != local_sha)

        if not remote_changed:
            return "sem mudança na nuvem"
        if has_local and local_changed:
            # Os dois lados têm dados diferentes: o usuário decide. Nada é apagado.
            use_cloud = self.ask(
                "roll3d6 — qual banco usar?",
                "Existe um banco na NUVEM e outro DIFERENTE neste PC.\n\n"
                "SIM  = usar o da NUVEM (o deste PC fica guardado em backup)\n"
                "NÃO  = manter o DESTE PC (ao fechar, ele substitui o da nuvem; "
                "o da nuvem fica guardado em backup)\n\n"
                "Dica: se este PC é novo/vazio, escolha SIM.")
            if not use_cloud:
                self._keep_remote_copy(remote, "nuvem-substituida")
                # estado = etag atual da nuvem, mas sem snapshot: força push no fechamento
                self._save_state(etag, "")
                return "mantido local"
            backup.backup_now(self.home, "antes-de-baixar-da-nuvem")
        elif has_local:
            backup.backup_now(self.home, "antes-de-baixar-da-nuvem")
        tmp = local.with_name(f".{DB_NAME}.download")
        self.client.download(DB_NAME, tmp)
        for ext in ("-wal", "-shm"):  # resíduos do banco antigo
            try:
                (self.home / (DB_NAME + ext)).unlink()
            except OSError:
                pass
        tmp.replace(local)
        snap2 = self._snapshot()
        self._save_state(etag, _sha_file(snap2) if snap2 else "")
        _log(self.home, f"banco baixado da nuvem (etag {etag})")
        return "baixado"

    def _keep_remote_copy(self, remote: dict, tag: str) -> None:
        try:
            dest = self.home / "backups" / f"nuvem-{datetime.now():%Y%m%d-%H%M%S}-{tag}.sqlite3"
            self.client.download(DB_NAME, dest)
        except Exception as e:  # noqa: BLE001
            _log(self.home, f"não guardou cópia da nuvem: {e}")

    # ---- push ---------------------------------------------------------------

    def push(self, include_media: bool = True) -> str:
        with self._push_lock:
            try:
                r = self._push_db()
                if include_media:
                    self._sync_media()
                return r
            except CloudError as e:
                _log(self.home, f"push falhou: {e}")
                return "erro"

    def _push_db(self) -> str:
        snap = self._snapshot()
        if snap is None:
            return "sem banco local"
        sha = _sha_file(snap)
        state = self._load_state()
        remote = self.client.meta(DB_NAME)
        if state and state.get("snapshot_sha") == sha and remote and remote.get("eTag") == state.get("remote_etag"):
            return "sem mudança"
        if remote and state and remote.get("eTag") != state.get("remote_etag"):
            # Alguém alterou a nuvem depois do nosso pull: guarda a cópia antes de sobrescrever.
            self._keep_remote_copy(remote, "sobrescrita-no-push")
        item = self.client.upload(DB_NAME, snap)
        self._save_state(item.get("eTag", ""), sha)
        _log(self.home, f"banco enviado à nuvem ({snap.stat().st_size} bytes)")
        return "enviado"

    def _sync_media(self) -> None:
        local_root = self.home / MEDIA_DIR
        remote = self.client.list_files(MEDIA_DIR)
        local: dict[str, int] = {}
        if local_root.exists():
            for p in local_root.rglob("*"):
                if p.is_file():
                    local[f"{MEDIA_DIR}/{p.relative_to(local_root).as_posix()}"] = p.stat().st_size
        for rel, size in local.items():
            if remote.get(rel) != size:
                self.client.upload(rel, self.home / rel)
        for rel in remote.keys() - local.keys():
            self.client.download(rel, self.home / rel)  # só traz o que falta; nunca apaga

    def pull_media(self) -> None:
        try:
            self._sync_media()
        except CloudError as e:
            _log(self.home, f"mídia: {e}")

    # ---- ciclo de vida ------------------------------------------------------

    def start_background(self) -> None:
        def loop() -> None:
            last_media = time.time()
            ticks = 0
            self.pull_media()
            while not self._stop.wait(LOCK_BEAT_S):
                ticks += 1
                if ticks % 2 == 0:
                    try:
                        self._write_remote_lock()
                    except CloudError as e:
                        _log(self.home, f"heartbeat do lock: {e}")
                # Quase tempo real: a cada 1 min envia o banco SE mudou (comparação por hash).
                media_due = time.time() - last_media >= MEDIA_EVERY_S
                self.push(include_media=media_due)
                if media_due:
                    last_media = time.time()

        threading.Thread(target=loop, daemon=True, name="cloud-sync").start()

    def shutdown(self) -> None:
        self._stop.set()
        self.push()
        self.release_remote_lock()
