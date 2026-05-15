"""Teste E2E headless (sem UI). Valida daphne + cloudflared + captura de URL."""
from __future__ import annotations

import sys
import time

from desktop import runtime_config, server, tunnel


def main() -> int:
    home = runtime_config.bootstrap_env()
    project_root = runtime_config.project_root()

    import django  # noqa: WPS433
    django.setup()

    from django.core.management import call_command  # noqa: WPS433
    print("[1/5] migrate...")
    call_command("migrate", "--noinput", verbosity=0)

    from django.contrib.auth import get_user_model  # noqa: WPS433
    User = get_user_model()
    if not User.objects.exists():
        print("[2/5] criando admin default...")
        User.objects.create_superuser(
            username="admin", email="admin@local.test", password="admin"
        )
    else:
        print(f"[2/5] usuários já existem ({User.objects.count()}), skip superuser")

    port = server.find_free_port(8000)
    print(f"[3/5] subindo daphne na porta {port}...")

    ds = server.DjangoServer(project_root, home, port)
    ds.start()

    if not server.wait_ready(port, timeout=30):
        print(f"FAIL: daphne não respondeu em 30s. Log em {home}/logs/daphne.log")
        ds.stop()
        return 1
    print(f"      daphne OK em http://127.0.0.1:{port}/")

    print("[4/5] garantindo cloudflared...")
    tunnel.ensure_cloudflared(home)

    print("[5/5] subindo túnel...")
    t = tunnel.Tunnel(home, port)
    captured = {"url": None}

    def on_url(u: str) -> None:
        captured["url"] = u

    t.start(on_url=on_url)

    deadline = time.time() + 45
    while time.time() < deadline and not captured["url"]:
        time.sleep(0.5)

    if captured["url"]:
        print()
        print("=" * 60)
        print("SUCESSO — pipeline E2E funcionando")
        print(f"  local : http://127.0.0.1:{port}/")
        print(f"  publica: {captured['url']}")
        print("=" * 60)
        # Mantém vivo 10s pra confirmar estabilidade.
        print("\nmantendo vivo 10s pra você poder testar a URL pública...")
        time.sleep(10)
        rc = 0
    else:
        print(f"FAIL: URL pública não apareceu em 45s. Veja {home}/logs/cloudflared.log")
        rc = 1

    print("\nencerrando...")
    t.stop()
    ds.stop()
    return rc


if __name__ == "__main__":
    sys.exit(main())
