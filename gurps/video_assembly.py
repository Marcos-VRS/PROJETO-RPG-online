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


def _cleanup(*paths):
    for p in paths:
        try:
            os.remove(p)
        except Exception:  # noqa: BLE001
            pass
