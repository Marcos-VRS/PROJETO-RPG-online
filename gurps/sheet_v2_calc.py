"""Cálculos auxiliares para CharacterSheetV2 baseados no catálogo GURPS 4e.

Tudo aqui é deterministico — dados em entrada = mesmas saídas. Sem efeitos
colaterais. Usado tanto no model.save() (recompute_points) quanto nas views
(compute_secondary) e no front via API simples.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent / "data"


# =============================================================================
# Catálogo (lazy load)
# =============================================================================

@lru_cache(maxsize=None)
def _load_catalog(name: str) -> dict:
    """Carrega um JSON de gurps/data/ uma única vez."""
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def get_advantage(adv_id: str) -> dict | None:
    for e in _load_catalog("advantages")["entries"]:
        if e["id"] == adv_id:
            return e
    return None


def get_disadvantage(disad_id: str) -> dict | None:
    for e in _load_catalog("disadvantages")["entries"]:
        if e["id"] == disad_id:
            return e
    return None


def get_skill(skill_id: str) -> dict | None:
    for e in _load_catalog("skills")["entries"]:
        if e["id"] == skill_id:
            return e
    return None


# =============================================================================
# Custos de atributos
# =============================================================================

# Pontos por +1 sobre o padrão (10)
ATTRIBUTE_COST_PER_POINT = {"st": 10, "dx": 20, "iq": 20, "ht": 10}


def cost_primary_attributes(primary: dict) -> int:
    """Custo total dos 4 atributos primários (ST/DX/IQ/HT). Base 10 = 0 pts."""
    total = 0
    for attr in ("st", "dx", "iq", "ht"):
        value = primary.get(attr, 10)
        total += (value - 10) * ATTRIBUTE_COST_PER_POINT[attr]
    return total


# =============================================================================
# Características secundárias (derivadas dos primários)
# =============================================================================

# Custo por ±1 nas secundárias compráveis individualmente
SECONDARY_COST_PER_POINT = {
    "hp": 2,            # HP: +2 pts por ponto acima/abaixo de ST
    "will": 5,          # Will: +5 pts por ponto acima/abaixo de IQ
    "per": 5,           # Per: +5 pts por ponto acima/abaixo de IQ
    "fp": 3,            # FP: +3 pts por ponto acima/abaixo de HT
    "basic_speed": 20,  # Basic Speed: +5 pts por +0.25 (=20/ponto inteiro)
    "basic_move": 5,    # Basic Move: +5 pts por +1 yd/s
}


def compute_secondary(primary: dict, modifiers: dict | None = None) -> dict:
    """Calcula HP, FP, Will, Per, Basic Speed, Basic Move, Dodge, Basic Lift.

    primary: {"st": 10, "dx": 10, "iq": 10, "ht": 10}
    modifiers: {"hp": +N, "fp": +N, "will": +N, "per": +N, "basic_speed": +0.25, "basic_move": +N}

    Returns: dict completo com todas as secundárias.
    """
    modifiers = modifiers or {}
    st = primary.get("st", 10)
    dx = primary.get("dx", 10)
    iq = primary.get("iq", 10)
    ht = primary.get("ht", 10)

    hp = st + modifiers.get("hp", 0)
    will = iq + modifiers.get("will", 0)
    per = iq + modifiers.get("per", 0)
    fp = ht + modifiers.get("fp", 0)
    basic_speed = (ht + dx) / 4 + modifiers.get("basic_speed", 0)
    basic_move = int(basic_speed) + modifiers.get("basic_move", 0)
    dodge = int(basic_speed) + 3  # Dodge não comprável separado
    basic_lift = (st * st) / 5  # em lbs

    thrust, swing = compute_thrust_swing(st)

    return {
        "hp": hp,
        "fp": fp,
        "will": will,
        "per": per,
        "basic_speed": round(basic_speed, 2),
        "basic_move": basic_move,
        "dodge": dodge,
        "basic_lift": round(basic_lift, 1),
        "thrust": thrust,
        "swing": swing,
    }


def compute_thrust_swing(st: int) -> tuple[str, str]:
    """Damage Table (Characters p16). Retorna (thrust, swing) como strings dados."""
    # Tabela parcial — cobre ST 1-30. Acima disso +1d em ambos cada +10 ST acima de 100.
    DAMAGE_TABLE = {
        # ST: (thrust, swing)
        1: ("1d-6", "1d-5"), 2: ("1d-6", "1d-5"), 3: ("1d-5", "1d-4"),
        4: ("1d-5", "1d-4"), 5: ("1d-4", "1d-3"), 6: ("1d-4", "1d-3"),
        7: ("1d-3", "1d-2"), 8: ("1d-3", "1d-2"), 9: ("1d-2", "1d-1"),
        10: ("1d-2", "1d"), 11: ("1d-1", "1d+1"), 12: ("1d-1", "1d+2"),
        13: ("1d", "2d-1"), 14: ("1d", "2d"), 15: ("1d+1", "2d+1"),
        16: ("1d+1", "2d+2"), 17: ("1d+2", "3d-1"), 18: ("1d+2", "3d"),
        19: ("2d-1", "3d+1"), 20: ("2d-1", "3d+2"), 21: ("2d", "4d-1"),
        22: ("2d", "4d"), 23: ("2d+1", "4d+1"), 24: ("2d+1", "4d+2"),
        25: ("2d+2", "5d-1"), 26: ("2d+2", "5d"), 27: ("3d-1", "5d+1"),
        28: ("3d-1", "5d+1"), 29: ("3d", "5d+2"), 30: ("3d", "5d+2"),
    }
    if st <= 0:
        return ("0", "0")
    if st in DAMAGE_TABLE:
        return DAMAGE_TABLE[st]
    if st <= 100:
        # Aproximação linear pra valores não tabelados
        return DAMAGE_TABLE.get(min(st, 30), ("3d", "5d+2"))
    # Acima de 100: +1d cada +10 ST
    base_thrust, base_swing = DAMAGE_TABLE[30]
    extra_d = (st - 100) // 10
    return (f"{base_thrust}+{extra_d}d", f"{base_swing}+{extra_d}d")


def cost_secondary_attributes(modifiers: dict) -> int:
    """Pontos gastos comprando bônus em secundárias."""
    total = 0
    for key, value in modifiers.items():
        if key == "basic_speed":
            # +5 pts por +0.25
            total += int(round(value / 0.25)) * 5
        elif key in SECONDARY_COST_PER_POINT:
            total += int(value * SECONDARY_COST_PER_POINT[key])
    return total


# =============================================================================
# Custos de vantagens / desvantagens / skills
# =============================================================================

def cost_advantage_entry(entry: dict) -> int:
    """Calcula custo de uma vantagem do sheet.

    entry pode ser:
      {"id": "combat_reflexes", "level": 1, ...}                  # catalog (fixed)
      {"id": "talent_animal_friend", "level": 3, ...}             # catalog (per_level)
      {"id": "claws", "variant_index": 2, "level": 1, ...}        # catalog (options)
      {"id": "manual:Minha Vantagem", "manual_cost": 12, ...}     # entrada manual
      {"manual_cost": N} sem id também é aceito como fallback.
    """
    # Modo manual explicito
    if entry.get("manual_cost") is not None:
        return int(entry["manual_cost"])
    # Backward-compat com "custom_cost"
    if entry.get("custom_cost") is not None:
        return int(entry["custom_cost"])

    raw_id = entry.get("id", "") or ""
    if raw_id.startswith("manual:"):
        return 0  # manual sem custo declarado

    adv = get_advantage(raw_id)
    if not adv:
        return 0

    cost_obj = adv.get("cost", {})
    cost_type = cost_obj.get("type")
    level = entry.get("level", 1) or 1

    if cost_type == "fixed":
        base = int(cost_obj.get("value", 0))
    elif cost_type == "per_level":
        base = int(cost_obj.get("value", 0)) * level
    elif cost_type == "options":
        idx = entry.get("variant_index", 0) or 0
        choices = cost_obj.get("choices", [])
        try:
            base = int(choices[idx].get("value", 0))
        except (IndexError, KeyError):
            base = 0
    else:
        # variable/tiered/desconhecido — usa manual_cost se houver, senão 0
        base = 0

    # Modificadores percentuais (Enhancements + Limitations)
    total_pct = sum(_modifier_effective_percent(m) for m in entry.get("modifiers", []) or [])
    total_pct = max(total_pct, -80)
    adjusted = base * (1 + total_pct / 100.0)
    return math.ceil(adjusted)


# =============================================================================
# Pickers: catálogos achatados pra dropdowns
# =============================================================================

def _safe_int(v, default=0) -> int:
    """int() tolerante: strings tipo '5/10/15' viram default (catalogador placeholder)."""
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _english_variant_label(choice: dict, idx: int) -> str:
    """Extrai melhor nome em inglês de um choice de catálogo.

    Catalog choices têm 'name_pt' (e às vezes 'name_en'). Vários começam com
    o nome em inglês literal seguido de '—' e descrição em pt. Truncamos pra
    obter só o nome quando possível.
    """
    name_en = choice.get("name_en")
    if name_en:
        return name_en
    raw = choice.get("name_pt", f"option {idx + 1}")
    for sep in (" — ", " – ", " - ", "—"):
        if sep in raw:
            return raw.split(sep, 1)[0].strip()
    return raw


def flatten_advantages_for_picker() -> list:
    """Retorna lista flat de 'opções de vantagem' pro dropdown.

    Cada entrada já tem o suficiente pra UI calcular custos:
      {
        "key": "claws#2",            # único, usado como value do select
        "id": "claws",               # id da vantagem no catálogo
        "label": "Claws (Sharp Claws — short)",
        "cost_type": "fixed" | "per_level" | "options" | "variable" | "tiered",
        "value": 5,                  # custo base (por nível se per_level, ou da variante se options)
        "variant_index": 2,          # se aplicável
        "page_ref": 42,
        "supports_levels": false,    # true só pra per_level
      }
    """
    data = _load_catalog("advantages")
    result = []
    for entry in data.get("entries", []):
        adv_id = entry["id"]
        # Prioriza inglês — facilita casar com o livro
        name = entry.get("name_en") or entry.get("name_pt") or adv_id
        page = entry.get("page_ref")
        cost = entry.get("cost", {})
        ctype = cost.get("type")

        if ctype == "fixed":
            result.append({
                "key": adv_id,
                "id": adv_id,
                "label": name,
                "cost_type": "fixed",
                "value": _safe_int(cost.get("value")),
                "page_ref": page,
                "supports_levels": False,
            })
        elif ctype == "per_level":
            result.append({
                "key": adv_id,
                "id": adv_id,
                "label": name,
                "cost_type": "per_level",
                "value": _safe_int(cost.get("value")),
                "page_ref": page,
                "supports_levels": True,
            })
        elif ctype == "options":
            for idx, choice in enumerate(cost.get("choices", [])):
                sub = _english_variant_label(choice, idx)
                if len(sub) > 60:
                    sub = sub[:57] + "..."
                result.append({
                    "key": f"{adv_id}#{idx}",
                    "id": adv_id,
                    "label": f"{name} ({sub})",
                    "cost_type": "fixed",
                    "value": _safe_int(choice.get("value")),
                    "variant_index": idx,
                    "page_ref": page,
                    "supports_levels": False,
                })
        elif ctype in ("variable", "tiered"):
            result.append({
                "key": adv_id,
                "id": adv_id,
                "label": f"{name} (variable cost)",
                "cost_type": "variable",
                "value": 0,
                "page_ref": page,
                "supports_levels": False,
            })
        else:
            # Tipo desconhecido — adiciona mesmo assim com custo 0
            result.append({
                "key": adv_id,
                "id": adv_id,
                "label": name,
                "cost_type": "unknown",
                "value": 0,
                "page_ref": page,
                "supports_levels": False,
            })

    # Ordena por label pra usuário achar fácil
    result.sort(key=lambda x: x["label"].lower())
    return result


def _parse_modifier_cost(cost_str: str) -> dict:
    """Parseia string de custo de modifier do catálogo.

    Retorna: {"kind": "fixed"|"per_level"|"options"|"variable",
              "value": int (default/base),
              "options": [int, ...] (se options)}

    Exemplos:
      "+50%"             → {kind: fixed, value: 50}
      "-40%"             → {kind: fixed, value: -40}
      "+5%/nível"        → {kind: per_level, value: 5}
      "-10% / -20% / -40%" → {kind: options, value: -10, options: [-10, -20, -40]}
      "+50% a +200%"     → {kind: variable, value: 50}
      "variável"         → {kind: variable, value: 0}
    """
    import re
    s = (cost_str or "").strip().lower()
    if not s or s in ("variável", "variavel", "variable"):
        return {"kind": "variable", "value": 0}

    # per_level: contém "/nível", "/level", "por nível"
    if "/nível" in s or "/nivel" in s or "/level" in s or "por nível" in s or "por nivel" in s:
        m = re.search(r"([+-]?\d+)", s)
        if m:
            return {"kind": "per_level", "value": int(m.group(1))}
        return {"kind": "variable", "value": 0}

    # range "X a Y": variável
    if " a " in s or " to " in s:
        m = re.search(r"([+-]?\d+)", s)
        if m:
            return {"kind": "variable", "value": int(m.group(1))}
        return {"kind": "variable", "value": 0}

    # múltiplos separados por "/": options
    if "/" in s:
        numbers = re.findall(r"[+-]?\d+", s)
        if len(numbers) >= 2:
            opts = [int(n) for n in numbers]
            return {"kind": "options", "value": opts[0], "options": opts}

    # fixed simples
    m = re.search(r"([+-]?\d+)", s)
    if m:
        return {"kind": "fixed", "value": int(m.group(1))}

    return {"kind": "variable", "value": 0}


def flatten_modifiers_for_picker() -> list:
    """Flatten enhancements + limitations num único array pro dropdown.

    Limitations entram com percent negativo, enhancements positivo. Variantes
    com sinais múltiplos (ex: '+50% a +200%') ficam como uma entrada 'variable'.

    Retorna lista com:
      {key, id, label, page_ref, percent (default), supports_levels (bool),
       kind ('fixed'|'per_level'|'variable'|'options'),
       options: [N, ...] se kind=options}
    """
    data = _load_catalog("modifiers")
    result = []

    for section_key, sign_hint in (("enhancements", 1), ("limitations", -1)):
        for entry in data.get(section_key, []):
            mod_id = entry["id"]
            name = entry.get("name_en") or entry.get("name_pt") or mod_id
            page = entry.get("page_ref")
            cost_raw = entry.get("cost", "")

            parsed = _parse_modifier_cost(cost_raw)
            kind = parsed["kind"]
            base_pct = parsed["value"]

            # Para options, gera UMA entry por choice
            if kind == "options":
                for idx, opt_val in enumerate(parsed["options"]):
                    result.append({
                        "key": f"{section_key[0]}:{mod_id}#{idx}",
                        "id": mod_id,
                        "label": f"{name} ({opt_val:+d}%)",
                        "page_ref": page,
                        "percent": opt_val,
                        "supports_levels": False,
                        "kind": "fixed",
                        "section": section_key,
                    })
            elif kind == "per_level":
                result.append({
                    "key": f"{section_key[0]}:{mod_id}",
                    "id": mod_id,
                    "label": name,
                    "page_ref": page,
                    "percent": base_pct,
                    "supports_levels": True,
                    "kind": "per_level",
                    "section": section_key,
                })
            elif kind == "variable":
                result.append({
                    "key": f"{section_key[0]}:{mod_id}",
                    "id": mod_id,
                    "label": f"{name} (variable)",
                    "page_ref": page,
                    "percent": base_pct,
                    "supports_levels": False,
                    "kind": "variable",
                    "section": section_key,
                })
            else:  # fixed
                result.append({
                    "key": f"{section_key[0]}:{mod_id}",
                    "id": mod_id,
                    "label": name,
                    "page_ref": page,
                    "percent": base_pct,
                    "supports_levels": False,
                    "kind": "fixed",
                    "section": section_key,
                })

    result.sort(key=lambda x: x["label"].lower())
    return result


def flatten_skills_for_picker() -> list:
    """Lista flat de skills pro dropdown.

    Skills têm: name, attribute (DX/IQ/HT/Per/Will/ST), difficulty (E/A/H/VH),
    page_ref. defaults estão em texto livre quando existirem.
    """
    data = _load_catalog("skills")
    result = []
    for entry in data.get("entries", []):
        s_id = entry["id"]
        name = entry.get("name_en") or s_id
        attr = (entry.get("controlling_attribute") or "").upper()
        diff = (entry.get("difficulty") or "").upper()
        result.append({
            "key": s_id,
            "id": s_id,
            "label": name,
            "attribute": attr,
            "difficulty": diff,
            "tl_dependent": entry.get("tl_dependent", False),
            "requires_specialty": entry.get("requires_specialty", False),
            "default": entry.get("default", ""),  # se houver
            "page_ref": entry.get("page_ref"),
        })
    result.sort(key=lambda x: x["label"].lower())
    return result


def flatten_disadvantages_for_picker() -> list:
    """Mesma ideia do flatten de advantages, mas pra desvantagens.

    Variantes (cost.type='options') viram entradas separadas. Custos são
    negativos. Self-controllable é marcado pra UI poder destacar.
    """
    data = _load_catalog("disadvantages")
    result = []
    for entry in data.get("entries", []):
        d_id = entry["id"]
        name = entry.get("name_en") or entry.get("name_pt") or d_id
        page = entry.get("page_ref")
        sc = entry.get("self_control", False)
        cost = entry.get("cost", {})
        ctype = cost.get("type")

        if ctype == "fixed":
            result.append({
                "key": d_id, "id": d_id, "label": name,
                "cost_type": "fixed", "value": _safe_int(cost.get("value")),
                "page_ref": page, "supports_levels": False, "self_control": sc,
            })
        elif ctype == "per_level":
            result.append({
                "key": d_id, "id": d_id, "label": name,
                "cost_type": "per_level", "value": _safe_int(cost.get("value")),
                "page_ref": page, "supports_levels": True, "self_control": sc,
            })
        elif ctype == "options":
            for idx, choice in enumerate(cost.get("choices", [])):
                sub = _english_variant_label(choice, idx)
                if len(sub) > 60:
                    sub = sub[:57] + "..."
                result.append({
                    "key": f"{d_id}#{idx}", "id": d_id,
                    "label": f"{name} ({sub})",
                    "cost_type": "fixed", "value": _safe_int(choice.get("value")),
                    "variant_index": idx, "page_ref": page,
                    "supports_levels": False, "self_control": sc,
                })
        elif ctype in ("variable", "tiered"):
            result.append({
                "key": d_id, "id": d_id, "label": f"{name} (variable cost)",
                "cost_type": "variable", "value": 0,
                "page_ref": page, "supports_levels": False, "self_control": sc,
            })
        else:
            result.append({
                "key": d_id, "id": d_id, "label": name,
                "cost_type": "unknown", "value": 0,
                "page_ref": page, "supports_levels": False, "self_control": sc,
            })

    result.sort(key=lambda x: x["label"].lower())
    return result


def cost_disadvantage_entry(entry: dict) -> int:
    """Custo (negativo) de uma desvantagem.

    Mesmo shape de entry que advantages:
      {"id": "bad_temper", "level":1, ...}                       # fixed/per_level
      {"id": "lame", "variant_index": 1, ...}                    # options
      {"id": "manual:Custom Disad", "manual_cost": -10, ...}     # manual
    Self-control number (3d): 6 = ×2, 9 = ×1.5, 12 = ×1 (default), 15 = ×0.5.
    """
    if entry.get("manual_cost") is not None:
        return int(entry["manual_cost"])
    if entry.get("custom_cost") is not None:
        return int(entry["custom_cost"])

    raw_id = entry.get("id", "") or ""
    if raw_id.startswith("manual:"):
        return 0

    disad = get_disadvantage(raw_id)
    if not disad:
        return 0

    cost_obj = disad.get("cost", {})
    cost_type = cost_obj.get("type")
    level = entry.get("level", 1) or 1

    if cost_type == "fixed":
        base = int(cost_obj.get("value", 0))
    elif cost_type == "per_level":
        base = int(cost_obj.get("value", 0)) * level
    elif cost_type == "options":
        idx = entry.get("variant_index", 0) or 0
        choices = cost_obj.get("choices", [])
        try:
            base = int(choices[idx].get("value", 0))
        except (IndexError, KeyError):
            base = 0
    else:
        base = 0

    sc = entry.get("self_control")
    sc_mult = {6: 2.0, 9: 1.5, 12: 1.0, 15: 0.5}.get(sc, 1.0) if disad.get("self_control") else 1.0

    # Aplica modificadores percentuais (Enhancements/Limitations)
    total_pct = sum(_modifier_effective_percent(m) for m in entry.get("modifiers", []) or [])
    total_pct = max(total_pct, -80)
    adjusted = base * sc_mult * (1 + total_pct / 100.0)

    # Para desvantagem (valor negativo), arredondar pro INTEIRO mais próximo de zero
    # Mas a prática GURPS é arredondar pro pior (mais negativo). Vou usar ceil
    # do absoluto e preservar sinal — equivalente a "menor valor absoluto" se positivo,
    # "menor valor (mais negativo)" se negativo. Pra disad: math.floor(adjusted)
    # devolve mais negativo. Mas vou seguir simples: ceil do valor (mantém compat com adv).
    return math.ceil(adjusted) if adjusted >= 0 else math.floor(adjusted)


def _modifier_effective_percent(mod_entry: dict) -> int:
    """Percentual efetivo de UM modifier (lista anexa à entry de adv/disad).

    mod_entry shape:
      {"id": "...", "percent": -20, "level": 1, "is_manual": false, ...}
    """
    if mod_entry.get("is_manual"):
        return int(mod_entry.get("manual_percent") or mod_entry.get("percent") or 0)
    pct = int(mod_entry.get("percent") or 0)
    if mod_entry.get("supports_levels"):
        lvl = int(mod_entry.get("level") or 1)
        return pct * lvl
    return pct


def _base_cost_from_catalog(cost_obj: dict, level: int) -> int:
    """Resolve um 'cost' do catálogo em pontos (já considera level se aplicável)."""
    kind = cost_obj.get("type")
    if kind == "fixed":
        return int(cost_obj.get("value", 0))
    if kind == "per_level":
        return int(cost_obj.get("value", 0)) * level
    if kind == "options":
        # Se entry escolheu option_index, usa; senão usa primeira
        idx = 0
        try:
            choices = cost_obj.get("choices", [])
            return int(choices[idx]["value"]) if choices else 0
        except (KeyError, IndexError):
            return 0
    if kind == "variable" or kind == "tiered":
        # Sem fórmula resolvida no schema; player declara custom_cost
        return 0
    return 0


def cost_skill_entry(entry: dict, primary: dict) -> int:
    """Custo de um skill conforme pontos investidos.

    GURPS Skill Cost Table (p170 Characters):
    - 1 pt = atributo-controlador-3 (Easy: -1; Average: -2; Hard: -3; VH: -3)
    - 2 pts = atributo (Easy +0; Average -1; Hard -2; VH -3 simplified)
    - 4 pts = atributo +1
    - 8 pts = atributo +2
    - +4 pts por +1 acima disso
    """
    if entry.get("custom_cost") is not None:
        return int(entry["custom_cost"])
    return int(entry.get("points", 0))


def compute_skill_level(entry: dict, primary: dict, secondary: dict | None = None) -> int:
    """Nível efetivo do skill baseado em pontos investidos + atributo controlador."""
    skill = get_skill(entry.get("id", ""))
    if not skill:
        return 0

    attr = skill.get("controlling_attribute", "DX").upper()
    difficulty = skill.get("difficulty", "Average").upper()

    # Mapeia attribute para valor
    attr_value_map = {
        "ST": primary.get("st", 10),
        "DX": primary.get("dx", 10),
        "IQ": primary.get("iq", 10),
        "HT": primary.get("ht", 10),
        "PER": (secondary or {}).get("per", primary.get("iq", 10)),
        "WILL": (secondary or {}).get("will", primary.get("iq", 10)),
    }
    base_attr = attr_value_map.get(attr, 10)

    points = entry.get("points", 0)

    # Easy / Average / Hard / Very Hard
    diff_offset = {"EASY": 0, "AVERAGE": -1, "HARD": -2, "VERY HARD": -3}.get(difficulty, -1)

    if points < 1:
        return 0
    # Thresholds: 1=base, 2=+1, 4=+2, 8=+3, depois +4 pts cada +1.
    # Valores intermediários usam o threshold imediatamente abaixo.
    if points < 2:
        bonus = 0
    elif points < 4:
        bonus = 1
    elif points < 8:
        bonus = 2
    else:
        bonus = 3 + (points - 8) // 4
    return base_attr + diff_offset + bonus


# =============================================================================
# Recompute total
# =============================================================================

def recompute_points(sheet) -> dict:
    """Recalcula pontos gastos no sheet inteiro. Chamado em save()."""
    primary = sheet.primary_attributes or {}
    modifiers = sheet.secondary_modifiers or {}

    attr_cost = cost_primary_attributes(primary)
    sec_cost = cost_secondary_attributes(modifiers)
    adv_cost = sum(cost_advantage_entry(e) for e in (sheet.advantages or []))
    disad_cost = sum(cost_disadvantage_entry(e) for e in (sheet.disadvantages or []))
    skill_cost = sum(cost_skill_entry(e, primary) for e in (sheet.skills or []))

    spent = attr_cost + sec_cost + adv_cost + disad_cost + skill_cost
    available = (sheet.points or {}).get("available", 150)

    return {
        "available": available,
        "spent": spent,
        "remaining": available - spent,
        "breakdown": {
            "attributes": attr_cost,
            "secondary": sec_cost,
            "advantages": adv_cost,
            "disadvantages": disad_cost,
            "skills": skill_cost,
        },
    }
