"""Sobreposição de título em imagens (modo Capa).

Modelos de imagem não escrevem texto legível, então o nome do episódio é
escrito POR CIMA da arte gerada, via Pillow — nítido e sempre legível. Um
scrim (degradê escuro) embaixo garante contraste.
"""
from __future__ import annotations

import io
import os

# Fontes candidatas (Windows). Cai na default do Pillow se nenhuma existir.
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/georgiab.ttf",   # Georgia Bold (serif, boa pra RPG)
    "C:/Windows/Fonts/timesbd.ttf",    # Times New Roman Bold
    "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
    "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
]


def _load_font(size):
    from PIL import ImageFont  # noqa: WPS433
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                continue
    try:
        return ImageFont.load_default(size)  # Pillow >= 10.1 aceita tamanho
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def add_title(png_bytes: bytes, title: str, position: str = "bottom") -> bytes:
    """Escreve `title` por cima da imagem (PNG in -> PNG out). Se o título tiver
    ':' ou '-', a primeira parte vira uma linha menor (ex. 'Episódio 7') acima
    do título principal. Sempre retorna PNG; em erro, devolve a imagem original."""
    title = (title or "").strip()
    if not title:
        return png_bytes
    try:
        from PIL import Image, ImageDraw  # noqa: WPS433

        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        W, H = img.size
        draw = ImageDraw.Draw(img)

        # separa "Episódio 7: O Portão" -> topo "EPISÓDIO 7", principal "O PORTÃO"
        top_line, main = "", title
        for sep in (":", " - ", " — "):
            if sep in title:
                a, b = title.split(sep, 1)
                top_line, main = a.strip().upper(), b.strip()
                break
        main = main.upper()

        margin = int(W * 0.07)
        max_w = W - 2 * margin
        main_size = max(28, int(W * 0.11))
        main_font = _load_font(main_size)
        # reduz até caber em no máx. 3 linhas
        lines = _wrap(draw, main, main_font, max_w)
        while len(lines) > 3 and main_size > 24:
            main_size = int(main_size * 0.9)
            main_font = _load_font(main_size)
            lines = _wrap(draw, main, main_font, max_w)
        top_font = _load_font(max(18, int(main_size * 0.42)))

        line_h = main_size + int(main_size * 0.18)
        top_h = (int(main_size * 0.6) + 8) if top_line else 0
        block_h = top_h + line_h * len(lines)

        # posição vertical do bloco
        if position == "top":
            block_top = margin
        else:
            block_top = H - block_h - margin

        # scrim degradê pra legibilidade
        scrim_h = block_h + int(H * 0.12)
        scrim = Image.new("RGBA", (W, scrim_h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(scrim)
        for i in range(scrim_h):
            # mais escuro perto do texto
            a = int(170 * (i / scrim_h)) if position == "top" else int(170 * (1 - i / scrim_h))
            sdraw.line([(0, i), (W, i)], fill=(0, 0, 0, a))
        scrim_y = 0 if position == "top" else H - scrim_h
        img.alpha_composite(scrim, (0, scrim_y))

        def centered(draw_text, font, y, fill):
            tw = draw.textlength(draw_text, font=font)
            x = (W - tw) / 2
            # contorno pra destacar
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    if dx or dy:
                        draw.text((x + dx, y + dy), draw_text, font=font, fill=(0, 0, 0, 220))
            draw.text((x, y), draw_text, font=font, fill=fill)

        y = block_top
        if top_line:
            centered(top_line, top_font, y, (220, 190, 120, 255))  # dourado
            y += top_h
        for ln in lines:
            centered(ln, main_font, y, (245, 245, 245, 255))
            y += line_h

        out = io.BytesIO()
        img.convert("RGB").save(out, format="PNG")
        return out.getvalue()
    except Exception:  # noqa: BLE001
        return png_bytes
