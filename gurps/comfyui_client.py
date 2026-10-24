"""Cliente do ComfyUI local — motor de geração de imagem na GPU do host.

O ComfyUI roda como serviço local separado (não embutido no app) e expõe uma
API HTTP em http://127.0.0.1:8188. Aqui: detectar se está online (`status`) e
gerar uma imagem SDXL a partir de um prompt (`generate_png`). Sem dependências
externas — só stdlib (urllib/json).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_URL = "http://127.0.0.1:8188"
# Modelo fotorrealista (RealVisXL V5.0 Lightning). Substitui o sd_xl_turbo, que
# gerava um acabamento "liso de videogame". Lightning = rápido (4-6 passos) mas
# com realismo cinematográfico. Cai pro turbo se o arquivo não existir (ver worker).
DEFAULT_CKPT = "RealVisXL_V5.0_Lightning_fp16.safetensors"
FALLBACK_CKPT = "sd_xl_turbo_1.0_fp16.safetensors"
# Sampler/scheduler recomendados pro RealVisXL Lightning (DPM++ SDE Karras).
DEFAULT_SAMPLER = "dpmpp_sde"
DEFAULT_SCHEDULER = "karras"
# Negative prompt padrão: além dos defeitos, mata explicitamente o visual
# cartoon/anime/render que o usuário NÃO quer (quer foto realista escura).
DEFAULT_NEGATIVE = (
    "cartoon, anime, cel shaded, cgi, 3d render, octane render, video game, illustration, "
    "painting drawing sketch, cute, chibi, bright saturated colors, plastic skin, "
    "lowres, blurry, deformed, disfigured, bad anatomy, extra limbs, extra fingers, "
    "watermark, text, signature, jpeg artifacts, ugly, worst quality, low quality"
)


def status(base_url: str = DEFAULT_URL, timeout: float = 3.0) -> dict:
    """Pinga /system_stats. Retorna {online, url, device, vram_total_mb, error}."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/system_stats", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"online": False, "url": base_url, "error": str(exc)[:200]}
    devices = data.get("devices") or []
    dev = devices[0] if devices else {}
    vram = dev.get("vram_total")
    return {
        "online": True,
        "url": base_url,
        "device": dev.get("name"),
        "vram_total_mb": round(vram / (1024 * 1024)) if isinstance(vram, (int, float)) else None,
    }


def available_checkpoints(base_url: str = DEFAULT_URL, timeout: float = 5.0) -> list:
    """Lista os checkpoints que o ComfyUI enxerga (via /object_info)."""
    try:
        url = base_url.rstrip("/") + "/object_info/CheckpointLoaderSimple"
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        opts = data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        return list(opts)
    except Exception:  # noqa: BLE001
        return []


def pick_checkpoint(preferred: str = DEFAULT_CKPT, base_url: str = DEFAULT_URL) -> str:
    """Escolhe o melhor checkpoint disponível: o preferido (RealVisXL) se existir,
    senão o fallback (turbo), senão o primeiro que houver. Nunca falha."""
    avail = available_checkpoints(base_url)
    if not avail:
        return preferred  # ComfyUI offline/sem resposta — deixa o generate falhar claro
    if preferred in avail:
        return preferred
    if FALLBACK_CKPT in avail:
        return FALLBACK_CKPT
    return avail[0]


def free_memory(base_url: str = DEFAULT_URL, timeout: float = 10.0) -> bool:
    """Pede pro ComfyUI descarregar modelos e liberar VRAM (/free). Best-effort —
    ajuda a evitar OOM acumulado ao gerar muitos clipes / trocar de modelo."""
    try:
        payload = json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8")
        req = urllib.request.Request(base_url.rstrip("/") + "/free", data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:  # noqa: BLE001
        return False


def wait_online(base_url: str = DEFAULT_URL, timeout: float = 90.0,
                interval: float = 3.0) -> bool:
    """Espera o ComfyUI voltar a responder (ex. depois de um restart). True se subiu."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if status(base_url).get("online"):
            return True
        time.sleep(interval)
    return False


def _build_sdxl_graph(prompt, negative, width, height, steps, cfg, seed, ckpt,
                      sampler_name=DEFAULT_SAMPLER, scheduler=DEFAULT_SCHEDULER):
    """Grafo mínimo SDXL text2img no formato API do ComfyUI."""
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": int(width), "height": int(height), "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg),
                         "sampler_name": sampler_name, "scheduler": scheduler, "denoise": 1.0,
                         "model": ["4", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": "rpg_gen"}},
    }


# Modelos do IP-Adapter (transferência de estilo a partir de imagem de referência).
IPADAPTER_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION_MODEL = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"


def _build_sdxl_ipadapter_graph(prompt, negative, width, height, steps, cfg, seed,
                                ckpt, ref_image_name, ref_weight,
                                sampler_name=DEFAULT_SAMPLER, scheduler=DEFAULT_SCHEDULER,
                                ipadapter_model=IPADAPTER_MODEL,
                                clip_vision_model=CLIP_VISION_MODEL):
    """Igual ao grafo SDXL, mas insere IP-Adapter: a imagem de referência
    (já enviada pro ComfyUI via /upload/image) condiciona o modelo com o
    estilo/clima dela. O KSampler roda sobre o modelo já 'patchado'."""
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": int(width), "height": int(height), "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["4", 1]}},
        "10": {"class_type": "LoadImage",
               "inputs": {"image": ref_image_name}},
        "11": {"class_type": "IPAdapterModelLoader",
               "inputs": {"ipadapter_file": ipadapter_model}},
        "12": {"class_type": "CLIPVisionLoader",
               "inputs": {"clip_name": clip_vision_model}},
        "13": {"class_type": "IPAdapterAdvanced",
               "inputs": {"model": ["4", 0], "ipadapter": ["11", 0],
                          "image": ["10", 0], "clip_vision": ["12", 0],
                          "weight": float(ref_weight), "weight_type": "style transfer",
                          "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0,
                          "embeds_scaling": "V only"}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg),
                         "sampler_name": sampler_name, "scheduler": scheduler, "denoise": 1.0,
                         "model": ["13", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": "rpg_gen"}},
    }


def upload_image(image_bytes: bytes, filename: str, base_url: str = DEFAULT_URL,
                 timeout: float = 30.0) -> str:
    """Envia uma imagem pro ComfyUI (/upload/image) e devolve o nome com que ele
    a guardou (pra referenciar no nó LoadImage). Multipart montado na mão (stdlib)."""
    boundary = "----rpg" + uuid.uuid4().hex
    ctype = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode(),
        f"Content-Type: {ctype}\r\n\r\n".encode(),
        image_bytes, b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n',
        f"--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        base_url.rstrip("/") + "/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    name = data.get("name") or filename
    sub = data.get("subfolder") or ""
    return f"{sub}/{name}" if sub else name


def _http_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def generate_png(prompt, negative=None, width=768, height=1024, steps=6, cfg=1.5,
                 seed=None, ckpt=DEFAULT_CKPT, base_url=DEFAULT_URL,
                 sampler_name=DEFAULT_SAMPLER, scheduler=DEFAULT_SCHEDULER,
                 ref_image_bytes=None, ref_image_filename="ref.png", ref_weight=0.7,
                 timeout=240, poll_interval=1.5, on_beat=None) -> bytes:
    """Gera uma imagem e retorna os bytes do PNG. Lança RuntimeError em falha.

    Se ``ref_image_bytes`` for dado, usa IP-Adapter pra transferir o estilo/clima
    da imagem de referência pra geração.

    on_beat: callback opcional chamado a cada poll (pra manter heartbeat/log).
    """
    base = base_url.rstrip("/")
    if negative is None:
        negative = DEFAULT_NEGATIVE
    if seed is None:
        seed = uuid.uuid4().int % (2 ** 31)
    client_id = uuid.uuid4().hex
    if ref_image_bytes:
        ref_name = upload_image(ref_image_bytes, ref_image_filename, base_url=base)
        graph = _build_sdxl_ipadapter_graph(
            prompt, negative, width, height, steps, cfg, seed, ckpt,
            ref_name, ref_weight, sampler_name=sampler_name, scheduler=scheduler)
    else:
        graph = _build_sdxl_graph(prompt, negative, width, height, steps, cfg, seed, ckpt,
                                  sampler_name=sampler_name, scheduler=scheduler)

    # 1) enfileira o job
    try:
        resp = _http_json(base + "/prompt", {"prompt": graph, "client_id": client_id})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500] if hasattr(e, "read") else ""
        raise RuntimeError(f"ComfyUI recusou o job (HTTP {e.code}): {body}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Falha ao enviar job pro ComfyUI: {e}")
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI não retornou prompt_id: {resp}")

    # 2) poll /history/<id> até terminar
    start = time.monotonic()
    outputs = None
    while time.monotonic() - start < timeout:
        if on_beat:
            try:
                on_beat()
            except Exception:  # noqa: BLE001
                pass
        try:
            with urllib.request.urlopen(base + "/history/" + prompt_id, timeout=10) as r:
                hist = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            time.sleep(poll_interval)
            continue
        entry = hist.get(prompt_id)
        if entry:
            st = (entry.get("status") or {})
            if st.get("status_str") == "error":
                raise RuntimeError("ComfyUI reportou erro na execução do grafo.")
            outs = entry.get("outputs") or {}
            for node_out in outs.values():
                imgs = node_out.get("images") or []
                if imgs:
                    outputs = imgs[0]
                    break
            if outputs:
                break
        time.sleep(poll_interval)

    if not outputs:
        raise RuntimeError("Timeout esperando a imagem do ComfyUI.")

    # 3) baixa o PNG via /view
    qs = urllib.parse.urlencode({
        "filename": outputs.get("filename", ""),
        "subfolder": outputs.get("subfolder", ""),
        "type": outputs.get("type", "output"),
    })
    with urllib.request.urlopen(base + "/view?" + qs, timeout=30) as r:
        return r.read()


# ===================== VÍDEO (AnimateDiff na GPU do host) =====================
VIDEO_CKPT = "toonyou_beta6.safetensors"           # checkpoint anime SD1.5
VIDEO_MOTION = "AnimateLCM_sd15_t2v.ckpt"          # motion module (AnimateLCM)
VIDEO_LORA = "AnimateLCM_sd15_t2v_lora.safetensors"  # LCM lora (poucos passos)
VIDEO_NEGATIVE = ("bad quality, worst quality, low quality, blurry, deformed, disfigured, "
                  "bad anatomy, extra limbs, watermark, text, signature, jpeg artifacts")


def _build_animatediff_graph(prompt, negative, width, height, frames, fps, steps, cfg, seed,
                             ckpt=VIDEO_CKPT, motion=VIDEO_MOTION, lora=VIDEO_LORA,
                             lora_strength=0.8, context_length=16, context_overlap=4,
                             filename_prefix="rpg_clip"):
    """Grafo AnimateDiff (AnimateLCM) text2video → mp4 via VHS_VideoCombine.

    Janelas de contexto (context_length) permitem frames > 16 sem estourar VRAM."""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"model": ["4", 0], "lora_name": lora, "strength_model": lora_strength}},
        "11": {"class_type": "ADE_AnimateDiffUniformContextOptions",
               "inputs": {"context_length": int(context_length), "context_stride": 1,
                          "context_overlap": int(context_overlap), "context_schedule": "uniform",
                          "closed_loop": False}},
        "12": {"class_type": "ADE_AnimateDiffLoaderGen1",
               "inputs": {"model": ["10", 0], "model_name": motion,
                          "beta_schedule": "lcm", "context_options": ["11", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": int(width), "height": int(height), "batch_size": int(frames)}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg),
                         "sampler_name": "lcm", "scheduler": "sgm_uniform", "denoise": 1.0,
                         "model": ["12", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "VHS_VideoCombine",
              "inputs": {"images": ["8", 0], "frame_rate": int(fps), "loop_count": 0,
                         "filename_prefix": filename_prefix, "format": "video/h264-mp4",
                         "pingpong": False, "save_output": True}},
    }


def generate_clip_mp4(prompt, negative=None, seconds=4, fps=8, width=512, height=512,
                      steps=8, cfg=1.8, seed=None, base_url=DEFAULT_URL,
                      ckpt=VIDEO_CKPT, timeout=600, poll_interval=2.0, on_beat=None) -> bytes:
    """Gera UM clipe de vídeo (AnimateDiff) e retorna os bytes do mp4.

    frames = seconds*fps. Lança RuntimeError em falha."""
    base = base_url.rstrip("/")
    if negative is None:
        negative = VIDEO_NEGATIVE
    if seed is None:
        seed = uuid.uuid4().int % (2 ** 31)
    frames = max(8, min(int(round(seconds * fps)), 96))
    client_id = uuid.uuid4().hex
    graph = _build_animatediff_graph(prompt, negative, width, height, frames, fps,
                                     steps, cfg, seed, ckpt=ckpt)
    try:
        resp = _http_json(base + "/prompt", {"prompt": graph, "client_id": client_id})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500] if hasattr(e, "read") else ""
        raise RuntimeError(f"ComfyUI recusou o clipe (HTTP {e.code}): {body}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Falha ao enviar clipe pro ComfyUI: {e}")
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI não retornou prompt_id: {resp}")

    start = time.monotonic()
    out = None
    while time.monotonic() - start < timeout:
        if on_beat:
            try:
                on_beat()
            except Exception:  # noqa: BLE001
                pass
        try:
            with urllib.request.urlopen(base + "/history/" + prompt_id, timeout=10) as r:
                hist = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            time.sleep(poll_interval)
            continue
        entry = hist.get(prompt_id)
        if entry:
            st = (entry.get("status") or {})
            if st.get("status_str") == "error":
                raise RuntimeError("ComfyUI reportou erro ao gerar o clipe.")
            outs = entry.get("outputs") or {}
            for node_out in outs.values():
                vids = node_out.get("gifs") or node_out.get("videos") or []
                if vids:
                    out = vids[0]
                    break
            if out:
                break
        time.sleep(poll_interval)

    if not out:
        raise RuntimeError("Timeout esperando o clipe do ComfyUI.")
    qs = urllib.parse.urlencode({
        "filename": out.get("filename", ""), "subfolder": out.get("subfolder", ""),
        "type": out.get("type", "output"),
    })
    with urllib.request.urlopen(base + "/view?" + qs, timeout=120) as r:
        return r.read()


def video_pick_checkpoint(base_url: str = DEFAULT_URL) -> bool:
    """True se os modelos de vídeo (ToonYou + AnimateLCM) estão disponíveis."""
    avail = available_checkpoints(base_url)
    return VIDEO_CKPT in avail
