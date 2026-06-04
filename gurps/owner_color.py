"""Cor identitária do dono de uma ficha/token.

Regra do projeto (decidida 2026-05-24):
- GM (dono da campanha) → vermelho fixo (#dc2626).
- Players → cor HSL derivada de hash do username, evitando a zona vermelha
  (reservada ao GM) pra não confundir.

Usado em:
- _build_player_mini (borda da mini na players-bar)
- consumers._add_token (borda do token no mapa)
"""

GM_COLOR = "#dc2626"


def _username_hue(username: str) -> int:
    """Hash estável do username → hue 0-359, empurrado pra fora da zona
    vermelha (0-30 e 340-360) que é reservada ao GM."""
    h = 0
    for ch in username or "":
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    hue = h % 360
    if hue < 40 or hue > 330:
        hue = (hue + 80) % 360
    return hue


def owner_color_for(owner_user, campanha) -> str:
    """Retorna a cor do dono. owner_user pode ser None (NPC sem dono) →
    cor neutra dourada. Se owner_user é o dono da campanha → vermelho GM."""
    if owner_user is None:
        return "#c9a55c"  # dourado neutro (NPC)
    if campanha is not None and campanha.dono_id == owner_user.id:
        return GM_COLOR
    return f"hsl({_username_hue(owner_user.username)}, 70%, 55%)"


def owner_color_for_character(character, campanha):
    """Resolve o owner_user de uma ficha (V2 owner FK; V1 info_campanha.player_name)
    e retorna a cor. Tolerante a ambos os schemas."""
    from gurps.models import CharacterSheetV2, RegisterUser

    owner_user = None
    if isinstance(character, CharacterSheetV2):
        owner_user = character.owner
    else:
        info = getattr(character, "info_campanha", None) or {}
        player_name = info.get("player_name")
        if player_name:
            owner_user = RegisterUser.objects.filter(username=player_name).first()
    return owner_color_for(owner_user, campanha)
