"""Smoke test (descartável) — valida config + porta + download do cloudflared."""
from __future__ import annotations

import time

from desktop import runtime_config, server, tunnel


def main() -> None:
    home = runtime_config.bootstrap_env()
    print(f"home: {home}")
    print(f"secret.key existe: {(home / 'secret.key').exists()}")
    print(f"media/ existe: {(home / 'media').exists()}")
    print(f"bin/ existe: {(home / 'bin').exists()}")

    port = server.find_free_port(8000)
    print(f"porta livre encontrada: {port}")

    last_pct = -1

    def progress(downloaded: int, total: int) -> None:
        nonlocal last_pct
        if not total:
            return
        pct = int(downloaded / total * 100)
        if pct != last_pct and pct % 10 == 0:
            print(f"cloudflared {downloaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB ({pct}%)")
            last_pct = pct

    print("\nbaixando cloudflared (uma vez só, fica em cache)...")
    t0 = time.time()
    exe = tunnel.ensure_cloudflared(home, progress=progress)
    print(f"\ncloudflared OK em {time.time() - t0:.1f}s")
    print(f"  path: {exe}")
    print(f"  tamanho: {exe.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
