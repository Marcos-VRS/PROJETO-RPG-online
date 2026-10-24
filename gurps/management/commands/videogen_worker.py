"""Worker de geração de VÍDEO (AnimateDiff local + ffmpeg).

Para cada VideoGenRequest pending: lê o journal, pede um storyboard ao claude,
gera cada tomada como um clipe curto (AnimateDiff na GPU), e costura tudo com
ffmpeg + trilha por clima. Vídeo longo (~90s) por montagem de clipes curtos —
cabe nos 6GB (cada tomada é curta). Nunca quebra o serviço.

Uso:
    python manage.py videogen_worker            # loop contínuo
    python manage.py videogen_worker --once      # processa 1 e sai (teste)
"""
import os
import tempfile
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from gurps import ai_context, comfyui_client, video_assembly
from gurps.models import VideoGenRequest


class Command(BaseCommand):
    help = "Worker de geração de vídeo (AnimateDiff + ffmpeg): storyboard -> clipes -> montagem."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=4.0)
        parser.add_argument("--url", default=comfyui_client.DEFAULT_URL)
        parser.add_argument("--timeout", type=int, default=900, help="timeout por clipe (s)")
        parser.add_argument("--claude", default="claude")
        parser.add_argument("--model", default="sonnet")
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **opts):
        self.base_url = opts["url"]
        self.clip_timeout = opts["timeout"]
        self.claude_bin = opts.get("claude") or "claude"
        self.claude_model = (opts.get("model") or "").strip()
        interval = opts["interval"]
        once = opts["once"]

        st = comfyui_client.status(self.base_url)
        has_models = comfyui_client.video_pick_checkpoint(self.base_url) if st.get("online") else False
        self.stdout.write(self.style.SUCCESS(
            f"videogen_worker iniciado (comfyui={self.base_url}, online={st.get('online')}, "
            f"modelos_video={has_models}). Ctrl+C pra parar."))
        try:
            while True:
                req = (VideoGenRequest.objects.filter(status="pending")
                       .order_by("created_at").first())
                if req is None:
                    if once:
                        break
                    time.sleep(interval)
                    continue
                self._process(req)
                if once:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\nvideogen_worker parado.")

    def _set(self, req, **fields):
        for k, v in fields.items():
            setattr(req, k, v)
        req.save(update_fields=list(fields.keys()) + ["updated_at"])

    def _process(self, req):
        self._set(req, status="processing", progress="montando storyboard...")
        self.stdout.write(f"#{req.id} video: {req.prompt[:50]!r} (alvo {req.target_seconds}s)")

        # 1) contexto do journal + storyboard via claude
        ctx = ""
        if req.use_context:
            try:
                ctx = ai_context.build_campaign_context(req.campanha)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  contexto falhou: {e}"))
        board, used = ai_context.write_storyboard_via_claude(
            ctx, req.prompt, req.style, req.target_seconds,
            claude_bin=self.claude_bin, model=self.claude_model)
        shots = board.get("shots") or []
        mood = board.get("mood") or "epic"
        if not shots:
            self._fail(req, "storyboard vazio")
            return
        human = "\n".join(f"{i+1}. ({s['seconds']}s) {s['prompt']}" for i, s in enumerate(shots))
        self._set(req, storyboard=shots, mood=mood,
                  expanded_prompt=f"[clima: {mood}] ({'claude' if used else 'mecanico'})\n" + human,
                  progress=f"0/{len(shots)} tomadas")
        self.stdout.write(f"  storyboard: {len(shots)} tomadas, clima={mood} ({'claude' if used else 'mecanico'})")

        # 2) gera cada tomada (libera VRAM antes de cada uma pra evitar OOM
        # acumulado em GPU pequena; re-tenta se o ComfyUI cair no meio).
        tmpdir = tempfile.mkdtemp(prefix=f"rpgvid_{req.id}_")
        clips = []
        for i, s in enumerate(shots, 1):
            self._set(req, progress=f"gerando tomada {i}/{len(shots)}")
            self.stdout.write(f"  #{req.id} tomada {i}/{len(shots)}: {s['prompt'][:60]!r}")
            comfyui_client.free_memory(self.base_url)
            mp4 = self._gen_clip(req, s, i, len(shots))
            if mp4 is None:
                return  # _gen_clip já marcou failed
            cp = os.path.join(tmpdir, f"shot_{i:03d}.mp4")
            with open(cp, "wb") as f:
                f.write(mp4)
            clips.append(cp)

        # 3) montagem + trilha: música escolhida pelo GM tem prioridade; senão
        # escolhe automática pelo clima.
        self._set(req, progress="montando vídeo + trilha...")
        music = None
        if req.music_file:
            music = video_assembly.resolve_music_rel(settings.MEDIA_ROOT, req.music_file)
        if not music:
            music = video_assembly.pick_music(settings.MEDIA_ROOT, mood)
        rel = f"videogen/vid_{req.id}.mp4"
        out = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        try:
            video_assembly.assemble(clips, out, music_path=music)
        except Exception as e:  # noqa: BLE001
            self._fail(req, f"montagem falhou: {e}")
            return

        self._set(req, result_file=rel, status="done", error="", progress="pronto")
        self.stdout.write(self.style.SUCCESS(
            f"#{req.id} OK — vídeo montado ({len(clips)} tomadas, musica={bool(music)})."))

    def _gen_clip(self, req, s, i, n):
        """Gera um clipe com até 2 tentativas. Se o ComfyUI cair (OOM/crash),
        espera ele voltar (o launcher reinicia) e tenta de novo. Retorna os bytes
        do mp4, ou None (e marca failed) se falhar de vez."""
        for attempt in (1, 2):
            try:
                return comfyui_client.generate_clip_mp4(
                    prompt=s["prompt"], seconds=s["seconds"], fps=req.fps,
                    width=req.width, height=req.height, steps=req.steps, cfg=req.cfg,
                    base_url=self.base_url, timeout=self.clip_timeout)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(
                    f"  tomada {i} tentativa {attempt} falhou: {str(e)[:120]}"))
                if attempt == 1:
                    self._set(req, progress=f"tomada {i}: ComfyUI caiu, aguardando voltar...")
                    comfyui_client.wait_online(self.base_url, timeout=180)
                    comfyui_client.free_memory(self.base_url)
                else:
                    self._fail(req, f"tomada {i} falhou após 2 tentativas: {str(e)[:300]}")
                    return None
        return None

    def _fail(self, req, msg):
        req.status = "failed"
        req.error = str(msg)[:500]
        req.save(update_fields=["status", "error", "updated_at"])
        self.stdout.write(self.style.ERROR(f"#{req.id} FALHOU: {req.error}"))
