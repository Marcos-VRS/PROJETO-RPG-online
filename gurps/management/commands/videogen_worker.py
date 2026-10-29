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
from gurps.models import VideoBeat, VideoGenRequest


class Command(BaseCommand):
    help = "Worker de geração de vídeo (AnimateDiff + ffmpeg): storyboard -> clipes -> montagem."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=4.0)
        parser.add_argument("--url", default=comfyui_client.DEFAULT_URL)
        parser.add_argument("--timeout", type=int, default=3600, help="timeout por clipe (s)")
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
                # Beats pendentes (modo editor) têm prioridade — são tarefas curtas.
                beat = (VideoBeat.objects.filter(status="pending")
                        .select_related("project").order_by("created_at").first())
                if beat is not None:
                    self._process_beat(beat)
                    if once:
                        break
                    continue
                req = (VideoGenRequest.objects.filter(status="pending")
                       .order_by("created_at").first())
                if req is None:
                    if once:
                        break
                    time.sleep(interval)
                    continue
                if req.mode == "beats":
                    self._assemble_project(req)
                else:
                    self._process(req)
                if once:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\nvideogen_worker parado.")

    def _set(self, req, **fields):
        for k, v in fields.items():
            setattr(req, k, v)
        req.save(update_fields=list(fields.keys()) + ["updated_at"])

    def _journal_images(self, campanha):
        """{nome_lower: caminho} das imagens RASTER do journal (retratos/assets),
        pra o IP-Adapter usar a aparência dos personagens no vídeo."""
        from gurps.models import CampanhaAssets  # noqa: WPS433
        out = {}
        for a in (CampanhaAssets.objects.filter(campanha=campanha, slot__in=[1, 2])
                  .order_by("-id")):
            if not a.image or (a.image.name or "").lower().endswith(".svg"):
                continue
            try:
                path = a.image.path
            except Exception:  # noqa: BLE001
                continue
            if os.path.exists(path):
                out[(a.name or "").strip().lower()] = (a.name, path)
        return out

    def _pause_requested(self, req):
        """Lê do banco se o GM pediu pausa (flag setada pela view, fora do worker)."""
        from gurps.models import VideoGenRequest  # noqa: WPS433
        return VideoGenRequest.objects.filter(id=req.id).values_list(
            "pause_requested", flat=True).first() or False

    def _process(self, req):
        # Limpa flag de pausa de uma rodada anterior (ex. ao retomar).
        self._set(req, status="processing", progress="montando storyboard...",
                  pause_requested=False)
        self.stdout.write(f"#{req.id} video: {req.prompt[:50]!r} (alvo {req.target_seconds}s)")

        images_map = self._journal_images(req.campanha)  # {nome_lower: (nome, path)}

        # 1) storyboard: RETOMA o existente (resume) ou pede um novo ao claude.
        if req.storyboard:
            shots = req.storyboard
            mood = req.mood or "epic"
            self.stdout.write(f"  RETOMANDO storyboard existente ({len(shots)} tomadas).")
        else:
            ctx = ""
            if req.use_context:
                try:
                    ctx = ai_context.build_campaign_context(req.campanha)
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.WARNING(f"  contexto falhou: {e}"))
            board, used = ai_context.write_storyboard_via_claude(
                ctx, req.prompt, req.style, req.target_seconds,
                available_images=[n for (n, _p) in images_map.values()],
                claude_bin=self.claude_bin, model=self.claude_model)
            shots = board.get("shots") or []
            mood = board.get("mood") or "epic"
            if not shots:
                self._fail(req, "storyboard vazio")
                return
            human = "\n".join(
                f"{i+1}. ({s['seconds']}s)" + (f" [{s['image']}]" if s.get('image') else "")
                + f" {s['prompt']}" for i, s in enumerate(shots))
            self._set(req, storyboard=shots, mood=mood,
                      expanded_prompt=f"[clima: {mood}] ({'claude' if used else 'mecanico'})\n" + human,
                      progress=f"0/{len(shots)} tomadas")
            self.stdout.write(f"  storyboard: {len(shots)} tomadas, clima={mood}")

        # 2) gera cada tomada. Clipes ficam em disco (media/videogen/clips/<id>/)
        # pra permitir RETOMAR sem refazer as que já saíram. Libera VRAM antes de
        # cada uma; re-tenta se o ComfyUI cair; monta o parcial se faltar.
        clipsdir = os.path.join(settings.MEDIA_ROOT, "videogen", "clips", str(req.id))
        os.makedirs(clipsdir, exist_ok=True)
        clips = []
        consecutive_fail = 0
        paused = False
        for i, s in enumerate(shots, 1):
            cp = os.path.join(clipsdir, f"shot_{i:03d}.mp4")
            if os.path.exists(cp) and os.path.getsize(cp) > 0:
                clips.append(cp)
                continue  # já gerada antes (resume)
            # GM pediu pausa? Para aqui (sem começar a próxima) e monta o parcial.
            if self._pause_requested(req):
                self.stdout.write(f"  pausa solicitada — montando o parcial com {len(clips)} cena(s).")
                paused = True
                break
            self._set(req, progress=f"gerando tomada {i}/{len(shots)}")
            ref_name = (s.get("image") or "").strip().lower()
            ref_bytes = None
            if ref_name and ref_name in images_map:
                try:
                    with open(images_map[ref_name][1], "rb") as fh:
                        ref_bytes = fh.read()
                except Exception:  # noqa: BLE001
                    ref_bytes = None
            self.stdout.write(
                f"  #{req.id} tomada {i}/{len(shots)}"
                + (f" [img:{s.get('image')}]" if ref_bytes else "") + f": {s['prompt'][:50]!r}")
            comfyui_client.free_memory(self.base_url)
            mp4 = self._gen_clip(req, s, i, len(shots), ref_bytes)
            if mp4 is None:
                consecutive_fail += 1
                if len(clips) >= 3 or consecutive_fail >= 2:
                    self.stdout.write(self.style.WARNING(
                        f"  tomada {i} falhou — montando o parcial com {len(clips)} cena(s)."))
                    break
                continue
            consecutive_fail = 0
            with open(cp, "wb") as f:
                f.write(mp4)
            clips.append(cp)

        if not clips:
            if paused:
                # pausou antes da 1a cena — deixa retomável, sem marcar erro feio
                self._set(req, status="failed", pause_requested=False,
                          error="pausado antes da 1a cena — use Continuar",
                          progress="pausado (0 cenas)")
            else:
                self._fail(req, "nenhuma cena pôde ser gerada (ComfyUI instável na GPU?).")
            return
        partial = len(clips) < len(shots)

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

        if paused:
            prog = f"pausado — prévia com {len(clips)}/{len(shots)} cenas"
            err = f"pausado: {len(clips)}/{len(shots)} cenas (use Continuar)"
        elif partial:
            prog = f"pronto ({len(clips)}/{len(shots)} cenas)"
            err = f"parcial: {len(clips)}/{len(shots)} cenas"
        else:
            prog = f"pronto ({len(clips)}/{len(shots)} cenas)"
            err = ""
        self._set(req, result_file=rel, status="done", error=err, progress=prog,
                  pause_requested=False)
        tag = " [PAUSADO]" if paused else (" [PARCIAL]" if partial else "")
        self.stdout.write(self.style.SUCCESS(
            f"#{req.id} OK{tag} — vídeo montado ({len(clips)} tomadas, musica={bool(music)})."))

    def _gen_clip(self, req, s, i, n, ref_bytes=None):
        """Gera um clipe com até 2 tentativas. Se vier ref_bytes (retrato do
        journal), usa IP-Adapter pra cena sair com a aparência do personagem.
        Se o ComfyUI cair, espera voltar e tenta de novo. Retorna bytes ou None."""
        for attempt in (1, 2):
            try:
                return comfyui_client.generate_clip_mp4(
                    prompt=s["prompt"], seconds=s["seconds"], fps=req.fps,
                    width=req.width, height=req.height, steps=req.steps, cfg=req.cfg,
                    base_url=self.base_url, timeout=self.clip_timeout,
                    ref_image_bytes=ref_bytes)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(
                    f"  tomada {i} tentativa {attempt} falhou: {str(e)[:120]}"))
                if attempt == 1:
                    self._set(req, progress=f"tomada {i}: ComfyUI instável, aguardando voltar...")
                    comfyui_client.wait_online(self.base_url, timeout=180)
                    comfyui_client.free_memory(self.base_url)
                # attempt 2: desiste DESTA tomada (o _process monta o parcial)
        return None

    def _fail(self, req, msg):
        req.status = "failed"
        req.error = str(msg)[:500]
        req.save(update_fields=["status", "error", "updated_at"])
        self.stdout.write(self.style.ERROR(f"#{req.id} FALHOU: {req.error}"))

    # ===================================================================== #
    # Modo EDITOR DE BEATS: gera um beat (cena) e monta o projeto.
    # ===================================================================== #
    def _set_beat(self, beat, **fields):
        for k, v in fields.items():
            setattr(beat, k, v)
        beat.save(update_fields=list(fields.keys()) + ["updated_at"])

    def _fail_beat(self, beat, msg):
        beat.status = "failed"
        beat.error = str(msg)[:500]
        beat.save(update_fields=["status", "error", "updated_at"])
        self.stdout.write(self.style.ERROR(f"beat #{beat.id} FALHOU: {beat.error}"))

    def _resolve_beat_ref(self, beat):
        """(bytes, nome) da imagem de referência do journal, ou (None, '')."""
        a = beat.ref_asset
        if not a or not getattr(a, "image", None):
            return None, ""
        name = (a.image.name or "")
        if name.lower().endswith(".svg"):
            return None, ""
        try:
            path = a.image.path
        except Exception:  # noqa: BLE001
            return None, ""
        if not os.path.exists(path):
            return None, ""
        try:
            with open(path, "rb") as fh:
                return fh.read(), (a.name or "")
        except Exception:  # noqa: BLE001
            return None, ""

    def _gen_one(self, project, prompt, seconds, seed, ref_bytes, max_frames=None,
                 animate=False, denoise=0.6):
        """Gera UM pedaço contínuo do beat (com retry + espera o ComfyUI voltar).
        Se animate=True, ANIMA a própria imagem (img2vid, fiel). Retorna bytes ou None."""
        if max_frames is None:
            max_frames = comfyui_client.VIDEO_BEAT_MAX_FRAMES
        for attempt in (1, 2):
            try:
                return comfyui_client.generate_clip_mp4(
                    prompt=prompt, seconds=seconds, fps=project.fps,
                    width=project.width, height=project.height,
                    steps=project.steps, cfg=project.cfg, seed=seed,
                    base_url=self.base_url, timeout=self.clip_timeout,
                    ref_image_bytes=ref_bytes, max_frames=max_frames,
                    animate=animate, denoise=denoise, freeinit=not animate)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(
                    f"  sub-clipe tentativa {attempt} falhou: {str(e)[:120]}"))
                if attempt == 1:
                    comfyui_client.wait_online(self.base_url, timeout=180)
                    comfyui_client.free_memory(self.base_url)
        return None

    def _process_beat(self, beat):
        project = beat.project
        self._set_beat(beat, status="processing", progress="escrevendo o prompt...", error="")
        self.stdout.write(f"beat #{beat.id} (proj {project.id}, ordem {beat.order}): "
                          f"{(beat.user_prompt or '')[:50]!r}")

        # 1) prompt CUMULATIVO: lê o journal + os beats anteriores já prontos.
        ref_bytes, ref_name = self._resolve_beat_ref(beat)
        ctx = ""
        if project.use_context:
            try:
                ctx = ai_context.build_campaign_context(project.campanha)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  contexto falhou: {e}"))
        priors = [b.expanded_prompt for b in
                  VideoBeat.objects.filter(project=project, start_ms__lt=beat.start_ms,
                                           status="done").order_by("start_ms", "id")
                  if (b.expanded_prompt or "").strip()]
        expanded, used = ai_context.write_beat_prompt_via_claude(
            ctx, project.prompt, priors, beat.user_prompt or project.prompt,
            correction=beat.correction, style_key=project.style, ref_name=ref_name,
            claude_bin=self.claude_bin, model=self.claude_model)
        self._set_beat(beat, expanded_prompt=expanded)
        self.stdout.write(f"  prompt ({'claude' if used else 'mecanico'}): {expanded[:70]!r}")

        # 2) beat CONTÍNUO: uma geração (janela deslizante do AnimateDiff) com a
        # MESMA seed em todos os pedaços — trava a aparência/roupa ao longo do
        # beat. Só divide em pedaços se passar do teto de frames por geração.
        import random  # noqa: WPS433
        import shutil  # noqa: WPS433
        fps = project.fps or 8
        max_f = comfyui_client.VIDEO_BEAT_MAX_FRAMES
        total_frames = max(8, int(round((beat.duration_ms or 2000) / 1000.0 * fps)))
        base_seed = beat.seed
        if base_seed is None:
            base_seed = random.randint(1, 2 ** 31 - 1)
            self._set_beat(beat, seed=base_seed)
        chunks = []
        remaining = total_frames
        while remaining > 0:
            chunks.append(min(remaining, max_f))
            remaining -= min(remaining, max_f)
        # Modo "animar a imagem" (fiel): a imagem vira o quadro base (img2vid).
        # fidelity 1.0 -> denoise ~0.35 (bem fiel); 0.0 -> ~0.9 (mais movimento).
        animate = (beat.ref_mode == "animate") and (ref_bytes is not None)
        fidelity = min(1.0, max(0.0, beat.fidelity if beat.fidelity is not None else 0.6))
        denoise = round(0.9 - 0.55 * fidelity, 3)
        if animate:
            self.stdout.write(f"  modo ANIMAR imagem (fiel), denoise={denoise}")
        bdir = os.path.join(settings.MEDIA_ROOT, "videobeats", str(project.id),
                            f"beat_{beat.id}")
        os.makedirs(bdir, exist_ok=True)
        parts = []
        for idx, fcount in enumerate(chunks):
            self._set_beat(beat, progress=(f"gerando {idx+1}/{len(chunks)}"
                           if len(chunks) > 1 else "gerando o beat..."))
            comfyui_client.free_memory(self.base_url)
            mp4 = self._gen_one(project, expanded, fcount / fps, base_seed, ref_bytes,
                                max_frames=max_f, animate=animate, denoise=denoise)
            if mp4 is None:
                if parts:  # usa o que já saiu
                    break
                self._fail_beat(beat, "ComfyUI instavel — nada gerado.")
                return
            sp = os.path.join(bdir, f"part_{idx:03d}.mp4")
            with open(sp, "wb") as f:
                f.write(mp4)
            parts.append(sp)

        # 3) junta os pedaços num vídeo mudo, depois sobrepõe o TRECHO da música
        # [start_ms, dur] pra o preview do beat tocar com som.
        rel = f"videobeats/{project.id}/beat_{beat.id}.mp4"
        out = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        silent = os.path.join(bdir, "silent.mp4")
        try:
            if len(parts) == 1:
                shutil.copyfile(parts[0], silent)
            else:
                video_assembly.assemble(parts, silent)  # concat sem música
        except Exception as e:  # noqa: BLE001
            self._fail_beat(beat, f"juncao do beat falhou: {e}")
            return
        music = None
        if project.music_file:
            music = video_assembly.resolve_music_rel(settings.MEDIA_ROOT, project.music_file)
        has_audio = False
        if music:
            has_audio = video_assembly.mux_music_segment(silent, music, beat.start_ms, out)
        else:
            shutil.copyfile(silent, out)
        self._set_beat(beat, clip_file=rel, status="done",
                       progress=f"pronto ({total_frames} frames" + (", com som" if has_audio else "") + ")")
        self.stdout.write(self.style.SUCCESS(
            f"beat #{beat.id} OK ({total_frames} frames, {len(parts)} pedaco(s), som={has_audio})."))

    def _assemble_project(self, req):
        """Monta o vídeo final do projeto de beats: clipes na ordem + transições
        (corte/crossfade) + trilha."""
        self._set(req, status="processing", progress="montando o video...", error="")
        beats = list(VideoBeat.objects.filter(project=req, status="done")
                     .exclude(clip_file="").order_by("start_ms", "id"))
        if not beats:
            self._fail(req, "nenhum beat pronto pra montar — gere os beats antes.")
            return
        clips, transitions = [], []
        for i, b in enumerate(beats):
            full = os.path.join(settings.MEDIA_ROOT, b.clip_file.replace("/", os.sep))
            if not os.path.exists(full):
                continue
            clips.append(full)
            if i == 0:
                transitions.append({"type": "cut", "ms": 0})
            else:
                transitions.append({"type": b.transition, "ms": int(b.transition_ms or 0)})
        if not clips:
            self._fail(req, "os clipes dos beats sumiram do disco — regere os beats.")
            return

        music = None
        if req.music_file:
            music = video_assembly.resolve_music_rel(settings.MEDIA_ROOT, req.music_file)
        if not music:
            music = video_assembly.pick_music(settings.MEDIA_ROOT, req.mood or "epic")
        rel = f"videogen/vid_{req.id}.mp4"
        out = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        try:
            video_assembly.assemble_with_transitions(
                clips, out, transitions, music_path=music, fps=req.fps)
        except Exception as e:  # noqa: BLE001
            self._fail(req, f"montagem falhou: {e}")
            return
        self._set(req, result_file=rel, status="done", error="",
                  progress=f"pronto ({len(clips)} beats, musica={bool(music)})")
        self.stdout.write(self.style.SUCCESS(
            f"#{req.id} PROJETO montado ({len(clips)} beats, musica={bool(music)})."))
