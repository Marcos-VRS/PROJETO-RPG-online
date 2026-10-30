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


def available_vaes(base_url: str = DEFAULT_URL, timeout: float = 5.0) -> list:
    """Lista as VAEs que o ComfyUI enxerga (via /object_info/VAELoader)."""
    try:
        url = base_url.rstrip("/") + "/object_info/VAELoader"
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        opts = data["VAELoader"]["input"]["required"]["vae_name"][0]
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
VIDEO_CKPT = "toonyou_beta6.safetensors"           # checkpoint anime SD1.5 (preset "anime")
# Preset "realismo": checkpoint SD1.5 FOTORREALISTA (Realistic Vision) + VAE SD1.5.
# O motion module (AnimateLCM) é SD1.5, então funciona com qualquer checkpoint SD1.5 —
# trocar o checkpoint é o que muda a ARTE (anime -> foto). RealVisXL NÃO serve: é SDXL.
VIDEO_CKPT_REALISM = "realisticVision_v51.safetensors"
VIDEO_VAE_REALISM = "vae-ft-mse-840000-ema-pruned.safetensors"  # VAE SD1.5 (cor não "lavada")
VIDEO_MOTION = "AnimateLCM_sd15_t2v.ckpt"          # motion module (AnimateLCM)
VIDEO_LORA = "AnimateLCM_sd15_t2v_lora.safetensors"  # LCM lora (poucos passos)
VIDEO_NEGATIVE = ("bad quality, worst quality, low quality, blurry, deformed, distorted, "
                  "disfigured, mutated, malformed, bad anatomy, bad proportions, extra limbs, "
                  "extra fingers, missing limbs, fused fingers, extra faces, duplicate, "
                  "inconsistent, morphing, watermark, text, signature, jpeg artifacts")
# Reforços do preset "realismo": empurra o resultado pra FOTO e longe de desenho/boneco.
VIDEO_REALISM_POSITIVE = ("photorealistic, realistic, photograph, hyperrealism, highly detailed, "
                          "natural skin texture, cinematic lighting, sharp focus, depth of field, "
                          "shot on film, 8k, raw photo")
VIDEO_REALISM_NEGATIVE = ("anime, cartoon, 3d render, cgi, illustration, painting, drawing, "
                          "sketch, doll, toy, plastic, figurine, cel shading, flat shading, "
                          "stylized, videogame")


def video_style_models(style: str, base_url: str = DEFAULT_URL) -> tuple:
    """(ckpt, vae) pro estilo de render do vídeo.

    - "realism" -> Realistic Vision (SD1.5) + VAE SD1.5, SE o modelo existir;
      senão cai graciosamente pro anime (ToonYou), que todo mundo tem.
    - qualquer outro -> ToonYou (anime), sem VAE explícita (usa a do checkpoint).
    """
    if (style or "").lower() == "realism":
        avail = available_checkpoints(base_url)
        if VIDEO_CKPT_REALISM in avail:
            vae = VIDEO_VAE_REALISM if VIDEO_VAE_REALISM in available_vaes(base_url) else None
            return VIDEO_CKPT_REALISM, vae
    return VIDEO_CKPT, None
# Modo Consistência (sempre ligado): 1 clipe = 1 janela de contexto (sem deriva de rosto),
# mais passos de amostragem, FreeInit e IP-Adapter forte. Custo: clipes bem mais lentos.
VIDEO_CONTEXT_LENGTH = 16          # frames por janela do AnimateDiff
VIDEO_MAX_CLIP_SECONDS = 2         # 16 frames @ 8 fps = 1 única janela
# Beat contínuo: o AnimateDiff gera o beat inteiro de uma vez usando a janela
# DESLIZANTE (overlap entre janelas = continuidade; mantém a roupa/aparência).
# Teto de frames por geração pra caber nos 6GB e não demorar demais.
VIDEO_BEAT_MAX_FRAMES = 48         # 6s @ 8 fps
VIDEO_MIN_STEPS = 14
VIDEO_REF_WEIGHT = 0.85
VIDEO_FREEINIT_ITERATIONS = 2
# IP-Adapter SD1.5 (pra o vídeo usar a aparência dos retratos do journal).
VIDEO_IPADAPTER = "ip-adapter-plus_sd15.safetensors"
# CLIP vision reusa o ViT-H (CLIP_VISION_MODEL, já definido lá em cima).

# ---- SVD (Stable Video Diffusion): modo "Dar vida (fiel)" ----
# Ao contrário do AnimateDiff, o SVD usa a PRÓPRIA imagem como quadro 1 de verdade
# e anima a partir dela (movimento de câmera/ambiente). NÃO obedece texto — é o
# motor pra quando a imagem JÁ está do jeito da cena. Validado na RTX 1000 Ada 6GB
# com --lowvram: 14 frames a 576x768 ~130s, sem OOM.
VIDEO_SVD_CKPT = "svd-fp16.safetensors"   # modelo SVD fp16 (14 frames), em models/checkpoints
VIDEO_SVD_FRAMES = 14                      # o SVD base gera 14 frames
VIDEO_SVD_FPS = 7                          # fps nativo de condicionamento do SVD
VIDEO_SVD_STEPS = 20
VIDEO_SVD_MIN_CFG = 1.0
VIDEO_SVD_CFG = 2.5
# Caixa de resolução segura pros 6GB (mantém a proporção da imagem, múltiplo de 64).
VIDEO_SVD_MAX_W = 768
VIDEO_SVD_MAX_H = 768


def svd_available(base_url: str = DEFAULT_URL) -> bool:
    """True se o modelo do SVD estiver instalado no ComfyUI (models/checkpoints)."""
    return VIDEO_SVD_CKPT in available_checkpoints(base_url)


def svd_dims_for(img_w: int, img_h: int) -> tuple:
    """(W, H) múltiplos de 64 que mantêm a proporção da imagem dentro da caixa
    segura dos 6GB. Protege contra OOM sem distorcer (nada de forçar quadrado)."""
    img_w = max(1, int(img_w or 1))
    img_h = max(1, int(img_h or 1))
    scale = min(VIDEO_SVD_MAX_W / img_w, VIDEO_SVD_MAX_H / img_h, 1.0)
    w = max(64, int(round(img_w * scale / 64)) * 64)
    h = max(64, int(round(img_h * scale / 64)) * 64)
    return w, h


# ---- Wan 2.2 TI2V-5B: modo "Ação dirigida" (imagem + TEXTO -> vídeo) ----
# Diferente do SVD (que ignora texto) e do img2vid (que repinta e erra o
# personagem), o Wan pega a imagem como quadro 1 E OBEDECE o prompt de ação,
# mantendo o personagem. É o motor pra "ele leva a mão ao rosto com magia".
# Validado na RTX 1000 Ada 6GB (--lowvram + 63GB RAM): 480x640, 49 frames,
# 20 passos ~25min. Lento, mas FAZ a ação mantendo a aparência.
VIDEO_WAN_UNET = "wan2.2_ti2v_5B_fp16.safetensors"       # models/diffusion_models
VIDEO_WAN_CLIP = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"  # models/text_encoders
VIDEO_WAN_VAE = "wan2.2_vae.safetensors"                 # models/vae
VIDEO_WAN_FPS = 24                 # fps nativo do Wan 5B
VIDEO_WAN_LENGTH = 49              # 49 frames ~2s @ 24fps (teto seguro p/ 6GB)
VIDEO_WAN_STEPS = 20
VIDEO_WAN_CFG = 5.0
VIDEO_WAN_SHIFT = 8.0              # ModelSamplingSD3 shift (recomendado p/ Wan)
VIDEO_WAN_MAX_W = 640             # caixa segura p/ 6GB (lado maior)
VIDEO_WAN_MAX_H = 640
VIDEO_WAN_NEGATIVE = ("blurry, low quality, distorted, deformed face, extra limbs, "
                      "extra fingers, morphing, flicker, cartoon, anime, text, watermark, "
                      "static, still image, worst quality, jpeg artifacts")


def wan_available(base_url: str = DEFAULT_URL) -> bool:
    """True se o conjunto do Wan (modelo + text encoder + VAE) está instalado."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/object_info/UNETLoader", timeout=8) as r:
            unet = json.loads(r.read())["UNETLoader"]["input"]["required"]["unet_name"][0]
        with urllib.request.urlopen(base_url.rstrip("/") + "/object_info/CLIPLoader", timeout=8) as r:
            clip = json.loads(r.read())["CLIPLoader"]["input"]["required"]["clip_name"][0]
    except Exception:  # noqa: BLE001
        return False
    return (VIDEO_WAN_UNET in unet and VIDEO_WAN_CLIP in clip
            and VIDEO_WAN_VAE in available_vaes(base_url))


def wan_dims_for(img_w: int, img_h: int) -> tuple:
    """(W, H) múltiplos de 16 que mantêm a proporção da imagem dentro da caixa
    segura dos 6GB pro Wan (lado maior <= 640). Evita OOM sem distorcer."""
    img_w = max(1, int(img_w or 1))
    img_h = max(1, int(img_h or 1))
    scale = min(VIDEO_WAN_MAX_W / img_w, VIDEO_WAN_MAX_H / img_h, 1.0)
    w = max(16, int(round(img_w * scale / 16)) * 16)
    h = max(16, int(round(img_h * scale / 16)) * 16)
    return w, h


def _node_defaults(base, class_type):
    """Lê /object_info/<node> e devolve {input: default} dos inputs obrigatórios,
    ou None se o nó não existir (custom node ausente/versão antiga)."""
    try:
        with urllib.request.urlopen(f"{base}/object_info/{class_type}", timeout=10) as r:
            info = json.loads(r.read().decode("utf-8")).get(class_type)
    except Exception:  # noqa: BLE001
        return None
    if not info:
        return None
    out = {}
    for name, spec in (info.get("input", {}).get("required") or {}).items():
        kind, opts = spec[0], (spec[1] if len(spec) > 1 else {})
        if isinstance(kind, list):
            out[name] = kind[0]
        elif isinstance(opts, dict) and "default" in opts:
            out[name] = opts["default"]
        else:
            return None
    return out


def _freeinit_nodes(base, iterations=VIDEO_FREEINIT_ITERATIONS):
    """Nós do FreeInit (AnimateDiff-Evolved) prontos pra mesclar no grafo, e o id
    do nó de sample settings. ({}, None) se o ComfyUI não tiver os nós — aí o clipe
    sai sem FreeInit em vez de falhar."""
    fi = _node_defaults(base, "ADE_IterationOptsFreeInit")
    ss = _node_defaults(base, "ADE_AnimateDiffSamplingSettings")
    if fi is None or ss is None:
        return {}, None
    fi["iterations"] = int(iterations)
    return {
        "30": {"class_type": "ADE_IterationOptsFreeInit", "inputs": fi},
        "31": {"class_type": "ADE_AnimateDiffSamplingSettings",
               "inputs": {**ss, "iteration_opts": ["30", 0]}},
    }, "31"


def _build_animatediff_ipadapter_graph(prompt, negative, width, height, frames, fps, steps,
                                       cfg, seed, ref_image_name, ref_weight=0.75,
                                       ckpt=VIDEO_CKPT, motion=VIDEO_MOTION, lora=VIDEO_LORA,
                                       lora_strength=0.8, context_length=16, context_overlap=4,
                                       filename_prefix="rpg_clip", freeinit=None, vae=None):
    """Igual ao grafo AnimateDiff, mas com IP-Adapter: a cena nova sai com a
    APARÊNCIA do retrato de referência (imagem do journal já enviada ao ComfyUI).
    O IP-Adapter patcha o modelo ANTES do AnimateDiff."""
    vae_ref = ["40", 0] if vae else ["4", 2]
    graph = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"model": ["4", 0], "lora_name": lora, "strength_model": lora_strength}},
        "20": {"class_type": "LoadImage", "inputs": {"image": ref_image_name}},
        "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": VIDEO_IPADAPTER}},
        "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": CLIP_VISION_MODEL}},
        "23": {"class_type": "IPAdapterAdvanced",
               "inputs": {"model": ["10", 0], "ipadapter": ["21", 0], "image": ["20", 0],
                          "clip_vision": ["22", 0], "weight": float(ref_weight),
                          "weight_type": "linear", "combine_embeds": "concat",
                          "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
        "11": {"class_type": "ADE_AnimateDiffUniformContextOptions",
               "inputs": {"context_length": int(context_length), "context_stride": 1,
                          "context_overlap": int(context_overlap), "context_schedule": "uniform",
                          "closed_loop": False}},
        "12": {"class_type": "ADE_AnimateDiffLoaderGen1",
               "inputs": {"model": ["23", 0], "model_name": motion,
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
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": vae_ref}},
        "9": {"class_type": "VHS_VideoCombine",
              "inputs": {"images": ["8", 0], "frame_rate": int(fps), "loop_count": 0,
                         "filename_prefix": filename_prefix, "format": "video/h264-mp4",
                         "pingpong": False, "save_output": True}},
    }
    if vae:
        graph["40"] = {"class_type": "VAELoader", "inputs": {"vae_name": vae}}
    if freeinit:
        nodes, ss_id = freeinit
        if nodes:
            graph.update(nodes)
            graph["12"]["inputs"]["sample_settings"] = [ss_id, 0]
    return graph


def _build_animatediff_init_graph(prompt, negative, width, height, frames, fps, steps, cfg,
                                  seed, image_name, denoise=0.6,
                                  ckpt=VIDEO_CKPT, motion=VIDEO_MOTION, lora=VIDEO_LORA,
                                  lora_strength=0.8, context_length=16, context_overlap=4,
                                  filename_prefix="rpg_clip", freeinit=None, vae=None):
    """img2vid: ANIMA a própria imagem. A imagem vira o latente inicial (VAEEncode
    repetido em todos os frames) e o KSampler só adiciona movimento com
    ``denoise`` < 1 — quanto menor, mais fiel à imagem. Sem IP-Adapter: a
    fidelidade vem do latente inicial, não de 'inventar no estilo'."""
    vae_ref = ["40", 0] if vae else ["4", 2]
    graph = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"model": ["4", 0], "lora_name": lora, "strength_model": lora_strength}},
        "20": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "24": {"class_type": "ImageScale",
               "inputs": {"image": ["20", 0], "upscale_method": "lanczos",
                          "width": int(width), "height": int(height), "crop": "center"}},
        "25": {"class_type": "VAEEncode", "inputs": {"pixels": ["24", 0], "vae": vae_ref}},
        "26": {"class_type": "RepeatLatentBatch",
               "inputs": {"samples": ["25", 0], "amount": int(frames)}},
        "11": {"class_type": "ADE_AnimateDiffUniformContextOptions",
               "inputs": {"context_length": int(context_length), "context_stride": 1,
                          "context_overlap": int(context_overlap), "context_schedule": "uniform",
                          "closed_loop": False}},
        "12": {"class_type": "ADE_AnimateDiffLoaderGen1",
               "inputs": {"model": ["10", 0], "model_name": motion,
                          "beta_schedule": "lcm", "context_options": ["11", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg),
                         "sampler_name": "lcm", "scheduler": "sgm_uniform",
                         "denoise": float(denoise),
                         "model": ["12", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["26", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": vae_ref}},
        "9": {"class_type": "VHS_VideoCombine",
              "inputs": {"images": ["8", 0], "frame_rate": int(fps), "loop_count": 0,
                         "filename_prefix": filename_prefix, "format": "video/h264-mp4",
                         "pingpong": False, "save_output": True}},
    }
    if vae:
        graph["40"] = {"class_type": "VAELoader", "inputs": {"vae_name": vae}}
    if freeinit:
        nodes, ss_id = freeinit
        if nodes:
            graph.update(nodes)
            graph["12"]["inputs"]["sample_settings"] = [ss_id, 0]
    return graph


def _build_animatediff_graph(prompt, negative, width, height, frames, fps, steps, cfg, seed,
                             ckpt=VIDEO_CKPT, motion=VIDEO_MOTION, lora=VIDEO_LORA,
                             lora_strength=0.8, context_length=16, context_overlap=4,
                             filename_prefix="rpg_clip", freeinit=None, vae=None):
    """Grafo AnimateDiff (AnimateLCM) text2video → mp4 via VHS_VideoCombine.

    Janelas de contexto (context_length) permitem frames > 16 sem estourar VRAM."""
    vae_ref = ["40", 0] if vae else ["4", 2]
    graph = {
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
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": vae_ref}},
        "9": {"class_type": "VHS_VideoCombine",
              "inputs": {"images": ["8", 0], "frame_rate": int(fps), "loop_count": 0,
                         "filename_prefix": filename_prefix, "format": "video/h264-mp4",
                         "pingpong": False, "save_output": True}},
    }
    if vae:
        graph["40"] = {"class_type": "VAELoader", "inputs": {"vae_name": vae}}
    if freeinit:
        nodes, ss_id = freeinit
        if nodes:
            graph.update(nodes)
            graph["12"]["inputs"]["sample_settings"] = [ss_id, 0]
    return graph


def _start_progress_ws(base, client_id, on_progress):
    """Abre um WebSocket no ComfyUI e repassa o progresso REAL da amostragem
    (evento 'progress' = passo atual/total) via ``on_progress(frac)`` (0..1).
    Roda numa thread daemon; se a lib/conexão falhar, simplesmente não atualiza
    (a geração continua normal, só sem %). Retorna (stop_event, thread) ou (None, None)."""
    try:
        import threading  # noqa: WPS433
        import websocket  # websocket-client  # noqa: WPS433
    except Exception:  # noqa: BLE001
        return None, None
    ws_url = (base.replace("https://", "wss://").replace("http://", "ws://")
              + "/ws?clientId=" + client_id)
    stop = threading.Event()

    def _run():
        try:
            ws = websocket.create_connection(ws_url, timeout=5)
        except Exception:  # noqa: BLE001
            return
        try:
            while not stop.is_set():
                try:
                    ws.settimeout(1.0)
                    msg = ws.recv()
                except Exception:  # noqa: BLE001
                    continue
                if not msg or isinstance(msg, (bytes, bytearray)):
                    continue
                try:
                    data = json.loads(msg)
                except Exception:  # noqa: BLE001
                    continue
                if data.get("type") == "progress":
                    d = data.get("data") or {}
                    mx = d.get("max") or 0
                    if mx:
                        try:
                            on_progress(min(1.0, (d.get("value") or 0) / mx))
                        except Exception:  # noqa: BLE001
                            pass
        finally:
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return stop, t


def generate_clip_mp4(prompt, negative=None, seconds=4, fps=8, width=512, height=512,
                      steps=VIDEO_MIN_STEPS, cfg=1.8, seed=None, base_url=DEFAULT_URL,
                      ckpt=VIDEO_CKPT, ref_image_bytes=None, ref_image_filename="ref.png",
                      ref_weight=VIDEO_REF_WEIGHT, freeinit=True, timeout=600, poll_interval=2.0,
                      on_beat=None, max_frames=VIDEO_CONTEXT_LENGTH,
                      animate=False, denoise=0.6, vae=None, on_progress=None) -> bytes:
    """Gera UM clipe de vídeo (AnimateDiff) e retorna os bytes do mp4.

    Se ``ref_image_bytes`` vier, usa IP-Adapter: a cena sai com a aparência do
    retrato (imagem do journal). frames = seconds*fps, limitado a ``max_frames``.
    Com max_frames > VIDEO_CONTEXT_LENGTH o AnimateDiff usa a janela DESLIZANTE
    (overlap = continuidade, mantém a aparência ao longo do beat). Lança
    RuntimeError em falha."""
    base = base_url.rstrip("/")
    if negative is None:
        negative = VIDEO_NEGATIVE
    if seed is None:
        seed = uuid.uuid4().int % (2 ** 31)
    steps = max(int(steps), VIDEO_MIN_STEPS)
    frames = max(8, min(int(round(seconds * fps)), int(max_frames)))
    fi = _freeinit_nodes(base) if freeinit else None
    client_id = uuid.uuid4().hex
    # Progresso REAL via WebSocket (passo/total da amostragem). Começa ANTES de
    # enviar o prompt pra não perder os primeiros eventos. Opcional e tolerante.
    prog_stop, prog_thread = (None, None)
    if on_progress:
        prog_stop, prog_thread = _start_progress_ws(base, client_id, on_progress)
    if ref_image_bytes and animate:
        # img2vid: anima a PRÓPRIA imagem (fiel), controlado por denoise.
        ref_name = upload_image(ref_image_bytes, ref_image_filename, base_url=base)
        graph = _build_animatediff_init_graph(
            prompt, negative, width, height, frames, fps, steps, cfg, seed,
            ref_name, denoise=denoise, ckpt=ckpt, freeinit=fi, vae=vae)
    elif ref_image_bytes:
        ref_name = upload_image(ref_image_bytes, ref_image_filename, base_url=base)
        graph = _build_animatediff_ipadapter_graph(
            prompt, negative, width, height, frames, fps, steps, cfg, seed,
            ref_name, ref_weight=ref_weight, ckpt=ckpt, freeinit=fi, vae=vae)
    else:
        graph = _build_animatediff_graph(prompt, negative, width, height, frames, fps,
                                         steps, cfg, seed, ckpt=ckpt, freeinit=fi, vae=vae)
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
    try:
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
    finally:
        if prog_stop is not None:
            prog_stop.set()

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


def _build_svd_graph(image_name, width, height, frames, fps, motion_bucket,
                     augmentation, steps, min_cfg, cfg, seed):
    """Grafo SVD: a imagem é o quadro 1 de verdade; o modelo anima a partir dela.
    ImageOnlyCheckpointLoader -> (SVD_img2vid_Conditioning) -> VideoLinearCFGGuidance
    -> KSampler -> VAEDecode -> VHS_VideoCombine(mp4). Validado na 6GB com lowvram."""
    return {
        "loader": {"class_type": "ImageOnlyCheckpointLoader",
                   "inputs": {"ckpt_name": VIDEO_SVD_CKPT}},
        "img": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "scale": {"class_type": "ImageScale",
                  "inputs": {"image": ["img", 0], "upscale_method": "lanczos",
                             "width": width, "height": height, "crop": "center"}},
        "cond": {"class_type": "SVD_img2vid_Conditioning",
                 "inputs": {"clip_vision": ["loader", 1], "init_image": ["scale", 0],
                            "vae": ["loader", 2], "width": width, "height": height,
                            "video_frames": frames, "motion_bucket_id": motion_bucket,
                            "fps": fps, "augmentation_level": augmentation}},
        "guide": {"class_type": "VideoLinearCFGGuidance",
                  "inputs": {"model": ["loader", 0], "min_cfg": min_cfg}},
        "ks": {"class_type": "KSampler",
               "inputs": {"model": ["guide", 0], "positive": ["cond", 0],
                          "negative": ["cond", 1], "latent_image": ["cond", 2],
                          "seed": seed, "steps": steps, "cfg": cfg,
                          "sampler_name": "euler", "scheduler": "karras", "denoise": 1.0}},
        "vaed": {"class_type": "VAEDecode",
                 "inputs": {"samples": ["ks", 0], "vae": ["loader", 2]}},
        "out": {"class_type": "VHS_VideoCombine",
                "inputs": {"images": ["vaed", 0], "frame_rate": fps, "loop_count": 0,
                           "filename_prefix": "svd_beat", "format": "video/h264-mp4",
                           "pingpong": False, "save_output": True}},
    }


def generate_svd_mp4(ref_image_bytes, ref_image_filename="ref.png", width=576, height=768,
                     motion=0.5, base_url=DEFAULT_URL, timeout=1200, poll_interval=2.0,
                     on_progress=None, seed=None) -> bytes:
    """Gera UM clipe SVD (modo FIEL) a partir da imagem e retorna os bytes do mp4.

    ``motion`` é 0..1 (0 = movimento sutil, 1 = bastante) e vira o motion_bucket_id.
    width/height já devem vir múltiplos de 64 e dentro da caixa segura dos 6GB
    (use ``svd_dims_for``). Não usa prompt — o SVD ignora texto. Lança RuntimeError
    em falha. Retorna um clipe curto (VIDEO_SVD_FRAMES frames @ VIDEO_SVD_FPS)."""
    base = base_url.rstrip("/")
    if seed is None:
        seed = uuid.uuid4().int % (2 ** 31)
    motion = min(1.0, max(0.0, float(motion if motion is not None else 0.5)))
    motion_bucket = int(round(40 + motion * 140))   # 40 (sutil) .. 180 (muito)
    client_id = uuid.uuid4().hex
    prog_stop, prog_thread = (None, None)
    if on_progress:
        prog_stop, prog_thread = _start_progress_ws(base, client_id, on_progress)
    ref_name = upload_image(ref_image_bytes, ref_image_filename, base_url=base)
    graph = _build_svd_graph(ref_name, int(width), int(height), VIDEO_SVD_FRAMES,
                             VIDEO_SVD_FPS, motion_bucket, 0.0, VIDEO_SVD_STEPS,
                             VIDEO_SVD_MIN_CFG, VIDEO_SVD_CFG, seed)
    try:
        resp = _http_json(base + "/prompt", {"prompt": graph, "client_id": client_id})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500] if hasattr(e, "read") else ""
        raise RuntimeError(f"ComfyUI recusou o SVD (HTTP {e.code}): {body}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Falha ao enviar SVD pro ComfyUI: {e}")
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI não retornou prompt_id (SVD): {resp}")

    start = time.monotonic()
    out = None
    try:
        while time.monotonic() - start < timeout:
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
                    raise RuntimeError("ComfyUI reportou erro ao gerar o SVD (possível OOM).")
                for node_out in (entry.get("outputs") or {}).values():
                    vids = node_out.get("gifs") or node_out.get("videos") or []
                    if vids:
                        out = vids[0]
                        break
                if out:
                    break
            time.sleep(poll_interval)
    finally:
        if prog_stop is not None:
            prog_stop.set()

    if not out:
        raise RuntimeError("Timeout esperando o clipe SVD do ComfyUI.")
    qs = urllib.parse.urlencode({
        "filename": out.get("filename", ""), "subfolder": out.get("subfolder", ""),
        "type": out.get("type", "output"),
    })
    with urllib.request.urlopen(base + "/view?" + qs, timeout=120) as r:
        return r.read()


def _build_wan_graph(image_name, prompt, negative, width, height, length, steps,
                     cfg, shift, seed, fps):
    """Grafo Wan 2.2 TI2V-5B: imagem (quadro 1) + TEXTO -> vídeo com a ação pedida,
    mantendo o personagem. UNETLoader(fp8)->ModelSamplingSD3->KSampler; CLIPLoader
    (umt5, type wan)->2x encode; Wan22ImageToVideoLatent encaixa a imagem."""
    return {
        "unet": {"class_type": "UNETLoader",
                 "inputs": {"unet_name": VIDEO_WAN_UNET, "weight_dtype": "fp8_e4m3fn"}},
        "shift": {"class_type": "ModelSamplingSD3",
                  "inputs": {"model": ["unet", 0], "shift": shift}},
        "clip": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": VIDEO_WAN_CLIP, "type": "wan"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_WAN_VAE}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["clip", 0]}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["clip", 0]}},
        "img": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "scale": {"class_type": "ImageScale",
                  "inputs": {"image": ["img", 0], "upscale_method": "lanczos",
                             "width": width, "height": height, "crop": "center"}},
        "lat": {"class_type": "Wan22ImageToVideoLatent",
                "inputs": {"vae": ["vae", 0], "width": width, "height": height,
                           "length": length, "batch_size": 1, "start_image": ["scale", 0]}},
        "ks": {"class_type": "KSampler",
               "inputs": {"model": ["shift", 0], "positive": ["pos", 0],
                          "negative": ["neg", 0], "latent_image": ["lat", 0],
                          "seed": seed, "steps": steps, "cfg": cfg,
                          "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0}},
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
        "out": {"class_type": "VHS_VideoCombine",
                "inputs": {"images": ["dec", 0], "frame_rate": fps, "loop_count": 0,
                           "filename_prefix": "wan_beat", "format": "video/h264-mp4",
                           "pingpong": False, "save_output": True}},
    }


def generate_wan_mp4(ref_image_bytes, prompt, ref_image_filename="ref.png", negative=None,
                     width=480, height=640, length=VIDEO_WAN_LENGTH, steps=VIDEO_WAN_STEPS,
                     cfg=VIDEO_WAN_CFG, base_url=DEFAULT_URL, timeout=3600, poll_interval=3.0,
                     on_progress=None, seed=None) -> bytes:
    """Gera UM clipe Wan (modo AÇÃO DIRIGIDA) e retorna os bytes do mp4.

    ``prompt`` descreve a cena + a AÇÃO (em inglês, de preferência). A imagem é o
    quadro 1; o Wan obedece o texto mantendo o personagem. LENTO (~min no 6GB).
    width/height já devem vir múltiplos de 16 (use ``wan_dims_for``)."""
    base = base_url.rstrip("/")
    if negative is None:
        negative = VIDEO_WAN_NEGATIVE
    if seed is None:
        seed = uuid.uuid4().int % (2 ** 31)
    client_id = uuid.uuid4().hex
    prog_stop, prog_thread = (None, None)
    if on_progress:
        prog_stop, prog_thread = _start_progress_ws(base, client_id, on_progress)
    ref_name = upload_image(ref_image_bytes, ref_image_filename, base_url=base)
    graph = _build_wan_graph(ref_name, prompt, negative, int(width), int(height),
                             int(length), int(steps), cfg, VIDEO_WAN_SHIFT, seed,
                             VIDEO_WAN_FPS)
    try:
        resp = _http_json(base + "/prompt", {"prompt": graph, "client_id": client_id})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500] if hasattr(e, "read") else ""
        raise RuntimeError(f"ComfyUI recusou o Wan (HTTP {e.code}): {body}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Falha ao enviar Wan pro ComfyUI: {e}")
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI não retornou prompt_id (Wan): {resp}")

    start = time.monotonic()
    out = None
    try:
        while time.monotonic() - start < timeout:
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
                    raise RuntimeError("ComfyUI reportou erro ao gerar o Wan (possível OOM).")
                for node_out in (entry.get("outputs") or {}).values():
                    vids = node_out.get("gifs") or node_out.get("videos") or []
                    if vids:
                        out = vids[0]
                        break
                if out:
                    break
            time.sleep(poll_interval)
    finally:
        if prog_stop is not None:
            prog_stop.set()

    if not out:
        raise RuntimeError("Timeout esperando o clipe Wan do ComfyUI.")
    qs = urllib.parse.urlencode({
        "filename": out.get("filename", ""), "subfolder": out.get("subfolder", ""),
        "type": out.get("type", "output"),
    })
    with urllib.request.urlopen(base + "/view?" + qs, timeout=180) as r:
        return r.read()
