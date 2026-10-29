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
from gurps.models import Campanha, CampanhaAssets, VideoBeat, VideoGenRequest

PROMPT_MAX = 2000
STYLE_CHOICES = {"anime", "cinematic_dark", "photoreal", "oil", "gritty", "none"}
AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".wav", ".opus", ".flac")
BEAT_MIN_MS = 1000
BEAT_MAX_MS = 30000


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
        # Pode retomar se já tem storyboard e não está rodando (parcial/falhou/pronto).
        "can_resume": bool(req.storyboard) and req.status in ("failed", "done"),
        "pause_requested": bool(req.pause_requested),
        "created_at": req.created_at.isoformat() if req.created_at else None,
    }


def _gm_or_403(campanha_id, request):
    """Devolve (campanha, None) se o user é o GM; (None, JsonResponse 403/404)."""
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return None, JsonResponse({"error": "só o GM pode isso"}, status=403)
    return campanha, None


def _save_music_choice(request, body):
    """Resolve a música escolhida (upload novo > faixa existente). Retorna o rel
    sob MEDIA_ROOT ou ''. Reusado pelo modo rápido e pelo editor de beats."""
    music_upload = request.FILES.get("music_upload") if request.FILES else None
    if music_upload is not None and music_upload.name.lower().endswith(AUDIO_EXTS):
        safe = get_valid_filename(music_upload.name) or "musica.mp3"
        rel = "music/uploads/" + safe
        dest = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in music_upload.chunks():
                f.write(chunk)
        return rel
    chosen = (body.get("music_file") or "").strip()
    if chosen and video_assembly.resolve_music_rel(settings.MEDIA_ROOT, chosen):
        return chosen
    return ""


def _serialize_beat(b):
    return {
        "id": b.id,
        "order": b.order,
        "start_ms": b.start_ms,
        "end_ms": b.end_ms,
        "duration_ms": b.duration_ms,
        "user_prompt": b.user_prompt or "",
        "correction": b.correction or "",
        "expanded_prompt": b.expanded_prompt or "",
        "ref_asset_id": b.ref_asset_id,
        "ref_asset_name": (b.ref_asset.name if b.ref_asset_id else ""),
        "ref_mode": b.ref_mode,
        "fidelity": b.fidelity,
        "status": b.status,
        "progress": b.progress or "",
        "error": b.error or "",
        "has_clip": bool(b.clip_file),
        "transition": b.transition,
        "transition_ms": b.transition_ms,
    }


def _serialize_project(req, with_beats=True):
    beats = list(req.beats.order_by("start_ms", "id")) if with_beats else []
    used_ms = max((b.end_ms for b in beats), default=0) if with_beats else 0
    return {
        "id": req.id,
        "mode": req.mode,
        "status": req.status,
        "prompt": req.prompt,
        "style": req.style,
        "render_style": req.render_style,
        "use_context": req.use_context,
        "music_file": os.path.basename(req.music_file) if req.music_file else "",
        "music_rel": req.music_file or "",
        "audio_duration_ms": req.audio_duration_ms,
        "used_ms": used_ms,
        "progress": req.progress,
        "error": req.error,
        "has_result": bool(req.result_file),
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "beats": [_serialize_beat(b) for b in beats] if with_beats else [],
    }


@login_required(login_url="gurps:login")
def videogen_project_create(request, campanha_id):
    """Cria um PROJETO de vídeo em modo editor de beats. Exige escolher/subir o
    áudio (a minutagem dele ancora os beats na timeline)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha, err = _gm_or_403(campanha_id, request)
    if err:
        return err
    body = request.POST if (request.content_type or "").startswith("multipart/") else _json_body(request)
    if body is None:
        return JsonResponse({"error": "corpo inválido"}, status=400)
    style = body.get("style") if body.get("style") in STYLE_CHOICES else "anime"
    render_style = "realism" if body.get("render_style") == "realism" else "anime"
    uc_raw = body.get("use_context")
    use_context = True if uc_raw is None else str(uc_raw).lower() not in ("0", "false", "no", "")
    prompt = (body.get("prompt") or "").strip()[:PROMPT_MAX]
    music_file = _save_music_choice(request, body)
    if not music_file:
        return JsonResponse({"error": "escolha ou envie uma música primeiro (a minutagem dela ancora os beats)"}, status=400)
    audio_ms = 0
    mpath = video_assembly.resolve_music_rel(settings.MEDIA_ROOT, music_file)
    if mpath:
        audio_ms = video_assembly.media_duration_ms(mpath)
    req = VideoGenRequest.objects.create(
        campanha=campanha, requested_by=request.user, prompt=prompt or "(vídeo por beats)",
        style=style, render_style=render_style, use_context=use_context, mode="beats",
        status="editing", music_file=music_file, audio_duration_ms=audio_ms)
    return JsonResponse({"ok": True, "project": _serialize_project(req)})


@login_required(login_url="gurps:login")
def videogen_projects(request, campanha_id):
    """Lista os projetos de vídeo em modo beats (pro painel do estúdio)."""
    campanha, err = _gm_or_403(campanha_id, request)
    if err:
        return err
    qs = (VideoGenRequest.objects.filter(campanha=campanha, mode="beats")
          .exclude(status="discarded").order_by("-created_at")[:20])
    comfy = comfyui_client.status()
    return JsonResponse({
        "ok": True, "comfy": comfy,
        "video_models": comfyui_client.video_pick_checkpoint() if comfy.get("online") else False,
        "projects": [_serialize_project(r) for r in qs],
    })


@login_required(login_url="gurps:login")
def videogen_project_detail(request, req_id):
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    comfy = comfyui_client.status()
    data = _serialize_project(req)
    data["comfy"] = comfy
    data["video_models"] = comfyui_client.video_pick_checkpoint() if comfy.get("online") else False
    return JsonResponse({"ok": True, "project": data})


@login_required(login_url="gurps:login")
def videogen_project_update(request, req_id):
    """Edita o TEMA GERAL do projeto depois de criado: ideia geral, estilo, ler
    journal e a música (troca a faixa — re-mede a minutagem). Não mexe nos beats
    já gerados; o prompt/estilo valem pras próximas gerações."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status in ("pending", "processing"):
        return JsonResponse({"error": "aguarde a montagem terminar pra editar o tema"}, status=400)
    body = request.POST if (request.content_type or "").startswith("multipart/") else (_json_body(request) or {})
    fields = []
    if "prompt" in body:
        req.prompt = (body.get("prompt") or "").strip()[:PROMPT_MAX] or "(vídeo por beats)"
        fields.append("prompt")
    if body.get("style") in STYLE_CHOICES:
        req.style = body.get("style")
        fields.append("style")
    if body.get("render_style") in ("anime", "realism"):
        req.render_style = body.get("render_style")
        fields.append("render_style")
    if "use_context" in body:
        req.use_context = str(body.get("use_context")).lower() not in ("0", "false", "no", "")
        fields.append("use_context")
    newmusic = _save_music_choice(request, body)
    if newmusic:
        req.music_file = newmusic
        mpath = video_assembly.resolve_music_rel(settings.MEDIA_ROOT, newmusic)
        req.audio_duration_ms = video_assembly.media_duration_ms(mpath) if mpath else req.audio_duration_ms
        fields += ["music_file", "audio_duration_ms"]
    if fields:
        req.save(update_fields=fields + ["updated_at"])
    return JsonResponse({"ok": True, "project": _serialize_project(req)})


def _reactivate_if_terminal(req):
    """Se o projeto já foi montado/falhou, volta pra 'editing' ao mexer num beat."""
    if req.mode == "beats" and req.status in ("done", "failed", "approved"):
        req.status = "editing"
        req.save(update_fields=["status", "updated_at"])


def _resolve_ref_asset(campanha, body):
    rid = body.get("ref_asset_id")
    if not rid:
        return None
    try:
        return CampanhaAssets.objects.filter(campanha=campanha, id=int(rid)).first()
    except (TypeError, ValueError):
        return None


def _beat_times(body, cur_start, cur_end, audio_ms):
    """Normaliza (start_ms, end_ms) do beat: >=0, dentro do áudio, e com a
    duração entre BEAT_MIN e BEAT_MAX."""
    def _as_int(key, default):
        v = body.get(key)
        if v is None or v == "":
            return default
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default
    start = max(0, _as_int("start_ms", cur_start))
    end = _as_int("end_ms", cur_end)
    if audio_ms and audio_ms > 0:
        start = min(start, max(0, audio_ms - BEAT_MIN_MS))
        end = min(end, audio_ms)
    if end < start + BEAT_MIN_MS:
        end = start + BEAT_MIN_MS
    if end - start > BEAT_MAX_MS:
        end = start + BEAT_MAX_MS
    return start, end


def _resequence(project):
    """Reindexa `order` pela ordem cronológica (start_ms) — a montagem segue isso."""
    for i, b in enumerate(project.beats.order_by("start_ms", "id")):
        if b.order != i:
            b.order = i
            b.save(update_fields=["order"])


@login_required(login_url="gurps:login")
def videogen_beat_add(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    body = _json_body(request) or request.POST
    from django.db.models import Max  # noqa: WPS433
    # por padrão o novo beat começa onde o último terminou (contíguo na música)
    prev_end = req.beats.aggregate(m=Max("end_ms"))["m"] or 0
    audio = req.audio_duration_ms or 0
    dft_start = prev_end if not audio else min(prev_end, max(0, audio - BEAT_MIN_MS))
    start, end = _beat_times(body, dft_start, dft_start + 2000, audio)
    beat = VideoBeat.objects.create(
        project=req, order=0, start_ms=start, end_ms=end, duration_ms=end - start,
        user_prompt=(body.get("user_prompt") or "").strip()[:PROMPT_MAX],
        ref_asset=_resolve_ref_asset(req.campanha, body),
        transition=("crossfade" if body.get("transition") == "crossfade" else "cut"),
        transition_ms=_clamp_transition(body.get("transition_ms")),
    )
    _resequence(req)
    _reactivate_if_terminal(req)
    beat.refresh_from_db()
    return JsonResponse({"ok": True, "beat": _serialize_beat(beat)})


@login_required(login_url="gurps:login")
def videogen_beat_update(request, beat_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    beat = get_object_or_404(VideoBeat, id=beat_id)
    if beat.project.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    body = _json_body(request) or request.POST
    changed = False
    if "user_prompt" in body:
        beat.user_prompt = (body.get("user_prompt") or "").strip()[:PROMPT_MAX]; changed = True
    if "correction" in body:
        beat.correction = (body.get("correction") or "").strip()[:PROMPT_MAX]; changed = True
    if "start_ms" in body or "end_ms" in body:
        start, end = _beat_times(body, beat.start_ms, beat.end_ms, beat.project.audio_duration_ms)
        beat.start_ms, beat.end_ms, beat.duration_ms = start, end, end - start
        changed = True
    if "ref_asset_id" in body:
        beat.ref_asset = _resolve_ref_asset(beat.project.campanha, body); changed = True
    if "ref_mode" in body:
        beat.ref_mode = "animate" if body.get("ref_mode") == "animate" else "style"; changed = True
    if "fidelity" in body:
        try:
            beat.fidelity = min(1.0, max(0.0, float(body.get("fidelity"))))
            changed = True
        except (TypeError, ValueError):
            pass
    if "transition" in body:
        beat.transition = "crossfade" if body.get("transition") == "crossfade" else "cut"
    if "transition_ms" in body:
        beat.transition_ms = _clamp_transition(body.get("transition_ms"))
    # Mudou o conteúdo da cena? marca pra regerar (mantém o clipe antigo p/ preview).
    if changed and beat.status in ("done", "failed"):
        beat.status = "empty"
    beat.save()
    _resequence(beat.project)
    _reactivate_if_terminal(beat.project)
    beat.refresh_from_db()
    return JsonResponse({"ok": True, "beat": _serialize_beat(beat)})


@login_required(login_url="gurps:login")
def videogen_beat_delete(request, beat_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    beat = get_object_or_404(VideoBeat, id=beat_id)
    project = beat.project
    if project.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    import shutil
    bdir = os.path.join(settings.MEDIA_ROOT, "videobeats", str(project.id), f"beat_{beat.id}")
    shutil.rmtree(bdir, ignore_errors=True)
    clip = os.path.join(settings.MEDIA_ROOT, (beat.clip_file or "").replace("/", os.sep))
    if beat.clip_file and os.path.exists(clip):
        try:
            os.remove(clip)
        except OSError:
            pass
    beat.delete()
    # reindexa a ordem
    for i, b in enumerate(project.beats.order_by("order", "id")):
        if b.order != i:
            b.order = i
            b.save(update_fields=["order"])
    _reactivate_if_terminal(project)
    return JsonResponse({"ok": True})


@login_required(login_url="gurps:login")
def videogen_beat_reorder(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    body = _json_body(request) or {}
    ids = body.get("order") or []
    pos = {int(i): n for n, i in enumerate(ids)}
    for b in req.beats.all():
        if b.id in pos and b.order != pos[b.id]:
            b.order = pos[b.id]
            b.save(update_fields=["order"])
    _reactivate_if_terminal(req)
    return JsonResponse({"ok": True, "project": _serialize_project(req)})


@login_required(login_url="gurps:login")
def videogen_beat_generate(request, beat_id):
    """Enfileira a geração (ou regeração) de UM beat. Só aquele beat regenera."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    beat = get_object_or_404(VideoBeat, id=beat_id)
    if beat.project.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if not (beat.user_prompt or "").strip() and not (beat.project.prompt or "").strip():
        return JsonResponse({"error": "descreva a cena do beat primeiro"}, status=400)
    beat.status = "pending"
    beat.error = ""
    beat.progress = "na fila"
    beat.save(update_fields=["status", "error", "progress", "updated_at"])
    _reactivate_if_terminal(beat.project)
    comfy = comfyui_client.status()
    return JsonResponse({"ok": True, "comfy_online": comfy.get("online", False),
                         "beat": _serialize_beat(beat)})


@login_required(login_url="gurps:login")
def videogen_beat_mp4(request, beat_id):
    beat = get_object_or_404(VideoBeat, id=beat_id)
    if beat.project.campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    if not beat.clip_file:
        return HttpResponse(status=404)
    full = os.path.join(settings.MEDIA_ROOT, beat.clip_file.replace("/", os.sep))
    if not os.path.exists(full):
        return HttpResponse(status=404)
    resp = FileResponse(open(full, "rb"), content_type="video/mp4")
    resp["Cache-Control"] = "no-store"
    resp["Accept-Ranges"] = "bytes"
    return resp


@login_required(login_url="gurps:login")
def videogen_project_assemble(request, req_id):
    """Monta o vídeo final do projeto (clipes dos beats na ordem + transições +
    trilha). Enfileira pro worker (status=pending, mode=beats)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    done = req.beats.filter(status="done").exclude(clip_file="").count()
    if done == 0:
        return JsonResponse({"error": "gere ao menos um beat antes de montar"}, status=400)
    req.status = "pending"
    req.error = ""
    req.progress = "montagem na fila"
    req.save(update_fields=["status", "error", "progress", "updated_at"])
    comfy = comfyui_client.status()
    return JsonResponse({"ok": True, "comfy_online": comfy.get("online", False)})


def _clamp_transition(v):
    try:
        return max(100, min(int(v), 3000))
    except (TypeError, ValueError):
        return 500


def _json_body(request):
    if (request.content_type or "").startswith("application/json"):
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


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
    render_style = "realism" if body.get("render_style") == "realism" else "anime"
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
        style=style, render_style=render_style, use_context=use_context,
        target_seconds=target, status="pending", music_file=music_file,
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
    qs = (VideoGenRequest.objects.filter(campanha=campanha, mode="auto")
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
def videogen_pause(request, req_id):
    """GM pede pausa: o worker para após a cena atual e monta o parcial pra ver.
    Depois dá pra Continuar, Aprovar ou Descartar."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if req.status != "processing":
        return JsonResponse({"error": "não está gerando"}, status=400)
    req.pause_requested = True
    req.save(update_fields=["pause_requested", "updated_at"])
    return JsonResponse({"ok": True})


@login_required(login_url="gurps:login")
def videogen_resume(request, req_id):
    """Retoma um vídeo parcial/falho: re-enfileira (status=pending) mantendo o
    storyboard e as cenas já geradas — o worker só gera as que faltam e remonta."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    if not req.storyboard:
        return JsonResponse({"error": "sem storyboard pra retomar"}, status=400)
    req.status = "pending"
    req.error = ""
    req.progress = "retomando..."
    req.save(update_fields=["status", "error", "progress", "updated_at"])
    comfy = comfyui_client.status()
    return JsonResponse({"ok": True, "comfy_online": comfy.get("online", False)})


@login_required(login_url="gurps:login")
def videogen_discard(request, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    req = get_object_or_404(VideoGenRequest, id=req_id)
    if req.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "sem permissão"}, status=403)
    req.status = "discarded"
    req.save(update_fields=["status", "updated_at"])
    # limpa as cenas persistidas (não vai mais retomar)
    import shutil
    for d in (os.path.join(settings.MEDIA_ROOT, "videogen", "clips", str(req.id)),
              os.path.join(settings.MEDIA_ROOT, "videobeats", str(req.id))):
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
    return JsonResponse({"ok": True})
