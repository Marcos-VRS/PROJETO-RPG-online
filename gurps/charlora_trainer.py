"""Fonte do treinador de LoRA SD1.5 (diffusers+peft) como STRING.

O treino roda no python do ComfyUI (python_embeded, que tem torch+cuda), não no
python do app. Como o app é empacotado (PyInstaller), o .py do trainer não existe
como arquivo acessível ao interpretador de fora; então guardamos a fonte aqui como
string e o worker a MATERIALIZA em disco (<home>/charlora/train_sd15_lora.py) e
roda com o python embutido. Mantido sem triple-quotes internas de propósito.

O script emite linhas "PROGRESS <pct>" e "STATUS <texto>" no stdout pro worker
parsear o progresso, e "DONE <arquivo>" ou "ERROR <msg>" no fim.
"""

# Pacotes que o treino exige no python do ComfyUI (torch já vem com o ComfyUI).
TRAIN_DEPS = ["diffusers", "accelerate", "peft"]

TRAINER_SOURCE = r'''
import argparse, os, sys, glob, random, traceback

def log(msg):
    sys.stdout.write(str(msg) + "\n"); sys.stdout.flush()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--steps", type=int, default=1200)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--resolution", type=int, default=512)
    a = ap.parse_args()

    import torch
    from PIL import Image
    import torchvision.transforms as T
    from diffusers import StableDiffusionPipeline, DDPMScheduler
    from peft import LoraConfig, get_peft_model, get_peft_model_state_dict

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        log("ERROR sem CUDA no python do ComfyUI")
        return 2
    dtype = torch.float16

    log("STATUS carregando o checkpoint SD1.5...")
    pipe = StableDiffusionPipeline.from_single_file(a.ckpt, torch_dtype=dtype, safety_checker=None)
    unet = pipe.unet.to(device, dtype=dtype)
    vae = pipe.vae.to(device, dtype=dtype)
    text_encoder = pipe.text_encoder.to(device, dtype=dtype)
    tokenizer = pipe.tokenizer
    noise_scheduler = DDPMScheduler.from_config(pipe.scheduler.config)
    vae.requires_grad_(False); text_encoder.requires_grad_(False); unet.requires_grad_(False)
    vae.eval(); text_encoder.eval()

    # LoRA só no UNet (atenção). Treina pouquíssimos parâmetros -> cabe em 6GB.
    cfg = LoraConfig(r=a.rank, lora_alpha=a.rank,
                     target_modules=["to_q", "to_k", "to_v", "to_out.0"],
                     lora_dropout=0.0, bias="none")
    unet = get_peft_model(unet, cfg)
    unet.train()
    try:
        unet.enable_gradient_checkpointing()
    except Exception:
        pass
    # parâmetros treináveis em fp32 pra estabilidade
    params = [p for p in unet.parameters() if p.requires_grad]
    for p in params:
        p.data = p.data.float()
    log("STATUS parametros treinaveis: " + str(sum(p.numel() for p in params)))

    # dataset: imagens + legenda .txt de mesmo nome
    exts = ("*.png", "*.jpg", "*.jpeg", "*.webp")
    files = []
    for e in exts:
        files += glob.glob(os.path.join(a.data, e))
    files = sorted(files)
    if not files:
        log("ERROR dataset vazio em " + a.data)
        return 2
    def caption_for(fp):
        base = os.path.splitext(fp)[0] + ".txt"
        if os.path.exists(base):
            try:
                return open(base, "r", encoding="utf-8").read().strip()
            except Exception:
                return ""
        return ""
    tf = T.Compose([
        T.Resize(a.resolution), T.CenterCrop(a.resolution),
        T.ToTensor(), T.Normalize([0.5], [0.5]),
    ])
    log("STATUS dataset: " + str(len(files)) + " imagens")

    opt = torch.optim.AdamW(params, lr=a.lr)
    scaler = torch.cuda.amp.GradScaler()
    sf = getattr(vae.config, "scaling_factor", 0.18215)

    step = 0
    last_pct = -1
    while step < a.steps:
        fp = random.choice(files)
        try:
            img = Image.open(fp).convert("RGB")
        except Exception:
            step += 1; continue
        px = tf(img).unsqueeze(0).to(device, dtype=dtype)
        cap = caption_for(fp)
        with torch.no_grad():
            latents = vae.encode(px).latent_dist.sample() * sf
            tok = tokenizer(cap, padding="max_length", truncation=True,
                            max_length=tokenizer.model_max_length, return_tensors="pt")
            enc = text_encoder(tok.input_ids.to(device))[0]
        noise = torch.randn_like(latents)
        ts = torch.randint(0, noise_scheduler.config.num_train_timesteps, (1,), device=device).long()
        noisy = noise_scheduler.add_noise(latents, noise, ts)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            pred = unet(noisy, ts, encoder_hidden_states=enc).sample
            target = noise
            loss = torch.nn.functional.mse_loss(pred.float(), target.float())
        opt.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(opt); scaler.update()
        step += 1
        pct = int(step * 100 / a.steps)
        if pct != last_pct:
            last_pct = pct
            log("PROGRESS " + str(pct))

    log("STATUS salvando o LoRA...")
    out_dir = os.path.dirname(a.output) or "."
    os.makedirs(out_dir, exist_ok=True)
    state = get_peft_model_state_dict(unet)
    # salva em formato diffusers (o ComfyUI moderno carrega); pytorch_lora_weights.safetensors
    StableDiffusionPipeline.save_lora_weights(out_dir, unet_lora_layers=state,
                                              safe_serialization=True)
    src = os.path.join(out_dir, "pytorch_lora_weights.safetensors")
    if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(a.output):
        try:
            if os.path.exists(a.output):
                os.remove(a.output)
            os.replace(src, a.output)
        except Exception:
            import shutil; shutil.copy(src, a.output)
    log("DONE " + a.output)
    return 0

try:
    rc = main()
    sys.exit(rc or 0)
except Exception as e:
    sys.stdout.write("ERROR " + repr(e) + "\n")
    traceback.print_exc()
    sys.exit(1)
'''
