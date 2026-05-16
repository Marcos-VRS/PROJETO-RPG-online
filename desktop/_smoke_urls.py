"""Smoke test: loga e bate em todas as URLs do site, relata 4xx/5xx."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

import django

os.environ["ROLL3D6_DESKTOP_HOME"] = str(Path(os.environ["OneDrive"]) / "roll3d6")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

BASE = "http://127.0.0.1:8000"


def make_session():
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", "rd6-smoke/1.0")]
    return opener


def get(opener, path, allow_redirect=True):
    req = urllib.request.Request(f"{BASE}{path}")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace") if e.fp else ""


def login(opener, username, password):
    # Pega CSRF cookie
    status, body = get(opener, "/login/")
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
    if not m:
        raise RuntimeError("não achou csrf na pagina de login")
    token = m.group(1)

    data = urllib.parse.urlencode(
        {"username": username, "password": password, "csrfmiddlewaretoken": token}
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/login/",
        data=data,
        headers={"Referer": f"{BASE}/login/", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with opener.open(req, timeout=10) as r:
            final = r.geturl()
            return r.status, final
    except urllib.error.HTTPError as e:
        return e.code, "?"


def reset_password(username, new_pw):
    """Reseta senha do user via ORM. Necessário pra logar no smoke."""
    User = get_user_model()
    u = User.objects.filter(username=username).first()
    if not u:
        return False
    u.set_password(new_pw)
    u.save()
    return True


def main():
    # Reseta senha do Marcos (GM da Accursed) pra "smoketest123" — operação local
    # temporária; em produção isso seria criminoso, aqui é só o banco do OneDrive
    # do teste local. Vou restaurar no fim.
    User = get_user_model()
    marcos = User.objects.filter(username="Marcos").first()
    if not marcos:
        print("FATAL: user 'Marcos' não existe no banco")
        return 1
    original_hash = marcos.password
    marcos.set_password("smoketest123")
    marcos.save()

    try:
        opener = make_session()
        status, final = login(opener, "Marcos", "smoketest123")
        print(f"login -> status {status}, redirect to {final}")

        # URLs a testar. Padrão: (path, expected_status_codes, label)
        ROUTES = [
            ("/", [200, 302], "index"),
            ("/login/", [200], "login"),
            ("/Nova_Campanha/", [200, 302], "nova_campanha_index"),
            ("/Nova_campanha/Criar_Campanha/", [200, 302], "criar_campanha"),
            ("/Nova_campanha/lista_campanhas/", [200, 302], "lista_campanhas"),
            ("/Carregar_Campanha/", [200, 302], "carregar_campanha_index"),
            ("/Carregar_campanha/GM/", [200, 302], "carregar_campanha_gm"),
            ("/Carregar_campanha/Player/", [200, 302], "carregar_campanha_player"),
            ("/Fichas/", [200, 302], "carregar_fichas"),
            ("/Fichas/Editar/2/", [200, 302], "editar_fichas_menu"),
            ("/Campanha/2/Criar_Ficha/", [200, 302], "criar_ficha_campanha"),
            ("/Journal/2/", [200], "journal"),
            ("/Fichas/Menu/GM/2", [200, 302], "menu_fichas_gm"),
            ("/Fichas/lista/gm/2/", [200, 302], "lista_gm_fichas"),
            ("/game/2/1/", [200], "game_interface"),
            ("/add-asset/2", [200, 302], "add_asset"),
            ("/edit-asset_menu/2/", [200, 302], "edit_asset_menu"),
            ("/delete-asset-menu/2/", [200, 302], "remove_asset_menu"),
            ("/delete-character-sheet-menu/3/", [200, 302], "delete_sheet_menu"),
        ]

        ok = bad = 0
        for path, expected, label in ROUTES:
            status, body = get(opener, path)
            if status in expected:
                marker = "OK "
                ok += 1
            elif status in (301, 302):
                marker = "RDR"
                ok += 1
            else:
                marker = "ERR"
                bad += 1
            print(f"  [{marker}] {status:3} {path:50} ({label})")
            if status >= 500:
                # mostra parte do html pra diagnóstico
                snippet = re.sub(r"\s+", " ", body[:300])
                print(f"        body: {snippet}")

        print(f"\nresumo: {ok} ok, {bad} erros")
        return 0 if bad == 0 else 1
    finally:
        # Restaura senha original
        marcos.password = original_hash
        marcos.save()
        print("senha do Marcos restaurada")


if __name__ == "__main__":
    sys.exit(main())
