"""Cor identitária do dono de uma ficha/token.

Regra do projeto (2026-05-24, refinada 2026-05-31):
- GM (dono da campanha) → vermelho fixo (#dc2626).
- Cada player → cor única e distinta. Personagens do MESMO player
  compartilham a cor; players diferentes nunca repetem.
- NPCs sem dono → tratados como controlados pelo GM (vermelho).

A distinção entre players usa **golden angle** (137.5°) sobre um índice
estável (ordenado por user id), garantindo cores bem espalhadas no círculo
de matiz e sem colisão visual até dezenas de players.

Usado em:
- _build_player_mini (borda do avatar na players-bar)
- consumers._add_token (borda do token no mapa)
"""

GM_COLOR = "#dc2626"
GOLDEN_ANGLE = 137.508


def _resolve_owner_user(character):
    """Resolve o RegisterUser dono da ficha. V2 = owner FK; V1 = info_campanha
    player_name. Retorna None se não há dono (NPC)."""
    from gurps.models import CharacterSheetV2, RegisterUser

    if isinstance(character, CharacterSheetV2):
        return character.owner
    info = getattr(character, "info_campanha", None) or {}
    player_name = info.get("player_name")
    if player_name:
        return RegisterUser.objects.filter(username=player_name).first()
    return None


def build_player_color_map(characters, campanha):
    """Computa um dict {user_id: cor} pros donos dos personagens da lista.

    - GM (campanha.dono_id) → vermelho.
    - Demais players → golden angle por índice estável (ordenado por user id).

    Personagens sem dono não entram (usam GM_COLOR no fallback).
    """
    owner_ids = set()
    for c in characters:
        ou = _resolve_owner_user(c)
        if ou is not None:
            owner_ids.add(ou.id)

    gm_id = campanha.dono_id if campanha else None
    # Players não-GM, ordenados pra estabilidade
    players = sorted(oid for oid in owner_ids if oid != gm_id)

    color_map = {}
    if gm_id is not None:
        color_map[gm_id] = GM_COLOR
    for i, oid in enumerate(players):
        hue = (40 + i * GOLDEN_ANGLE) % 360  # começa em 40 (longe do vermelho)
        # Se cair perto do vermelho (0-25 ou 335-360), empurra
        if hue < 25 or hue > 335:
            hue = (hue + 60) % 360
        color_map[oid] = f"hsl({hue:.0f}, 72%, 55%)"
    return color_map


def color_for_character(character, campanha, color_map=None):
    """Cor de UM personagem. Usa color_map se fornecido (caminho rápido na
    players-bar); senão computa só pra esse char (caminho do token).

    NPC sem dono → GM_COLOR (controlado pelo mestre)."""
    ou = _resolve_owner_user(character)
    if ou is None:
        return GM_COLOR  # NPC = controlado pelo GM
    if color_map is not None and ou.id in color_map:
        return color_map[ou.id]
    # Fallback: computa pra um único char (token)
    if campanha is not None and campanha.dono_id == ou.id:
        return GM_COLOR
    h = 0
    for ch in ou.username:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    hue = (40 + (h % 360)) % 360
    if hue < 25 or hue > 335:
        hue = (hue + 60) % 360
    return f"hsl({hue}, 72%, 55%)"


# Compat: nome antigo usado em outros módulos
def owner_color_for_character(character, campanha):
    return color_for_character(character, campanha, color_map=None)
