"""Geração de mapas por IA (Claude headless).

Fase 2 — fila + degradação graciosa. Os endpoints aqui NUNCA dependem do
gerador estar de pé: criar um pedido sempre responde na hora; se o worker
estiver offline (sem heartbeat recente) ou travar, o pedido vira ``failed``
por timeout — o jogo/chat/mapa continuam funcionando.

Endpoints:
  POST /map-gen/<campanha_id>/request/   GM cria um pedido (pending).
  GET  /map-gen/status/<req_id>/         Poll do estado (timeout lazy).
"""
import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from gurps import ai_context
from gurps.models import Campanha, CampanhaAssets, GenWorkerStatus, MapGenRequest

# Pedido pending/processing além disso (e sem worker online) vira failed.
REQUEST_TIMEOUT_SECONDS = 180
PROMPT_MAX = 2000


def _serialize(req: MapGenRequest) -> dict:
    return {
        "id": req.id,
        "status": req.status,
        "prompt": req.prompt,
        "error": req.error,
        "has_result": bool(req.result_svg),
        "result_asset_id": req.result_asset_id,
        "created_at": req.created_at.isoformat() if req.created_at else None,
    }


@login_required(login_url="gurps:login")
def map_gen_request(request, campanha_id):
    """GM enfileira um pedido de mapa. Responde na hora; não trava se offline."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM pode gerar mapas"}, status=403)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return JsonResponse({"error": "descreva o mapa (prompt vazio)"}, status=400)
    prompt = prompt[:PROMPT_MAX]

    online = GenWorkerStatus.is_online()
    req = MapGenRequest.objects.create(
        campanha=campanha,
        requested_by=request.user,
        prompt=prompt,
        grid_size_px=campanha.grid_size_px or 64,
        status="pending",
    )
    return JsonResponse({
        "ok": True,
        "id": req.id,
        "status": req.status,
        # Cliente usa isso pra mostrar "gerando…" (online) vs "gerador offline"
        # (na fila; será atendido se um worker subir dentro do timeout).
        "worker_online": online,
    })


@login_required(login_url="gurps:login")
def map_gen_status(request, req_id):
    """Poll do estado de um pedido. Aplica timeout lazy (offline demais → failed)."""
    req = get_object_or_404(MapGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)

    if req.status in ("pending", "processing"):
        age = (timezone.now() - req.created_at).total_seconds()
        if age > REQUEST_TIMEOUT_SECONDS and not GenWorkerStatus.is_online():
            req.status = "failed"
            req.error = "Gerador de mapas offline ou sem resposta (timeout)."
            req.save(update_fields=["status", "error", "updated_at"])

    return JsonResponse({
        "ok": True,
        "worker_online": GenWorkerStatus.is_online(),
        **_serialize(req),
    })


@login_required(login_url="gurps:login")
def map_gen_list(request, campanha_id):
    """Lista os pedidos recentes da campanha (pro painel do GM). GM only."""
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    # Ativos + histórico recente (esconde approved/discarded pra não poluir).
    qs = (MapGenRequest.objects
          .filter(campanha=campanha)
          .exclude(status__in=["approved", "discarded"])
          .order_by("-created_at")[:20])
    return JsonResponse({
        "ok": True,
        "worker_online": GenWorkerStatus.is_online(),
        "requests": [_serialize(r) for r in qs],
    })


@login_required(login_url="gurps:login")
def map_gen_svg(request, req_id):
    """Serve o SVG gerado (preview). GM only."""
    req = get_object_or_404(MapGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    if not req.result_svg:
        return HttpResponse(status=404)
    resp = HttpResponse(req.result_svg, content_type="image/svg+xml")
    resp["Cache-Control"] = "no-store"
    return resp


@login_required(login_url="gurps:login")
def map_gen_approve(request, req_id):
    """GM aprova um mapa gerado → vira CampanhaAssets (show=False)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(MapGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status != "done" or not req.result_svg:
        return JsonResponse({"error": "pedido não está pronto pra aprovar"}, status=400)

    # Grava o SVG em media/ e cria o asset (oculto dos players).
    fname = f"campanhas_assets/gen_{req.id}.svg"
    full = os.path.join(settings.MEDIA_ROOT, fname.replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(req.result_svg)

    name = (req.prompt or "Mapa gerado").strip()[:40] or "Mapa gerado"
    asset = CampanhaAssets(
        campanha=req.campanha,
        name=name,
        description="Mapa gerado por IA — " + (req.prompt or "")[:200],
        slot=2,
        show=False,
    )
    asset.image.name = fname
    asset.save()

    req.status = "approved"
    req.result_asset = asset
    req.save(update_fields=["status", "result_asset", "updated_at"])

    # Acumula no contexto da campanha (mapas aprovados também contam).
    ai_context.append_approved_context(
        req.campanha, f"[mapa] {name}: {(req.prompt or '')[:200]}")

    return JsonResponse({"ok": True, "asset_id": asset.id, "asset_name": asset.name})


@login_required(login_url="gurps:login")
def map_gen_discard(request, req_id):
    """GM descarta um pedido (não vira asset)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(MapGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    req.status = "discarded"
    req.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True})
