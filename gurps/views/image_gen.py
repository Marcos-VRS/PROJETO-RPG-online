"""Estúdio de Imagem por IA local (ComfyUI na GPU do host).

Fila + degradação graciosa (mesmo padrão do map-gen). Os endpoints nunca
dependem do ComfyUI estar de pé; se estiver offline, o pedido expira por
timeout e o jogo continua normal.

Endpoints:
  GET  /imagegen/<campanha_id>/status/   status do ComfyUI (online + GPU)
  POST /imagegen/<campanha_id>/request/  cria um pedido (pending)
  GET  /imagegen/<campanha_id>/list/     pedidos recentes (painel do GM)
  GET  /imagegen/req/<req_id>/status/    poll de 1 pedido (timeout lazy)
  GET  /imagegen/png/<req_id>/           serve o PNG gerado (preview)
  POST /imagegen/<req_id>/approve/       vira CampanhaAssets (show=False)
  POST /imagegen/<req_id>/discard/
"""
import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from gurps import ai_context, comfyui_client
from gurps.models import Campanha, CampanhaAssets, ImageGenRequest

REQUEST_TIMEOUT_SECONDS = 360  # geração de imagem pode ser lenta em GPU modesta
PROMPT_MAX = 1500

# Tamanhos default por tipo (SDXL-Turbo vai bem em 768-1024).
SIZE_BY_KIND = {
    "personagem": (768, 1024),
    "mapa": (1024, 1024),
    "cena": (1024, 768),
}


def _serialize(req):
    return {
        "id": req.id,
        "kind": req.kind,
        "status": req.status,
        "prompt": req.prompt,
        "error": req.error,
        "has_result": bool(req.result_file),
        "has_ref": bool(req.ref_image or req.ref_asset_id),
        "expanded_prompt": req.expanded_prompt or "",
        "used_context": req.use_context,
        "result_asset_id": req.result_asset_id,
        "created_at": req.created_at.isoformat() if req.created_at else None,
    }


@login_required(login_url="gurps:login")
def imagegen_status(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    return JsonResponse({"ok": True, "comfy": comfyui_client.status()})


@login_required(login_url="gurps:login")
def imagegen_request(request, campanha_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM pode gerar imagens"}, status=403)

    # Aceita multipart (com imagem de referência) OU JSON (sem). A UI manda
    # multipart (FormData) sempre que possível.
    ref_file = None
    ref_weight = 0.7
    if request.content_type and request.content_type.startswith("multipart/"):
        body = request.POST
        ref_file = request.FILES.get("ref_image")
        try:
            ref_weight = float(body.get("ref_weight") or 0.7)
        except (TypeError, ValueError):
            ref_weight = 0.7
    else:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

    prompt = (body.get("prompt") or "").strip()[:PROMPT_MAX]
    if not prompt:
        return JsonResponse({"error": "descreva a imagem (prompt vazio)"}, status=400)
    kind = body.get("kind") if body.get("kind") in SIZE_BY_KIND else "personagem"
    dw, dh = SIZE_BY_KIND[kind]
    width = int(body.get("width") or dw)
    height = int(body.get("height") or dh)
    # limita o tamanho pra não estourar VRAM
    width = max(384, min(width, 1280))
    height = max(384, min(height, 1280))
    ref_weight = max(0.0, min(ref_weight, 1.5))

    style = (body.get("style") or "cinematic_dark")[:32]
    # use_context: default True; "0"/"false"/"" desliga.
    uc_raw = body.get("use_context")
    use_context = True if uc_raw is None else str(uc_raw).lower() not in ("0", "false", "no", "")

    # Referência escolhida do próprio journal (asset da campanha).
    ref_asset = None
    ref_asset_id = body.get("ref_asset_id")
    if ref_asset_id:
        ref_asset = CampanhaAssets.objects.filter(
            id=ref_asset_id, campanha=campanha).first()

    comfy = comfyui_client.status()
    req = ImageGenRequest.objects.create(
        campanha=campanha, requested_by=request.user, kind=kind,
        prompt=prompt, width=width, height=height, status="pending",
        ref_weight=ref_weight, style=style, use_context=use_context,
        ref_asset=ref_asset,
    )
    if ref_file is not None:
        req.ref_image = ref_file
        req.save(update_fields=["ref_image"])
    return JsonResponse({
        "ok": True, "id": req.id, "status": req.status,
        "has_ref": bool(ref_file or ref_asset),
        "comfy_online": comfy.get("online", False),
        "comfy_device": comfy.get("device"),
    })


@login_required(login_url="gurps:login")
def imagegen_journal(request, campanha_id):
    """Lista as imagens RASTER do journal da campanha pro seletor de referência
    (SVGs são excluídos — IP-Adapter não lê SVG). GM only."""
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    items = []
    qs = (CampanhaAssets.objects.filter(campanha=campanha, slot__in=[1, 2])
          .order_by("-id")[:60])
    for a in qs:
        if not a.image:
            continue
        nm = (a.image.name or "").lower()
        if nm.endswith(".svg"):
            continue
        try:
            url = a.image.url
        except Exception:  # noqa: BLE001
            continue
        items.append({"id": a.id, "name": a.name or f"asset {a.id}", "url": url})
    return JsonResponse({"ok": True, "items": items})


@login_required(login_url="gurps:login")
def imagegen_req_status(request, req_id):
    req = get_object_or_404(ImageGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status in ("pending", "processing"):
        age = (timezone.now() - req.created_at).total_seconds()
        if age > REQUEST_TIMEOUT_SECONDS and not comfyui_client.status().get("online"):
            req.status = "failed"
            req.error = "ComfyUI offline ou sem resposta (timeout)."
            req.save(update_fields=["status", "error", "updated_at"])
    return JsonResponse({"ok": True, **_serialize(req)})


@login_required(login_url="gurps:login")
def imagegen_list(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    qs = (ImageGenRequest.objects.filter(campanha=campanha)
          .exclude(status__in=["approved", "discarded"]).order_by("-created_at")[:20])
    return JsonResponse({
        "ok": True,
        "comfy": comfyui_client.status(),
        "requests": [_serialize(r) for r in qs],
    })


@login_required(login_url="gurps:login")
def imagegen_png(request, req_id):
    req = get_object_or_404(ImageGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    if not req.result_file:
        return HttpResponse(status=404)
    full = os.path.join(settings.MEDIA_ROOT, req.result_file.replace("/", os.sep))
    if not os.path.exists(full):
        return HttpResponse(status=404)
    with open(full, "rb") as f:
        data = f.read()
    resp = HttpResponse(data, content_type="image/png")
    resp["Cache-Control"] = "no-store"
    return resp


@login_required(login_url="gurps:login")
def imagegen_approve(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(ImageGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status != "done" or not req.result_file:
        return JsonResponse({"error": "pedido não está pronto pra aprovar"}, status=400)

    src = os.path.join(settings.MEDIA_ROOT, req.result_file.replace("/", os.sep))
    if not os.path.exists(src):
        return JsonResponse({"error": "arquivo da imagem sumiu"}, status=400)
    dest_rel = f"campanhas_assets/imagegen_{req.id}.png"
    dest = os.path.join(settings.MEDIA_ROOT, dest_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(src, "rb") as fsrc, open(dest, "wb") as fdst:
        fdst.write(fsrc.read())

    name = (req.prompt or "Imagem gerada").strip()[:40] or "Imagem gerada"
    asset = CampanhaAssets(
        campanha=req.campanha, name=name,
        description=f"Imagem gerada por IA ({req.kind}) — " + (req.prompt or "")[:200],
        slot=2, show=False,
    )
    asset.image.name = dest_rel
    asset.save()

    req.status = "approved"
    req.result_asset = asset
    req.save(update_fields=["status", "result_asset", "updated_at"])

    # Acumula no contexto da campanha o que foi aprovado (alimenta gerações futuras).
    desc = (req.expanded_prompt or req.prompt or "").strip()[:220]
    ai_context.append_approved_context(req.campanha, f"[{req.kind}] {name}: {desc}")

    return JsonResponse({"ok": True, "asset_id": asset.id, "asset_name": asset.name})


@login_required(login_url="gurps:login")
def imagegen_discard(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(ImageGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    req.status = "discarded"
    req.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True})
