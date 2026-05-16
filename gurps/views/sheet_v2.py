"""Views da CharacterSheetV2 (ficha nova)."""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from gurps.models import Campanha, CharacterSheet, CharacterSheetV2
from gurps.sheet_v2_calc import (
    compute_secondary,
    cost_primary_attributes,
    cost_secondary_attributes,
    flatten_advantages_for_picker,
    flatten_disadvantages_for_picker,
    flatten_modifiers_for_picker,
    flatten_skills_for_picker,
    recompute_points,
)


# =============================================================================
# Broadcast helpers
# =============================================================================

def _broadcast_character_updated(sheet):
    """Notifica clientes WS da campanha que esta ficha foi atualizada.
    Envia mini data (HP/FP/nome/avatar) — front decide se faz partial refresh
    das janelas modais conforme contexto.
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from gurps.views.interface_jogo import _wrap_v2_as_legacy, _build_player_mini

        _wrap_v2_as_legacy(sheet)
        char_data = _build_player_mini(sheet, present_ids=None, show_numbers=True)
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            f"chat_{sheet.campanha_id}",
            {"type": "character_updated", "char": char_data},
        )
    except Exception:
        # WS é melhor-esforço: nunca quebra o save da ficha
        import traceback
        traceback.print_exc()


# =============================================================================
# Permissões
# =============================================================================

def _is_gm(user, campanha: Campanha) -> bool:
    return campanha.dono_id == user.id


def _can_view(user, sheet: CharacterSheetV2) -> bool:
    return _is_gm(user, sheet.campanha) or sheet.owner_id == user.id


def _can_edit(user, sheet: CharacterSheetV2) -> bool:
    return _can_view(user, sheet)


# =============================================================================
# Criar
# =============================================================================

@login_required
def criar_v2(request, campanha_id: int):
    """GET: form vazio para nova ficha V2.
    POST: cria e redireciona pra editar."""
    campanha = get_object_or_404(Campanha, pk=campanha_id)

    if request.method == "POST":
        nome = (request.POST.get("nome_personagem") or "").strip()
        if not nome:
            return render(request, "global/sheet_v2/criar_ficha_v2.html", {
                "campanha": campanha,
                "error": "Nome do personagem é obrigatório.",
            })
        # Cria com defaults
        sheet = CharacterSheetV2.objects.create(
            campanha=campanha,
            owner=request.user,
            nome_personagem=nome,
            primary_attributes={"st": 10, "dx": 10, "iq": 10, "ht": 10},
            secondary_modifiers={},
            advantages=[],
            disadvantages=[],
            skills=[],
            points={"available": campanha.pontos_de_ficha or 150, "spent": 0,
                    "remaining": campanha.pontos_de_ficha or 150,
                    "breakdown": {"attributes": 0, "secondary": 0,
                                  "advantages": 0, "disadvantages": 0, "skills": 0}},
        )
        return redirect("gurps:editar_v2", id=sheet.id)

    return render(request, "global/sheet_v2/criar_ficha_v2.html", {
        "campanha": campanha,
    })


# =============================================================================
# Editar
# =============================================================================

@login_required
def editar_v2(request, id: int):
    """GET: form preenchido (single-page com seções).
    POST: salva alterações."""
    sheet = get_object_or_404(CharacterSheetV2, pk=id)
    if not _can_edit(request.user, sheet):
        return HttpResponseForbidden("Sem permissão para editar esta ficha.")

    save_error = None
    save_field_errors = []  # lista de strings descritivas

    if request.method == "POST":
        # Captura erros de parsing em listas pra reportar ao user em vez de silenciar
        bad_json_fields = []

        sheet.nome_personagem = (request.POST.get("nome_personagem") or sheet.nome_personagem).strip()
        if not sheet.nome_personagem:
            save_field_errors.append("Nome do personagem é obrigatório.")
        sheet.aparencia = request.POST.get("aparencia", "")
        sheet.idade = request.POST.get("idade", "")
        sheet.background = request.POST.get("background", "")
        sheet.money = request.POST.get("money", "")

        primary = {}
        for attr in ("st", "dx", "iq", "ht"):
            val = request.POST.get(f"attr_{attr}", "10")
            try:
                primary[attr] = int(val)
            except (TypeError, ValueError):
                primary[attr] = 10
                save_field_errors.append(f"Atributo {attr.upper()} inválido (usando 10).")
        sheet.primary_attributes = primary

        sec_mods = {}
        for key in ("hp", "fp", "will", "per", "basic_move"):
            raw = request.POST.get(f"secmod_{key}", "0")
            try:
                if raw and int(raw) != 0:
                    sec_mods[key] = int(raw)
            except (TypeError, ValueError):
                pass
        raw_speed = request.POST.get("secmod_basic_speed", "0")
        try:
            if raw_speed and float(raw_speed) != 0:
                sec_mods["basic_speed"] = float(raw_speed)
        except (TypeError, ValueError):
            pass
        sheet.secondary_modifiers = sec_mods

        for field in ("advantages", "disadvantages", "skills",
                      "equipment_melee", "equipment_ranged", "equipment_armor",
                      "equipment_misc",
                      "maneuvers_melee", "maneuvers_ranged", "maneuvers_defense"):
            raw = request.POST.get(field, "")
            if raw:
                try:
                    setattr(sheet, field, json.loads(raw))
                except json.JSONDecodeError:
                    bad_json_fields.append(field)

        if bad_json_fields:
            save_field_errors.append(
                "JSON inválido nestas seções (mantive a versão anterior): "
                + ", ".join(bad_json_fields)
            )

        if _is_gm(request.user, sheet.campanha):
            try:
                available = int(request.POST.get("points_available", 150))
                points = sheet.points or {}
                points["available"] = available
                sheet.points = points
            except (TypeError, ValueError):
                save_field_errors.append("Valor inválido em 'Pontos disponíveis'.")

        if "photo" in request.FILES:
            sheet.photo = request.FILES["photo"]

        # Tenta salvar; captura erros DB (nome duplicado, etc.)
        if not save_field_errors:
            try:
                sheet.save()
                # Broadcast WS pra que abas abertas da tela de jogo atualizem
                # mini/janelas sem refresh manual.
                _broadcast_character_updated(sheet)
                # Após salvar com sucesso, vai direto pra tela de jogo da campanha.
                # Slot 1 = pagina_inicial default da campanha.
                return redirect("gurps:game_interface", campanha_id=sheet.campanha_id, slot=1)
            except Exception as exc:
                msg = str(exc)
                # Mensagem mais clara para constraint de nome único por campanha
                if "unique" in msg.lower() and "nome_personagem" in msg.lower():
                    save_error = (
                        f"Já existe outra ficha chamada '{sheet.nome_personagem}' "
                        f"nesta campanha. Escolha outro nome."
                    )
                else:
                    save_error = f"Erro ao salvar: {msg}"
        else:
            save_error = "Não foi possível salvar — corrija os erros abaixo e tente de novo."

    # GET: prepara contexto
    primary = sheet.primary_attributes or {}
    sec = compute_secondary(primary, sheet.secondary_modifiers or {})
    points = sheet.points or {}

    response = render(request, "global/sheet_v2/editar_ficha_v2.html", {
        "sheet": sheet,
        "campanha": sheet.campanha,
        "primary": primary,
        "secondary": sec,
        "points": points,
        "is_gm": _is_gm(request.user, sheet.campanha),
        "advantages_json": json.dumps(sheet.advantages or []),
        "disadvantages_json": json.dumps(sheet.disadvantages or []),
        "skills_json": json.dumps(sheet.skills or []),
        "equipment_melee_json": json.dumps(sheet.equipment_melee or []),
        "equipment_ranged_json": json.dumps(sheet.equipment_ranged or []),
        "equipment_armor_json": json.dumps(sheet.equipment_armor or []),
        "equipment_misc_json": json.dumps(sheet.equipment_misc or []),
        "maneuvers_melee_json": json.dumps(sheet.maneuvers_melee or []),
        "maneuvers_ranged_json": json.dumps(sheet.maneuvers_ranged or []),
        "maneuvers_defense_json": json.dumps(sheet.maneuvers_defense or []),
        "save_error": save_error,
        "save_field_errors": save_field_errors,
        "save_success": request.GET.get("saved") == "1",
    })
    # Anti-cache agressivo — ficha muda constantemente, qualquer cache atrapalha
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


# =============================================================================
# Ver (read-only)
# =============================================================================

@login_required
def ver_v2(request, id: int):
    """GET read-only. GM ou owner."""
    sheet = get_object_or_404(CharacterSheetV2, pk=id)
    if not _can_view(request.user, sheet):
        return HttpResponseForbidden("Sem permissão para ver esta ficha.")

    primary = sheet.primary_attributes or {}
    sec = compute_secondary(primary, sheet.secondary_modifiers or {})

    return render(request, "global/sheet_v2/ver_ficha_v2.html", {
        "sheet": sheet,
        "campanha": sheet.campanha,
        "primary": primary,
        "secondary": sec,
        "points": sheet.points or {},
        "is_gm": _is_gm(request.user, sheet.campanha),
    })


# =============================================================================
# Listas
# =============================================================================

@login_required
def lista_v2_gm(request, campanha_id: int):
    """GM vê todas as fichas V2 da campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id)
    if not _is_gm(request.user, campanha):
        return HttpResponseForbidden("Apenas o GM da campanha pode acessar.")

    sheets = CharacterSheetV2.objects.filter(campanha=campanha).order_by("nome_personagem")
    return render(request, "global/sheet_v2/lista_v2_gm.html", {
        "campanha": campanha,
        "sheets": sheets,
    })


@login_required
def lista_v2_player(request, campanha_id: int):
    """Player vê suas próprias fichas V2 da campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id)
    sheets = CharacterSheetV2.objects.filter(
        campanha=campanha, owner=request.user
    ).order_by("nome_personagem")
    return render(request, "global/sheet_v2/lista_v2_player.html", {
        "campanha": campanha,
        "sheets": sheets,
    })


# =============================================================================
# API: compute on-the-fly
# =============================================================================

@login_required
def api_catalog_advantages(request):
    """GET — retorna lista flat de vantagens pro dropdown picker."""
    return JsonResponse({"advantages": flatten_advantages_for_picker()})


@login_required
def api_catalog_disadvantages(request):
    """GET — retorna lista flat de desvantagens pro dropdown picker."""
    return JsonResponse({"disadvantages": flatten_disadvantages_for_picker()})


@login_required
def api_catalog_modifiers(request):
    """GET — retorna lista flat de Enhancements + Limitations pro picker de modifiers."""
    return JsonResponse({"modifiers": flatten_modifiers_for_picker()})


@login_required
def api_catalog_skills(request):
    """GET — retorna lista flat de skills pro picker."""
    return JsonResponse({"skills": flatten_skills_for_picker()})


@login_required
@require_http_methods(["POST"])
def api_compute_secondary(request):
    """POST {primary: {st,dx,iq,ht}, modifiers: {...}} → secondary + cost preview."""
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    primary = body.get("primary") or {}
    modifiers = body.get("modifiers") or {}

    secondary = compute_secondary(primary, modifiers)
    attr_cost = cost_primary_attributes(primary)
    sec_cost = cost_secondary_attributes(modifiers)

    return JsonResponse({
        "secondary": secondary,
        "cost_attributes": attr_cost,
        "cost_secondary": sec_cost,
    })


# =============================================================================
# Delete (GM ou owner)
# =============================================================================

@login_required
@require_http_methods(["POST"])
def delete_v2(request, id: int):
    sheet = get_object_or_404(CharacterSheetV2, pk=id)
    if not _can_edit(request.user, sheet):
        return HttpResponseForbidden("Sem permissão.")
    campanha_id = sheet.campanha_id
    sheet.delete()
    return redirect("gurps:lista_v2_player", campanha_id=campanha_id)


# =============================================================================
# Quick add / remove — usados pelo botão "+" da side nav da tela de jogo.
# Permitem adicionar e remover cards (maneuvers / skill / equipment) sem
# sair pra tela completa de edição.
# =============================================================================

# Whitelist de campos JSONField que aceitam quickadd/quickremove.
# Mapa: kind URL → atributo no model.
_QUICK_KINDS = {
    "maneuvers_melee": "maneuvers_melee",
    "maneuvers_ranged": "maneuvers_ranged",
    "maneuvers_defense": "maneuvers_defense",
}


def _quick_entry_template(kind: str, payload: dict, schema: str) -> dict:
    """Entry mínima por kind, escolhendo keys conforme schema:
    - schema='v2': name/damage/nh/details (inglês)
    - schema='v1': nome/damage/nh/detalhes (pt) — mesma estrutura usada
      pelas janelas legacy do template.
    """
    name = (payload.get("name") or "").strip() or "(sem nome)"
    nh = payload.get("nh", "")
    if schema == "v1":
        if kind == "maneuvers_defense":
            return {"nome": name, "nh": nh, "detalhes": ""}
        damage = (payload.get("damage") or "").strip()
        return {"nome": name, "damage": damage, "nh": nh, "detalhes": ""}
    # v2
    if kind == "maneuvers_defense":
        return {"name": name, "nh": nh, "details": ""}
    damage = (payload.get("damage") or "").strip()
    return {"name": name, "damage": damage, "nh": nh, "details": ""}


def _resolve_sheet_any(user, id: int):
    """Procura ficha por id em V2 primeiro, depois V1. Retorna (sheet, schema)
    ou (None, None) se não achar ou sem permissão.
    """
    v2 = CharacterSheetV2.objects.filter(pk=id).first()
    if v2 is not None:
        if not _can_edit(user, v2):
            return None, None
        return v2, "v2"
    v1 = CharacterSheet.objects.filter(pk=id).first()
    if v1 is not None:
        # V1 tem info_campanha.player_name. Sem campanha-FK, então o "edit
        # right" é só: sou o dono pelo nome do player.
        owner_name = (v1.info_campanha or {}).get("player_name")
        if owner_name and owner_name == user.username:
            return v1, "v1"
        # GM da campanha também pode editar — busca pela nome_campanha.
        camp_nome = (v1.info_campanha or {}).get("nome_campanha")
        if camp_nome:
            from gurps.models import Campanha as _C
            campanha = _C.objects.filter(nome=camp_nome).first()
            if campanha and campanha.dono_id == user.id:
                return v1, "v1"
    return None, None


@login_required
@require_http_methods(["POST"])
def api_quick_add(request, id: int, kind: str):
    """POST body: {name, damage?, nh}. Adiciona 1 entry à lista <kind>.
    Funciona em CharacterSheetV2 e CharacterSheet (V1 legacy)."""
    if kind not in _QUICK_KINDS:
        return JsonResponse({"error": f"kind inválido: {kind}"}, status=400)
    sheet, schema = _resolve_sheet_any(request.user, id)
    if sheet is None:
        return JsonResponse({"error": "ficha não encontrada ou sem permissão"},
                            status=404)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)
    attr = _QUICK_KINDS[kind]
    current = list(getattr(sheet, attr) or [])
    current.append(_quick_entry_template(kind, body, schema))
    setattr(sheet, attr, current)
    sheet.save()
    return JsonResponse({"ok": True, "kind": kind, "count": len(current),
                         "schema": schema})


@login_required
@require_http_methods(["POST"])
def api_quick_remove(request, id: int, kind: str, index: int):
    """Remove entry de posição <index> em <kind>. V2 ou V1."""
    if kind not in _QUICK_KINDS:
        return JsonResponse({"error": f"kind inválido: {kind}"}, status=400)
    sheet, schema = _resolve_sheet_any(request.user, id)
    if sheet is None:
        return JsonResponse({"error": "ficha não encontrada ou sem permissão"},
                            status=404)
    attr = _QUICK_KINDS[kind]
    current = list(getattr(sheet, attr) or [])
    if not (0 <= index < len(current)):
        return JsonResponse({"error": "index fora do range"}, status=400)
    current.pop(index)
    setattr(sheet, attr, current)
    sheet.save()
    return JsonResponse({"ok": True, "kind": kind, "count": len(current),
                         "schema": schema})
