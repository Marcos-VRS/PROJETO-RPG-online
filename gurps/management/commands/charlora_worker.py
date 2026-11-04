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

# Poses do dataset: (tag curta, trecho em inglês que varia a pose/ângulo/expressão).
# A imagem-semente (IP-Adapter) trava a aparência; o texto muda a pose.
POSES = [
    ("front", "front view, standing, neutral expression, full body"),
    ("three_quarter", "three-quarter view, standing, full body"),
    ("profile", "side profile view, standing, full body"),
    ("back", "back view, standing, full body"),
    ("closeup", "close-up portrait of the face, neutral"),
    ("smile", "close-up portrait, smiling"),
    ("angry", "close-up portrait, angry expression"),
    ("sad", "close-up portrait, sad expression"),
    ("look_up", "looking up, three-quarter view"),
    ("look_down", "looking down, three-quarter view"),
    ("running", "running, dynamic action pose, full body"),
    ("fighting", "fighting stance, full body, dynamic"),
    ("sitting", "sitting down, full body"),
    ("arms_crossed", "arms crossed, standing, full body"),
    ("casting", "casting a spell, dramatic pose, full body"),
    ("walking", "walking, full body, side view"),
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
    def _build_dataset(self, lora):
        self._set(lora, status="dataset_pending", progress="preparando as poses...", error="")
        seed = self._seed_bytes(lora)
        if seed is None:
            self._fail(lora, "sem imagem-semente (escolha uma do journal ou envie uma).")
            return
        st = comfyui_client.status(self.base_url)
        if not st.get("online"):
            self._fail(lora, "ComfyUI offline — não dá pra gerar as poses agora.")
            return
        ckpt = comfyui_client.pick_checkpoint(comfyui_client.DEFAULT_CKPT, self.base_url)
        rel_dir = f"charloras/{lora.id}"
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir.replace("/", os.sep))
        os.makedirs(abs_dir, exist_ok=True)
        # limpa registros antigos (regerar dataset)
        lora.images.all().delete()
        trigger = (lora.trigger_word or f"ch_{lora.id}").strip()
        desc = (lora.description or "").strip()
        n = max(4, min(int(lora.n_poses or 16), len(POSES)))
        made = 0
        for i in range(n):
            tag, pose = POSES[i % len(POSES)]
            self._set(lora, progress=f"gerando pose {i+1}/{n} ({tag})...",
                      progress_pct=int(i * 100 / n))
            prompt = (desc + ", " if desc else "") + pose + ", high quality, detailed, solo"
            try:
                png = comfyui_client.generate_png(
                    prompt=prompt, negative=comfyui_client.DEFAULT_NEGATIVE,
                    width=768, height=768, steps=9, cfg=2.2, seed=None, ckpt=ckpt,
                    base_url=self.base_url, timeout=240,
                    ref_image_bytes=seed, ref_image_filename="seed.png", ref_weight=0.85)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  pose {tag} falhou: {str(e)[:100]}"))
                continue
            rel = f"{rel_dir}/img_{i:03d}.png"
            with open(os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep)), "wb") as fh:
                fh.write(png)
            caption = f"{trigger}, {pose}" + (", " + desc if desc else "")
            CharacterLoraImage.objects.create(lora=lora, file=rel, caption=caption, pose=tag, keep=True)
            made += 1
        if made == 0:
            self._fail(lora, "nenhuma pose foi gerada (ComfyUI falhou em todas).")
            return
        self._set(lora, status="dataset_ready", progress=f"{made} poses geradas — revise e treine.",
                  progress_pct=100, error="")
        self.stdout.write(self.style.SUCCESS(f"#{lora.id} dataset pronto: {made} poses."))

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
