"""Gerador de Personagem (LoRA SD1.5): endpoints do estúdio.

Fluxo: criar -> gerar folha de poses (dataset) -> curar (keep) -> treinar ->
usar no vídeo (o LoRA fica disponível pros projetos de vídeo pela palavra-gatilho).
Mesmo padrão de fila/degradação graciosa dos outros estúdios.
"""
import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify

from gurps.models import Campanha, CampanhaAssets, CharacterLora, CharacterLoraImage


def _gm_or_403(campanha_id, request):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return None, JsonResponse({"error": "só o GM"}, status=403)
    return campanha, None


def _trigger_from(name, lora_id=None):
    s = slugify(name or "").replace("-", "_")[:30] or f"char{lora_id or ''}"
    return "ch_" + s


def _serialize_image(im):
    return {"id": im.id, "pose": im.pose, "keep": im.keep,
            "url": f"/charlora/image/{im.id}/"}


def _serialize(cl, with_images=True):
    d = {
        "id": cl.id, "name": cl.name, "trigger_word": cl.trigger_word,
        "description": cl.description, "status": cl.status,
        "progress": cl.progress, "progress_pct": cl.progress_pct, "error": cl.error,
        "n_poses": cl.n_poses, "rank": cl.rank, "train_steps": cl.train_steps,
        "has_seed": bool(cl.seed_asset_id or cl.seed_image),
        "seed_asset_id": cl.seed_asset_id,
        "lora_file": cl.lora_file, "trained": cl.status == "trained",
        "n_images": cl.images.count() if cl.pk else 0,
        "n_keep": cl.images.filter(keep=True).count() if cl.pk else 0,
    }
    if with_images:
        d["images"] = [_serialize_image(im) for im in cl.images.all()]
    return d


@login_required(login_url="gurps:login")
def charlora_studio(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    return render(request, "global/charlora_studio.html", {"campanha": campanha})


@login_required(login_url="gurps:login")
def charlora_list(request, campanha_id):
    campanha, err = _gm_or_403(campanha_id, request)
    if err:
        return err
    qs = CharacterLora.objects.filter(campanha=campanha).order_by("-created_at")[:50]
    from gurps import comfyui_client  # noqa: WPS433
    return JsonResponse({"ok": True, "comfy": comfyui_client.status(),
                         "loras": [_serialize(c, with_images=False) for c in qs]})


@login_required(login_url="gurps:login")
def charlora_detail(request, lora_id):
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    return JsonResponse({"ok": True, "lora": _serialize(cl)})


@login_required(login_url="gurps:login")
def charlora_create(request, campanha_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha, err = _gm_or_403(campanha_id, request)
    if err:
        return err
    body = request.POST if request.POST else (json.loads(request.body or "{}"))
    name = (body.get("name") or "").strip()[:120]
    if not name:
        return JsonResponse({"error": "dê um nome ao personagem"}, status=400)
    trigger = (body.get("trigger_word") or "").strip()[:40] or _trigger_from(name)
    cl = CharacterLora.objects.create(
        campanha=campanha, requested_by=request.user, name=name,
        trigger_word=trigger, description=(body.get("description") or "").strip()[:1500],
        n_poses=max(4, min(int(body.get("n_poses") or 16), 16)),
        train_steps=max(400, min(int(body.get("train_steps") or 1200), 4000)),
        status="draft")
    sid = body.get("seed_asset_id")
    if sid:
        cl.seed_asset = CampanhaAssets.objects.filter(id=sid, campanha=campanha).first()
        cl.save(update_fields=["seed_asset", "updated_at"])
    if not cl.trigger_word:
        cl.trigger_word = _trigger_from(name, cl.id); cl.save(update_fields=["trigger_word"])
    return JsonResponse({"ok": True, "lora": _serialize(cl)})


@login_required(login_url="gurps:login")
def charlora_update(request, lora_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    body = request.POST if request.POST else (json.loads(request.body or "{}"))
    fields = []
    if "name" in body:
        cl.name = (body.get("name") or cl.name).strip()[:120]; fields.append("name")
    if "description" in body:
        cl.description = (body.get("description") or "").strip()[:1500]; fields.append("description")
    if "trigger_word" in body:
        cl.trigger_word = (body.get("trigger_word") or "").strip()[:40] or cl.trigger_word
        fields.append("trigger_word")
    if "n_poses" in body:
        cl.n_poses = max(4, min(int(body.get("n_poses") or 16), 16)); fields.append("n_poses")
    if "train_steps" in body:
        cl.train_steps = max(400, min(int(body.get("train_steps") or 1200), 4000)); fields.append("train_steps")
    if "seed_asset_id" in body:
        sid = body.get("seed_asset_id")
        cl.seed_asset = (CampanhaAssets.objects.filter(id=sid, campanha=cl.campanha).first()
                         if sid else None)
        fields.append("seed_asset")
    if fields:
        cl.save(update_fields=fields + ["updated_at"])
    return JsonResponse({"ok": True, "lora": _serialize(cl)})


@login_required(login_url="gurps:login")
def charlora_seed_upload(request, lora_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    up = request.FILES.get("image") if request.FILES else None
    if up is None:
        return JsonResponse({"error": "nenhuma imagem"}, status=400)
    cl.seed_image = up
    cl.seed_asset = None
    cl.save(update_fields=["seed_image", "seed_asset", "updated_at"])
    return JsonResponse({"ok": True, "lora": _serialize(cl)})


@login_required(login_url="gurps:login")
def charlora_gen_dataset(request, lora_id):
    """Enfileira a geração da folha de poses (dataset)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    if not (cl.seed_asset_id or cl.seed_image):
        return JsonResponse({"error": "escolha uma imagem-semente primeiro"}, status=400)
    cl.status = "dataset_pending"; cl.error = ""; cl.progress = "na fila..."; cl.progress_pct = -1
    cl.save(update_fields=["status", "error", "progress", "progress_pct", "updated_at"])
    from gurps import comfyui_client  # noqa: WPS433
    return JsonResponse({"ok": True, "lora": _serialize(cl, with_images=False),
                         "comfy_online": comfyui_client.status().get("online", False)})


@login_required(login_url="gurps:login")
def charlora_image_toggle(request, image_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    im = get_object_or_404(CharacterLoraImage, id=image_id)
    if im.lora.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    im.keep = not im.keep
    im.save(update_fields=["keep"])
    return JsonResponse({"ok": True, "id": im.id, "keep": im.keep})


@login_required(login_url="gurps:login")
def charlora_image(request, image_id):
    im = get_object_or_404(CharacterLoraImage, id=image_id)
    if im.lora.campanha.dono_id != request.user.id:
        return HttpResponse(status=403)
    full = os.path.join(settings.MEDIA_ROOT, im.file.replace("/", os.sep))
    if not os.path.exists(full):
        return HttpResponse(status=404)
    resp = FileResponse(open(full, "rb"), content_type="image/png")
    resp["Cache-Control"] = "no-store"
    return resp


@login_required(login_url="gurps:login")
def charlora_train(request, lora_id):
    """Enfileira o treino do LoRA (precisa de dataset curado com >=4 imagens keep)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    if cl.images.filter(keep=True).count() < 4:
        return JsonResponse({"error": "mantenha ao menos 4 poses (keep) antes de treinar"}, status=400)
    cl.status = "train_pending"; cl.error = ""; cl.progress = "na fila de treino..."; cl.progress_pct = -1
    cl.save(update_fields=["status", "error", "progress", "progress_pct", "updated_at"])
    return JsonResponse({"ok": True, "lora": _serialize(cl, with_images=False)})


@login_required(login_url="gurps:login")
def charlora_delete(request, lora_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    cl = get_object_or_404(CharacterLora, id=lora_id)
    if cl.campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM"}, status=403)
    cl.delete()
    return JsonResponse({"ok": True})


@login_required(login_url="gurps:login")
def charlora_trained(request, campanha_id):
    """Lista só os LoRAs TREINADOS da campanha (pro seletor do Estúdio de Vídeo)."""
    campanha, err = _gm_or_403(campanha_id, request)
    if err:
        return err
    qs = CharacterLora.objects.filter(campanha=campanha, status="trained").order_by("name")
    return JsonResponse({"ok": True, "loras": [
        {"id": c.id, "name": c.name, "trigger_word": c.trigger_word} for c in qs]})
