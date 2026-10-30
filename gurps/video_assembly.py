"""Montagem de vídeo com ffmpeg: concatena os clipes gerados e sobrepõe a
trilha por clima. Usa o ffmpeg que vem com o imageio-ffmpeg (sem depender de
ffmpeg no PATH do sistema).

Trilha por clima: arquivos em MEDIA_ROOT/music/<mood>/*.(mp3|m4a|ogg|wav). O
worker escolhe uma faixa do clima; se a pasta estiver vazia, o vídeo sai sem
áudio (degradação graciosa). O GM pode jogar as próprias faixas nessas pastas.
"""
from __future__ import annotations

import os
import random
import subprocess
import tempfile

AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".wav", ".opus", ".flac")


def get_ffmpeg() -> str:
    """Caminho do executável ffmpeg (do imageio-ffmpeg)."""
    try:
        import imageio_ffmpeg  # noqa: WPS433
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return "ffmpeg"  # fallback: PATH do sistema


def music_root(media_root: str) -> str:
    return os.path.join(media_root, "music")


def list_music(media_root: str) -> list[dict]:
    """Lista todas as faixas em MEDIA_ROOT/music/<clima>/, como
    [{"rel": "music/epic/x.mp3", "name": "x", "mood": "epic"}, ...]."""
    root = music_root(media_root)
    items = []
    if not os.path.isdir(root):
        return items
    for mood in sorted(os.listdir(root)):
        mdir = os.path.join(root, mood)
        if not os.path.isdir(mdir):
            continue
        for f in sorted(os.listdir(mdir)):
            if f.lower().endswith(AUDIO_EXTS):
                rel = "music/" + mood + "/" + f
                items.append({"rel": rel, "name": os.path.splitext(f)[0], "mood": mood})
    return items


def resolve_music_rel(media_root: str, rel: str) -> str | None:
    """Valida um caminho relativo de música (anti path-traversal) e devolve o
    caminho absoluto se existir sob MEDIA_ROOT/music. Senão None."""
    if not rel:
        return None
    rel = rel.replace("\\", "/").lstrip("/")
    if not rel.startswith("music/"):
        return None
    root = os.path.realpath(music_root(media_root))
    full = os.path.realpath(os.path.join(media_root, rel.replace("/", os.sep)))
    if os.path.commonpath([root, full]) != root:
        return None  # tentou escapar da pasta music/
    return full if os.path.isfile(full) else None


def pick_music(media_root: str, mood: str) -> str | None:
    """Escolhe uma faixa aleatória do clima; cai em qualquer faixa se o clima
    específico não tiver. Retorna None se não houver nenhuma música."""
    root = music_root(media_root)
    candidates = []
    mood_dir = os.path.join(root, mood or "")
    if mood and os.path.isdir(mood_dir):
        candidates = [os.path.join(mood_dir, f) for f in os.listdir(mood_dir)
                      if f.lower().endswith(AUDIO_EXTS)]
    if not candidates and os.path.isdir(root):
        # qualquer faixa, de qualquer clima
        for dp, _dn, fns in os.walk(root):
            for f in fns:
                if f.lower().endswith(AUDIO_EXTS):
                    candidates.append(os.path.join(dp, f))
    return random.choice(candidates) if candidates else None


def _run(cmd) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=600)
        if p.returncode != 0:
            return False, (p.stderr or b"").decode("utf-8", "replace")[-800:]
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def media_duration_ms(path, ffmpeg=None) -> int:
    """Duração de um áudio/vídeo em ms, lendo a saída do ffmpeg (sem ffprobe,
    que não vem com o imageio-ffmpeg). Retorna 0 se não conseguir."""
    import re
    ff = ffmpeg or get_ffmpeg()
    try:
        p = subprocess.run([ff, "-i", path], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=60)
        txt = (p.stderr or b"").decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return 0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", txt)
    if not m:
        return 0
    h, mn, s, cs = m.groups()
    return int(((int(h) * 3600 + int(mn) * 60 + int(s)) * 100 + int(cs)) * 10)


def assemble(clip_paths, out_path, music_path=None, ffmpeg=None) -> None:
    """Concatena os clipes (mesmo codec/params → concat sem recodificar) e, se
    houver, sobrepõe a música (em loop, cortada no tamanho do vídeo). Lança
    RuntimeError em falha."""
    if not clip_paths:
        raise RuntimeError("sem clipes pra montar")
    ff = ffmpeg or get_ffmpeg()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 1) concat sem recodificar (clipes são todos 512x512 h264 do mesmo encoder)
    listfile = os.path.join(tempfile.gettempdir(), f"rpg_concat_{os.getpid()}.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write("file '" + c.replace("\\", "/").replace("'", "'\\''") + "'\n")

    if not music_path:
        ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                        "-c", "copy", out_path])
        if not ok:
            # fallback: recodifica (caso concat-copy falhe por params divergentes)
            ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path])
        _cleanup(listfile)
        if not ok:
            raise RuntimeError("ffmpeg concat falhou: " + err)
        return

    # 2) concat + música: vídeo do concat, áudio em loop cortado no -shortest
    silent = out_path + ".silent.mp4"
    ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-c", "copy", silent])
    if not ok:
        ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", silent])
    if not ok:
        _cleanup(listfile)
        raise RuntimeError("ffmpeg concat falhou: " + err)

    ok, err = _run([ff, "-y", "-i", silent, "-stream_loop", "-1", "-i", music_path,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", out_path])
    _cleanup(listfile, silent)
    if not ok:
        raise RuntimeError("ffmpeg mux de áudio falhou: " + err)


def _concat_copy(ff, clip_paths, out_path) -> tuple[bool, str]:
    """Concatena clipes sem recodificar (concat demuxer). Fallback reencode."""
    listfile = os.path.join(tempfile.gettempdir(),
                            f"rpg_seg_{os.getpid()}_{random.randint(0, 1 << 30)}.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write("file '" + c.replace("\\", "/").replace("'", "'\\''") + "'\n")
    ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-c", "copy", out_path])
    if not ok:
        ok, err = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path])
    _cleanup(listfile)
    return ok, err


def _mux_music(ff, silent, music_path, out_path) -> tuple[bool, str]:
    return _run([ff, "-y", "-i", silent, "-stream_loop", "-1", "-i", music_path,
                 "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-shortest", out_path])


def fit_to_duration(src_path, dur_ms, out_path, fps=8, ffmpeg=None) -> bool:
    """Encaixa um clipe CURTO (ex. SVD ~2s) na duração do beat sem corte brusco.

    Faz um BOOMERANG (vai-e-volta: original + reverso) pra o loop ser suave, e
    repete até preencher dur_ms, cortando no tamanho exato. Reencoda em yuv420p/fps.
    Retorna True se gerou. Em falha, copia o src cru (nunca quebra)."""
    ff = ffmpeg or get_ffmpeg()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    dur_s = max(0.3, int(dur_ms or 0) / 1000.0)
    src_ms = media_duration_ms(src_path, ff) or 1000
    boom = out_path + ".boom.mp4"
    # 1) boomerang (original + reverso) — movimento de ida e volta, loop sem salto.
    okb, _e = _run([ff, "-y", "-i", src_path,
                    "-filter_complex", "[0:v]reverse[r];[0:v][r]concat=n=2:v=1[v]",
                    "-map", "[v]", "-an", "-r", str(fps), "-pix_fmt", "yuv420p", boom])
    base = boom if okb else src_path
    boom_ms = (src_ms * 2) if okb else src_ms
    # 2) loop o boomerang até passar da duração e corta exato.
    import math
    loops = max(0, math.ceil(dur_s * 1000.0 / max(1, boom_ms)) - 1)
    ok, _err = _run([ff, "-y", "-stream_loop", str(loops), "-i", base,
                     "-t", f"{dur_s:.3f}", "-an", "-r", str(fps),
                     "-pix_fmt", "yuv420p", out_path])
    _cleanup(boom)
    if ok:
        return True
    try:
        import shutil
        shutil.copyfile(src_path, out_path)
    except Exception:  # noqa: BLE001
        pass
    return False


def mux_music_segment(video_path, music_path, start_ms, out_path, ffmpeg=None) -> bool:
    """Sobrepõe no vídeo o TRECHO da música a partir de start_ms (cortado no
    tamanho do vídeo). Usado pra o preview do beat tocar o som certo. Se falhar,
    copia o vídeo sem áudio (nunca quebra). Retorna True se saiu com áudio."""
    ff = ffmpeg or get_ffmpeg()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    start = max(0, int(start_ms)) / 1000.0
    ok, _err = _run([ff, "-y", "-i", video_path, "-ss", f"{start:.3f}", "-i", music_path,
                     "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                     "-c:a", "aac", "-b:a", "192k", "-shortest", out_path])
    if ok:
        return True
    # fallback: sem áudio (copia o vídeo)
    try:
        import shutil
        shutil.copyfile(video_path, out_path)
    except Exception:  # noqa: BLE001
        pass
    return False


def assemble_with_transitions(clip_paths, out_path, transitions, music_path=None,
                              fps=8, ffmpeg=None) -> None:
    """Monta os beats na ordem dada, aplicando a transição de cada um em relação
    ao anterior. `transitions[i]` = {"type": "cut"|"crossfade", "ms": int} descreve
    como o clipe i ENTRA (transitions[0] é ignorado). Cortes secos viram concat
    rápido; crossfades usam o filtro xfade do ffmpeg. Lança RuntimeError em falha.
    """
    if not clip_paths:
        raise RuntimeError("sem clipes pra montar")
    ff = ffmpeg or get_ffmpeg()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    transitions = list(transitions or [])
    while len(transitions) < len(clip_paths):
        transitions.append({"type": "cut", "ms": 0})

    # 1) Agrupa clipes ligados por CORTE SECO em segmentos (concat rápido); um
    # CROSSFADE quebra o segmento e vira uma junção xfade entre segmentos.
    segments = [[clip_paths[0]]]
    xfades = []  # segundos de crossfade entre segment[k-1] e segment[k]
    for i in range(1, len(clip_paths)):
        t = transitions[i] or {}
        if (t.get("type") == "crossfade") and int(t.get("ms") or 0) > 0:
            segments.append([clip_paths[i]])
            xfades.append(max(0.1, int(t["ms"]) / 1000.0))
        else:
            segments[-1].append(clip_paths[i])

    tmp = []
    try:
        # Sem nenhum crossfade: é um único segmento = concat simples.
        if len(segments) == 1:
            if not music_path:
                ok, err = _concat_copy(ff, segments[0], out_path)
                if not ok:
                    raise RuntimeError("ffmpeg concat falhou: " + err)
                return
            silent = out_path + ".silent.mp4"
            tmp.append(silent)
            ok, err = _concat_copy(ff, segments[0], silent)
            if not ok:
                raise RuntimeError("ffmpeg concat falhou: " + err)
            ok, err = _mux_music(ff, silent, music_path, out_path)
            if not ok:
                raise RuntimeError("ffmpeg mux de áudio falhou: " + err)
            return

        # 2) Concatena cada segmento num arquivo real (cortes secos internos).
        seg_files = []
        for idx, seg in enumerate(segments):
            if len(seg) == 1:
                sf = seg[0]
            else:
                sf = os.path.join(tempfile.gettempdir(),
                                  f"rpg_segf_{os.getpid()}_{idx}.mp4")
                tmp.append(sf)
                ok, err = _concat_copy(ff, seg, sf)
                if not ok:
                    raise RuntimeError("ffmpeg concat de segmento falhou: " + err)
            seg_files.append(sf)

        # 3) Crossfade PAR A PAR, materializando cada intermediário. O xfade
        # encadeado num filtergraph só falha porque o output intermediário não
        # tem duração no config; materializar em arquivo real resolve (o offset é
        # medido do arquivo). Cada passo é um xfade simples de 2 entradas.
        merged = seg_files[0]
        merged_tmp = False
        for k in range(1, len(seg_files)):
            d = xfades[k - 1]
            dur = media_duration_ms(merged, ff) / 1000.0
            if dur <= 0:
                dur = 2.0
            offset = max(0.1, dur - d)
            nxt = os.path.join(tempfile.gettempdir(),
                               f"rpg_xf_{os.getpid()}_{k}.mp4")
            # xfade cru de 2 entradas (clipes são uniformes: mesmo tamanho/fps/encoder).
            # Normalizar com fps/setsar/setpts quebra o config do xfade neste build.
            fg = f"[0:v][1:v]xfade=transition=fade:duration={d:.3f}:offset={offset:.3f}[out]"
            ok, err = _run([ff, "-y", "-i", merged, "-i", seg_files[k],
                            "-filter_complex", fg, "-map", "[out]",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", nxt])
            if merged_tmp:
                _cleanup(merged)
            if not ok:
                _cleanup(nxt)
                raise RuntimeError("ffmpeg xfade falhou: " + err)
            merged, merged_tmp = nxt, True
            tmp.append(nxt)

        if not music_path:
            import shutil
            shutil.move(merged, out_path)
            if merged in tmp:
                tmp.remove(merged)
        else:
            ok, err = _mux_music(ff, merged, music_path, out_path)
            if not ok:
                raise RuntimeError("ffmpeg mux de áudio falhou: " + err)
    finally:
        _cleanup(*tmp)


def _cleanup(*paths):
    for p in paths:
        try:
            os.remove(p)
        except Exception:  # noqa: BLE001
            pass
