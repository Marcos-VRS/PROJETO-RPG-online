"""Worker do Gerador de Personagem (LoRA SD1.5).

Dois trabalhos, mesma fila:
  - dataset_pending: gera a FOLHA DE POSES (dataset) do personagem via IP-Adapter
    a partir da imagem-semente (varia a pose pelo texto, trava a cara pela imagem).
  - train_pending:   instala o treinador (uma vez) no python do ComfyUI e treina
    um LoRA SD1.5 com as poses curadas (keep=True). Salva em models/loras.

Roda ao lado do imagegen_worker (o launcher sobe os dois). Degrada gracioso: se o
ComfyUI/treinador não estiver disponível, marca o pedido como failed com mensagem.

Uso:
    python manage.py charlora_worker            # loop
    python manage.py charlora_worker --once     # processa 1 e sai (teste)
"""
import os
import subprocess
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from gurps import comfyui_client
from gurps.charlora_trainer import TRAIN_DEPS, TRAINER_SOURCE
from gurps.models import CharacterLora, CharacterLoraImage

# Variações do dataset (img2img): mantêm o MESMO personagem e a MESMA roupa
# (parte da imagem-semente, pouco denoise) e só variam expressão/luz/ângulo leve.
# A VARIEDADE DE POSES não vem daqui — vem do LoRA na hora de usar (o modelo base
# sabe desenhar "sentado/correndo"; o LoRA injeta o personagem). Tentar inventar
# poses aqui (como antes) quebrava a identidade. (tag, trecho EN, denoise).
VARIATIONS = [
    ("neutral", "neutral expression", 0.42),
    ("smile", "smiling warmly", 0.50),
    ("serious", "serious expression", 0.48),
    ("angry", "angry expression", 0.55),
    ("look_left", "looking slightly to the left", 0.50),
    ("look_right", "looking slightly to the right", 0.50),
    ("soft_light", "soft diffused lighting", 0.45),
    ("dramatic_light", "dramatic rim lighting", 0.52),
    ("closeup", "close-up of the face, sharp focus", 0.50),
    ("three_quarter", "slight three-quarter angle", 0.55),
    ("determined", "determined expression", 0.50),
    ("calm", "calm expression, looking forward", 0.45),
    ("side_glance", "glancing to the side", 0.52),
    ("low_angle", "slightly low camera angle", 0.55),
    ("natural", "natural daylight", 0.45),
    ("detailed", "highly detailed, crisp", 0.40),
]


class Command(BaseCommand):
    help = "Worker do Gerador de Personagem (LoRA SD1.5): gera dataset e treina."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=4.0)
        parser.add_argument("--url", default=comfyui_client.DEFAULT_URL)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **opts):
        self.base_url = opts["url"]
        once = opts["once"]
        interval = opts["interval"]
        self.stdout.write(self.style.SUCCESS("charlora_worker iniciado. Ctrl+C pra parar."))
        try:
            while True:
                lora = (CharacterLora.objects
                        .filter(status__in=["dataset_pending", "train_pending"])
                        .order_by("updated_at").first())
                if lora is None:
                    if once:
                        break
                    time.sleep(interval)
                    continue
                try:
                    if lora.status == "dataset_pending":
                        self._build_dataset(lora)
                    elif lora.status == "train_pending":
                        self._train(lora)
                except Exception as e:  # noqa: BLE001
                    self._fail(lora, f"erro inesperado: {e}")
                if once:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\ncharlora_worker parado.")

    # ---------- util ----------
    def _set(self, lora, **f):
        for k, v in f.items():
            setattr(lora, k, v)
        f.setdefault("updated_at", None)
        lora.save()

    def _fail(self, lora, msg):
        self.stdout.write(self.style.ERROR(f"#{lora.id} FALHOU: {msg}"))
        lora.status = "failed"
        lora.error = str(msg)[:500]
        lora.save(update_fields=["status", "error", "updated_at"])

    def _seed_bytes(self, lora):
        a = lora.seed_asset
        if a and getattr(a, "image", None) and not a.image.name.lower().endswith(".svg"):
            try:
                a.image.open("rb"); d = a.image.read(); a.image.close(); return d
            except Exception:  # noqa: BLE001
                pass
        if lora.seed_image:
            try:
                lora.seed_image.open("rb"); d = lora.seed_image.read(); lora.seed_image.close(); return d
            except Exception:  # noqa: BLE001
                pass
        return None

    # ---------- dataset ----------
    @staticmethod
    def _resize_seed(seed_bytes, max_side=768):
        """Normaliza a semente: RGB, lado maior = max_side (o img2img segue o tamanho
        da imagem de entrada). Retorna PNG bytes (ou os bytes originais se falhar)."""
        try:
            from PIL import Image  # noqa: WPS433
            import io  # noqa: WPS433
            im = Image.open(io.BytesIO(seed_bytes)).convert("RGB")
            w, h = im.size
            if max(w, h) > max_side:
                if w >= h:
                    im = im.resize((max_side, max(1, round(h * max_side / w))))
                else:
                    im = im.resize((max(1, round(w * max_side / h)), max_side))
            buf = io.BytesIO(); im.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:  # noqa: BLE001
            return seed_bytes

    def _build_dataset(self, lora):
        self._set(lora, status="dataset_pending", progress="preparando as variações...", error="")
        seed = self._seed_bytes(lora)
        if seed is None:
            self._fail(lora, "sem imagem-semente (escolha uma do journal ou envie uma).")
            return
        st = comfyui_client.status(self.base_url)
        if not st.get("online"):
            self._fail(lora, "ComfyUI offline — não dá pra gerar as variações agora.")
            return
        ckpt = comfyui_client.pick_checkpoint(comfyui_client.DEFAULT_CKPT, self.base_url)
        seed = self._resize_seed(seed, 768)
        rel_dir = f"charloras/{lora.id}"
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir.replace("/", os.sep))
        os.makedirs(abs_dir, exist_ok=True)
        lora.images.all().delete()  # regerar: limpa o anterior
        trigger = (lora.trigger_word or f"ch_{lora.id}").strip()
        desc = (lora.description or "").strip()
        # a legenda é CONSTANTE (gatilho + aparência) pra o gatilho absorver a
        # identidade/roupa; a variação (expressão/luz) fica livre, não é legendada.
        caption = f"{trigger}, " + (desc if desc else "a character") + ", solo"
        base_prompt = (desc + ", " if desc else "") + "same character, same outfit, consistent, high quality, detailed, solo"

        def _save(idx, png, tag):
            rel = f"{rel_dir}/img_{idx:03d}.png"
            with open(os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep)), "wb") as fh:
                fh.write(png)
            CharacterLoraImage.objects.create(lora=lora, file=rel, caption=caption, pose=tag, keep=True)

        made = 0
        # 0) a própria semente entra como imagem de maior fidelidade.
        _save(0, seed, "semente"); made += 1
        n = max(4, min(int(lora.n_poses or 16), len(VARIATIONS)))
        for i in range(n):
            tag, suffix, dn = VARIATIONS[i % len(VARIATIONS)]
            self._set(lora, progress=f"gerando variação {i+1}/{n} ({tag})...",
                      progress_pct=int(i * 100 / n))
            prompt = base_prompt + ", " + suffix
            try:
                # img2img: PARTE da semente (mantém a roupa), só nudge pela variação.
                png = comfyui_client.generate_png(
                    prompt=prompt, negative=comfyui_client.DEFAULT_NEGATIVE,
                    width=768, height=768, steps=10, cfg=2.2, seed=None, ckpt=ckpt,
                    base_url=self.base_url, timeout=240,
                    init_image_bytes=seed, init_image_filename="seed.png", denoise=dn)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  variação {tag} falhou: {str(e)[:100]}"))
                continue
            _save(i + 1, png, tag); made += 1
        if made <= 1:
            self._fail(lora, "nenhuma variação foi gerada (ComfyUI falhou em todas).")
            return
        self._set(lora, status="dataset_ready",
                  progress=f"{made} imagens (mesmo personagem) — revise e treine.",
                  progress_pct=100, error="")
        self.stdout.write(self.style.SUCCESS(f"#{lora.id} dataset pronto: {made} imagens."))

    # ---------- treino ----------
    def _comfy_paths(self):
        home = comfyui_client.find_portable_comfyui()
        if home is None:
            return None, None, None
        py = home / "python_embeded" / "python.exe"
        loras = home / "ComfyUI" / "models" / "loras"
        ckpts = home / "ComfyUI" / "models" / "checkpoints"
        return py, loras, ckpts

    def _ensure_deps(self, lora, py):
        check = subprocess.run([str(py), "-c", "import diffusers, peft, accelerate, torchvision"],
                               capture_output=True, text=True)
        if check.returncode == 0:
            return True
        self._set(lora, progress="instalando o treinador (download único, alguns min)...")
        self.stdout.write("  instalando deps do treino no python do ComfyUI...")
        try:
            r = subprocess.run([str(py), "-m", "pip", "install", "--no-input", *TRAIN_DEPS],
                               capture_output=True, text=True, timeout=2400)
        except Exception as e:  # noqa: BLE001
            self._fail(lora, f"falha ao instalar o treinador: {e}")
            return False
        # revalida
        again = subprocess.run([str(py), "-c", "import diffusers, peft, accelerate, torchvision"],
                               capture_output=True, text=True)
        if again.returncode != 0:
            self._fail(lora, "treinador não ficou disponível após instalar: "
                       + (r.stderr or r.stdout or "")[-300:])
            return False
        return True

    def _stage_dataset(self, lora):
        """Copia as imagens curadas (keep=True) + legendas pra uma pasta limpa de treino."""
        import shutil
        home = os.environ.get("ROLL3D6_DESKTOP_HOME") or settings.MEDIA_ROOT
        train_dir = os.path.join(home, "charlora_train", str(lora.id))
        if os.path.isdir(train_dir):
            shutil.rmtree(train_dir, ignore_errors=True)
        os.makedirs(train_dir, exist_ok=True)
        n = 0
        for im in lora.images.filter(keep=True):
            src = os.path.join(settings.MEDIA_ROOT, im.file.replace("/", os.sep))
            if not os.path.exists(src):
                continue
            dst = os.path.join(train_dir, f"img_{n:03d}.png")
            shutil.copy(src, dst)
            with open(os.path.splitext(dst)[0] + ".txt", "w", encoding="utf-8") as fh:
                fh.write(im.caption or (lora.trigger_word or f"ch_{lora.id}"))
            n += 1
        return train_dir, n

    def _train(self, lora):
        self._set(lora, status="training", progress="preparando o treino...", progress_pct=-1, error="")
        py, loras_dir, ckpts_dir = self._comfy_paths()
        if py is None:
            self._fail(lora, "instalação do ComfyUI não encontrada (python_embeded).")
            return
        if not self._ensure_deps(lora, py):
            return
        train_dir, n = self._stage_dataset(lora)
        if n < 4:
            self._fail(lora, f"poucas imagens pro treino ({n}); mantenha ao menos 4 (keep).")
            return
        # checkpoint base SD1.5 (o do vídeo), onde o LoRA vai se aplicar
        base = (lora.base_ckpt or comfyui_client.VIDEO_CKPT)
        ckpt_path = os.path.join(str(ckpts_dir), base)
        if not os.path.exists(ckpt_path):
            self._fail(lora, f"checkpoint SD1.5 base não encontrado: {base}")
            return
        # materializa o script do treinador em disco
        home = os.environ.get("ROLL3D6_DESKTOP_HOME") or settings.MEDIA_ROOT
        script_dir = os.path.join(home, "charlora")
        os.makedirs(script_dir, exist_ok=True)
        script = os.path.join(script_dir, "train_sd15_lora.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(TRAINER_SOURCE)
        out_name = f"char_{lora.id}.safetensors"
        out_path = os.path.join(str(loras_dir), out_name)
        cmd = [str(py), "-s", script, "--ckpt", ckpt_path, "--data", train_dir,
               "--output", out_path, "--steps", str(int(lora.train_steps or 1200)),
               "--rank", str(int(lora.rank or 16))]
        self.stdout.write(f"#{lora.id} treinando: {' '.join(cmd)}")
        self._set(lora, progress=f"treinando ({n} imagens, {lora.train_steps} passos)...", progress_pct=0)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
        except Exception as e:  # noqa: BLE001
            self._fail(lora, f"não consegui iniciar o treino: {e}")
            return
        done_file = None
        err_msg = None
        for line in proc.stdout:
            line = line.rstrip()
            if line.startswith("PROGRESS "):
                try:
                    pct = int(line.split(" ", 1)[1])
                    CharacterLora.objects.filter(pk=lora.id).update(progress_pct=pct)
                except Exception:  # noqa: BLE001
                    pass
            elif line.startswith("STATUS "):
                CharacterLora.objects.filter(pk=lora.id).update(progress=line[7:][:160])
            elif line.startswith("DONE "):
                done_file = line[5:].strip()
            elif line.startswith("ERROR "):
                err_msg = line[6:].strip()
            else:
                self.stdout.write("  " + line[:200])
        proc.wait()
        if done_file and os.path.exists(out_path):
            lora.refresh_from_db()
            self._set(lora, status="trained", lora_file=out_name, progress="treino concluído.",
                      progress_pct=100, error="")
            self.stdout.write(self.style.SUCCESS(f"#{lora.id} LoRA treinado -> {out_name}"))
        else:
            self._fail(lora, err_msg or f"treino terminou sem gerar o arquivo (rc={proc.returncode}).")
