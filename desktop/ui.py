"""Janelinha de bandeja em pywebview com status + URLs + botões."""
from __future__ import annotations

import threading
import webbrowser
from typing import Callable, Optional

import webview

INDEX_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>roll3d6 RPG</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0; padding: 18px;
    background: #1a1c20; color: #e8e8e8;
    user-select: none;
  }
  h1 { font-size: 18px; margin: 0 0 12px 0; color: #f0c674; }
  .row { margin: 14px 0; }
  .label { font-size: 11px; text-transform: uppercase; color: #8a8e94; margin-bottom: 4px; letter-spacing: 0.05em; }
  .value {
    background: #2a2d33; border: 1px solid #3a3d43; border-radius: 4px;
    padding: 8px 10px; font-family: Consolas, monospace; font-size: 12px;
    word-break: break-all; user-select: text;
  }
  .status { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; }
  .status.ok { background: #2d5a3d; color: #b9f3c8; }
  .status.wait { background: #5a4d2d; color: #f3e5b9; }
  .status.err { background: #5a2d2d; color: #f3b9b9; }
  .buttons { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
  button {
    flex: 1; min-width: 110px;
    background: #3a3d43; color: #e8e8e8;
    border: 1px solid #4a4d53; border-radius: 4px;
    padding: 8px 12px; font-size: 12px; cursor: pointer;
  }
  button:hover { background: #4a4d53; }
  button.primary { background: #5a7a3d; border-color: #6a8a4d; }
  button.primary:hover { background: #6a8a4d; }
  button.danger { background: #7a3d3d; border-color: #8a4d4d; }
  button.danger:hover { background: #8a4d4d; }
</style>
</head>
<body>
  <h1>roll3d6 RPG <span id="status" class="status wait">iniciando…</span></h1>

  <div class="row">
    <div class="label">URL local (você)</div>
    <div class="value" id="local-url">aguardando servidor…</div>
  </div>

  <div class="row">
    <div class="label">URL pública (compartilhe com os jogadores)</div>
    <div class="value" id="public-url">criando túnel Cloudflare…</div>
  </div>

  <div class="row">
    <div class="label">dados <span id="cloud-badge" style="display:none; background:#2d4d5a; color:#b9e0f3; padding:1px 6px; border-radius:3px; font-size:9px; margin-left:6px;">OneDrive sync</span></div>
    <div class="value" style="font-size:11px;" id="home-path">…</div>
  </div>

  <div class="buttons">
    <button class="primary" onclick="pywebview.api.open_browser()">Abrir no navegador</button>
    <button onclick="pywebview.api.copy_public()">Copiar URL pública</button>
    <button class="danger" onclick="pywebview.api.shutdown()">Encerrar</button>
  </div>

<script>
  async function refresh() {
    try {
      const s = await pywebview.api.state();
      document.getElementById('local-url').textContent = s.local_url || 'aguardando…';
      document.getElementById('public-url').textContent = s.public_url || 'criando túnel…';
      document.getElementById('home-path').textContent = s.home_path || '';
      document.getElementById('cloud-badge').style.display = s.cloud_sync ? 'inline' : 'none';
      const st = document.getElementById('status');
      st.className = 'status ' + (s.status === 'ok' ? 'ok' : (s.status === 'err' ? 'err' : 'wait'));
      st.textContent = s.status_text;
    } catch (e) { /* pywebview ainda não bridge-ou */ }
  }
  setInterval(refresh, 800);
  refresh();
</script>
</body>
</html>
"""


class JsApi:
    """Bridge JS ↔ Python exposto pelo pywebview."""

    def __init__(self):
        self.local_url: Optional[str] = None
        self.public_url: Optional[str] = None
        self.status: str = "wait"  # ok | wait | err
        self.status_text: str = "iniciando…"
        self.home_path: str = ""
        self.cloud_sync: bool = False
        self._shutdown_cb: Optional[Callable[[], None]] = None
        self._window = None

    def attach_window(self, window) -> None:
        self._window = window

    def set_shutdown(self, cb: Callable[[], None]) -> None:
        self._shutdown_cb = cb

    def set_local_url(self, url: str) -> None:
        self.local_url = url

    def set_public_url(self, url: str) -> None:
        self.public_url = url
        if self.local_url:
            self.status = "ok"
            self.status_text = "tudo pronto"

    def set_status(self, status: str, text: str) -> None:
        self.status = status
        self.status_text = text

    # ---- métodos chamados do JS ----
    def state(self) -> dict:
        return {
            "local_url": self.local_url or "",
            "public_url": self.public_url or "",
            "status": self.status,
            "status_text": self.status_text,
            "home_path": self.home_path,
            "cloud_sync": self.cloud_sync,
        }

    def open_browser(self) -> None:
        url = self.public_url or self.local_url
        if url:
            webbrowser.open(url)

    def copy_public(self) -> None:
        if self.public_url and self._window:
            try:
                # pywebview clipboard helper varia entre versões; fallback ctypes.
                import ctypes
                ctypes.windll.user32.OpenClipboard(0)
                ctypes.windll.user32.EmptyClipboard()
                CF_UNICODETEXT = 13
                GMEM_MOVEABLE = 0x0002
                data = self.public_url.encode("utf-16-le") + b"\x00\x00"
                handle = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                pcontents = ctypes.windll.kernel32.GlobalLock(handle)
                ctypes.cdll.msvcrt.memcpy(pcontents, data, len(data))
                ctypes.windll.kernel32.GlobalUnlock(handle)
                ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, handle)
                ctypes.windll.user32.CloseClipboard()
            except Exception:
                pass

    def shutdown(self) -> None:
        if self._shutdown_cb:
            threading.Thread(target=self._shutdown_cb, daemon=True).start()
        if self._window:
            self._window.destroy()


def run_ui(api: JsApi, on_close: Callable[[], None]) -> None:
    """Bloqueia até a janela ser fechada."""
    window = webview.create_window(
        title="roll3d6 RPG",
        html=INDEX_HTML,
        width=480,
        height=380,
        resizable=False,
        js_api=api,
    )
    api.attach_window(window)

    def _on_closed():
        try:
            on_close()
        except Exception:
            pass

    window.events.closed += _on_closed
    webview.start()
