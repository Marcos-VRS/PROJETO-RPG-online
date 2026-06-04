"""GM Tool Box — CRUD da biblioteca pessoal do user (UserAsset).

Status effects custom + tokens reutilizáveis que persistem através de
campanhas. Ver docs/TABLETOP_NEXT_PHASES.md §6.
"""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods

from gurps.models import UserAsset


def _serialize(ua: UserAsset) -> dict:
    return {
        "id": ua.id,
        "kind": ua.kind,
        "name": ua.name,
        "data": ua.data or {},
        "image_url": ua.image.url if ua.image else None,
        "source": ua.source,
    }


@login_required
@require_http_methods(["GET"])
def toolbox_list(request):
    """Lista a tool box do user logado. ?kind=status_effect filtra."""
    qs = UserAsset.objects.filter(owner=request.user)
    kind = request.GET.get("kind")
    if kind:
        qs = qs.filter(kind=kind)
    return JsonResponse({"items": [_serialize(x) for x in qs]})


@login_required
@require_http_methods(["POST"])
def toolbox_create(request):
    """Cria um item na tool box.
    Body JSON: {kind, name, data, source?}.
    """
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    kind = body.get("kind")
    name = (body.get("name") or "").strip()
    if kind not in dict(UserAsset.KIND_CHOICES):
        return JsonResponse({"error": "kind inválido"}, status=400)
    if not name:
        return JsonResponse({"error": "nome obrigatório"}, status=400)

    source = body.get("source", "custom")
    if source not in dict(UserAsset.SOURCE_CHOICES):
        source = "custom"

    ua = UserAsset.objects.create(
        owner=request.user,
        kind=kind,
        name=name[:80],
        data=body.get("data") or {},
        source=source,
    )
    return JsonResponse({"ok": True, "item": _serialize(ua)})


@login_required
@require_http_methods(["POST"])
def toolbox_delete(request, item_id: int):
    """Remove um item da tool box (só o owner)."""
    ua = UserAsset.objects.filter(pk=item_id).first()
    if ua is None:
        return JsonResponse({"error": "não existe"}, status=404)
    if ua.owner_id != request.user.id:
        return HttpResponseForbidden("Não é seu.")
    ua.delete()
    return JsonResponse({"ok": True})
