"""Estúdio de Vídeo por IA local (AnimateDiff na GPU do host).

Mesma pegada do image_gen: fila + degradação graciosa. Fica no menu de GM da
campanha (fora da tela de jogo). O worker `videogen_worker` processa os pending.

Endpoints:
  POST /videogen/<campanha_id>/request/   cria pedido (pending)
  GET  /videogen/<campanha_id>/list/      pedidos recentes (painel do GM)
  GET  /videogen/mp4/<req_id>/            serve o mp4 gerado (preview)
  POST /videogen/<req_id>/approve/        marca aprovado (fica salvo)
  POST /videogen/<req_id>/discard/
"""
import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import get_valid_filename

from gurps import ai_context, comfyui_client, video_assembly
from gurps.models import Campanha, VideoGenRequest

PROMPT_MAX = 2000
STYLE_CHOICES = {"anime", "cinematic_dark", "photoreal", "oil", "gritty", "none"}
AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".wav", ".opus", ".flac")


def _serialize(req):
    return {
        "id": req.id,
        "status": req.status,
        "prompt": req.prompt,
        "mood": req.mood,
        "music_file": os.path.basename(req.music_file) if req.music_file else "",
        "progress": req.progress,
        "error": req.error,
        "target_seconds": req.target_seconds,
        "has_result": bool(req.result_file),
        "expanded_prompt": req.expanded_prompt or "",
        "created_at": req.created_at.isoformat() if req.created_at else None,
    }


@login_required(login_url="gurps:login")
def videogen_request(request, campanha_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM pode gerar vídeos"}, status=403)
    # Aceita multipart (com upload de música) OU JSON (sem).
    music_upload = None
    if request.content_type and request.content_type.startswith("multipart/"):
        body = request.POST
        music_upload = request.FILES.get("music_upload")
    else:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

    prompt = (body.get("prompt") or "").strip()[:PROMPT_MAX]
    if not prompt:
        return JsonResponse({"error": "descreva o que aconteceu (prompt vazio)"}, status=400)
    style = body.get("style") if body.get("style") in STYLE_CHOICES else "anime"
    uc_raw = body.get("use_context")
    use_context = True if uc_raw is None else str(uc_raw).lower() not in ("0", "false", "no", "")
    try:
        target = int(body.get("target_seconds") or 90)
    except (TypeError, ValueError):
        target = 90
    target = max(10, min(target, 180))

    # Música escolhida: upload novo tem prioridade; senão uma faixa já existente
    # (validada contra path-traversal); senão vazio = automática pelo clima.
    music_file = ""
    if music_upload is not None and music_upload.name.lower().endswith(AUDIO_EXTS):
        safe = get_valid_filename(music_upload.name) or "musica.mp3"
        rel = "music/uploads/" + safe
        dest = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in music_upload.chunks():
                f.write(chunk)
        music_file = rel
    else:
        chosen = (body.get("music_file") or "").strip()
        if chosen and video_assembly.resolve_music_rel(settings.MEDIA_ROOT, chosen):
            music_file = chosen

    comfy = comfyui_client.status()
    has_models = comfyui_client.video_pick_checkpoint() if comfy.get("online") else False
    req = VideoGenRequest.objects.create(
        campanha=campanha, requested_by=request.user, prompt=prompt,
        style=style, use_context=use_context, target_seconds=target, status="pending",
        music_file=music_file,
    )
    return JsonResponse({
        "ok": True, "id": req.id, "status": req.status,
        "comfy_online": comfy.get("online", False),
        "video_models": has_models,
    })


@login_required(login_url="gurps:login")
def videogen_music(request, campanha_id):
    """Lista as faixas de música disponíveis (por clima) pro seletor da UI."""
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    return JsonResponse({"ok": True, "tracks": video_assembly.list_music(settings.MEDIA_ROOT)})


@login_required(login_url="gurps:login")
def videogen_list(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    qs = (VideoGenRequest.objects.filter(campanha=campanha)
          .exclude(status="discarded").order_by("-created_at")[:20])
    comfy = comfyui_client.status()
    return JsonResponse({
        "ok": True,
        "comfy": comfy,
        "video_models": comfyui_client.video_pick_checkpoint() if comfy.get("online") else False,
        "requests": [_serialize(r) for r in qs],
    })


@login_required(login_url="gurps:login")
def videogen_mp4(request, req_id):
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    if not req.result_file:
        return HttpResponse(status=404)
    full = os.path.join(settings.MEDIA_ROOT, req.result_file.replace("/", os.sep))
    if not os.path.exists(full):
        return HttpResponse(status=404)
    resp = FileResponse(open(full, "rb"), content_type="video/mp4")
    resp["Cache-Control"] = "no-store"
    resp["Accept-Ranges"] = "bytes"
    return resp


@login_required(login_url="gurps:login")
def videogen_approve(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status != "done" or not req.result_file:
        return JsonResponse({"error": "vídeo não está pronto pra aprovar"}, status=400)
    req.status = "approved"
    req.save(update_fields=["status", "updated_at"])
    # Acumula no contexto da campanha (o que foi retratado em vídeo também conta).
    ai_context.append_approved_context(
        req.campanha, f"[vídeo] {(req.prompt or '')[:120]} (clima {req.mood})")
    return JsonResponse({"ok": True})


@login_required(login_url="gurps:login")
def videogen_discard(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    req.status = "discarded"
    req.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True})
