"""Contexto de campanha pra geração por IA (journal → prompt).

Reúne um resumo textual do "journal" da campanha (descrição, regras, contexto
acumulado do que já foi aprovado, assets e personagens) pra dar COERÊNCIA às
gerações de imagem/mapa — "qualquer prompt lê o journal". Também:

- `append_approved_context()`: acumula no `Campanha.ai_context` o que o GM aprova.
- `write_image_prompt_via_claude()`: usa o `claude -p` headless (mesma assinatura,
  sem custo de API) pra transformar o pedido curto do GM num prompt de imagem
  otimizado e coerente com o mundo. Fallback mecânico se o claude não existir.

Nada aqui quebra o serviço: se o claude falhar/sumir, cai no modo mecânico.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import threading
import time

# Climas pra trilha (biblioteca por clima). O claude escolhe um destes.
MOODS = ["epic", "battle", "tense", "sad", "mysterious", "calm", "triumphant", "dark", "adventure"]

MAX_CONTEXT_CHARS = 6000
MAX_AI_CONTEXT_CHARS = 8000

# Palavras-chave de estilo (espelha o seletor da UI). Server-authoritative pra
# o claude e o fallback mecânico usarem a mesma definição.
STYLE_KEYWORDS = {
    "cinematic_dark": ("cinematic photorealistic, dramatic chiaroscuro lighting, dark moody "
                       "background, low key lighting, muted desaturated earthy palette, rim "
                       "light, deep shadows, detailed realistic skin texture, shot on 85mm "
                       "lens, shallow depth of field, film grain, dark fantasy"),
    "photoreal": ("photorealistic, natural realistic lighting, detailed realistic skin "
                  "texture, sharp focus, high dynamic range, 50mm photo"),
    "oil": ("dark fantasy oil painting, classical portrait, dramatic chiaroscuro, visible "
            "textured brush strokes, muted somber palette, old master painting"),
    "gritty": ("gritty grimdark realism, harsh dramatic lighting, dirt and grime, weathered, "
               "desaturated cold palette, cinematic, highly detailed, film grain"),
    "anime": ("anime style, cel shaded, vibrant detailed anime key visual, dramatic anime "
              "lighting, dynamic composition, cinematic anime, highly detailed"),
    "none": "",
}


def style_keywords(style_key: str) -> str:
    return STYLE_KEYWORDS.get(style_key or "", STYLE_KEYWORDS["cinematic_dark"])


def _character_briefs(campanha, limit=20):
    """Nomes dos personagens da campanha (V2 + V1) pra ancorar coerência."""
    from gurps.models import CharacterSheet, CharacterSheetV2  # noqa: WPS433

    names = []
    for c in CharacterSheetV2.objects.filter(campanha=campanha).order_by("-id")[:limit]:
        nm = (c.nome_personagem or "").strip()
        if nm:
            names.append(nm)
    for c in CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome
    ).order_by("-id")[:limit]:
        nm = (c.nome_personagem or "").strip()
        if nm and nm not in names:
            names.append(nm)
    return names[:limit]


def build_campaign_context(campanha, max_assets=15) -> str:
    """Monta o texto de contexto do journal pra alimentar a geração."""
    from gurps.models import CampanhaAssets  # noqa: WPS433

    parts = []
    if campanha.descricao:
        parts.append("## Descrição da campanha\n" + campanha.descricao.strip()[:2500])
    if campanha.regras:
        parts.append("## Regras / tom\n" + campanha.regras.strip()[:1500])

    acc = (getattr(campanha, "ai_context", "") or "").strip()
    if acc:
        parts.append("## Contexto acumulado (itens aprovados)\n" + acc[-3000:])

    assets = (CampanhaAssets.objects.filter(campanha=campanha, slot__in=[1, 2])
              .order_by("-id")[:max_assets])
    asset_lines = []
    for a in assets:
        d = (a.description or "").strip()
        asset_lines.append(f"- {a.name}: {d[:160]}" if d else f"- {a.name}")
    if asset_lines:
        parts.append("## Elementos já no journal\n" + "\n".join(asset_lines))

    chars = _character_briefs(campanha)
    if chars:
        parts.append("## Personagens da campanha\n" + ", ".join(chars))

    return "\n\n".join(parts).strip()[:MAX_CONTEXT_CHARS]


def append_approved_context(campanha, line: str) -> None:
    """Acumula uma linha do que foi aprovado em `Campanha.ai_context` (capado)."""
    line = (line or "").strip().replace("\n", " ")
    if not line:
        return
    cur = (getattr(campanha, "ai_context", "") or "").strip()
    new = (cur + "\n- " + line).strip() if cur else ("- " + line)
    # Mantém só o fim (itens mais recentes) se estourar o teto.
    if len(new) > MAX_AI_CONTEXT_CHARS:
        new = new[-MAX_AI_CONTEXT_CHARS:]
    campanha.ai_context = new
    try:
        campanha.save(update_fields=["ai_context"])
    except Exception:  # noqa: BLE001  (campo pode não existir antes da migration)
        campanha.save()


_KIND_HINT = {
    "personagem": ("a character illustration — use EXACTLY the camera framing the GM asks "
                   "for (full body head-to-toe, full figure, waist-up, or face portrait). "
                   "If the GM asks for full body / corpo inteiro, show the ENTIRE body from "
                   "head to feet. Do NOT default to a face-only headshot"),
    "mapa": "a top-down tabletop battle map",
    "cena": "an environment / scene illustration",
    "capa": ("a dramatic cinematic POSTER / title-card background (wide establishing shot, "
             "strong focal subject, cinematic composition, leave calm negative space at the "
             "top or bottom for a title to be added later — do NOT draw any text or letters)"),
    "item": "a single object / item on a simple backdrop, product-shot style",
}


# Enquadramento da câmera (palavras-chave reforçadas que o modelo obedece bem).
FRAMING_KEYWORDS = {
    "portrait": "(tight portrait, head and shoulders, face in sharp focus:1.3)",
    "fullbody": "(full body shot, head to toe, entire body visible, full figure standing:1.4)",
    "action": "(dynamic action shot, the character actively doing the action, full body "
              "in motion, medium-wide cinematic shot showing the whole scene:1.3)",
}
# Descrição em inglês do enquadramento pra instruir o claude.
FRAMING_HINT = {
    "portrait": "a tight PORTRAIT — head and shoulders, face in focus.",
    "fullbody": "a FULL BODY shot — show the ENTIRE body from head to feet, full figure.",
    "action": "an ACTION shot — the character actively DOING what the GM describes, "
              "full body in motion, medium-to-wide cinematic framing of the whole scene.",
}


def framing_prefix(framing):
    """Palavras-chave de enquadramento pra colar no início de um prompt verbatim/mecânico."""
    return FRAMING_KEYWORDS.get(framing or "", "")


def _echo_phrases():
    """Frases de estilo/enquadramento/sufixos que podem ter sido coladas de um
    prompt anterior e que NÃO devem acumular."""
    phrases = [v for v in STYLE_KEYWORDS.values() if v]
    phrases += list(FRAMING_KEYWORDS.values())
    phrases += [
        "highly detailed, sharp focus, professional photography, masterpiece",
        "highly detailed, sharp focus, high dynamic range, 50mm photo",
        "natural realistic lighting, detailed realistic skin texture, sharp focus, "
        "high dynamic range, 50mm photo",
    ]
    return phrases


def strip_prompt_echo(text):
    """Remove blocos de estilo/enquadramento que o GM possa ter colado de um prompt
    anterior — evita o estilo repetir (×2, ×3...) ao colar/regerar. Mantém o resto
    do texto do GM intacto."""
    if not text:
        return text
    s = text
    for ph in _echo_phrases():
        s = re.sub(re.escape(ph), " ", s, flags=re.IGNORECASE)
    # colapsa vírgulas/espaços redundantes deixados pela remoção
    s = re.sub(r"(\s*,\s*){2,}", ", ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip(" ,\n\t")


def _mechanical_prompt(user_request, style_key, kind):
    """Fallback sem claude: cola as palavras-chave do estilo + enquadramento."""
    user_request = strip_prompt_echo(user_request)
    style = style_keywords(style_key)
    base = (style + ", " + user_request) if style else user_request
    if kind == "personagem":
        return f"{base}, highly detailed, sharp focus, professional photography, masterpiece"
    if kind in ("mapa", "cena"):
        return f"top-down tabletop RPG battle map, {base}, highly detailed, masterpiece"
    return base


def write_image_prompt_via_claude(context, user_request, style_key, kind,
                                  claude_bin="claude", model="sonnet",
                                  timeout=90, allow_all=False, framing="") -> tuple[str, bool]:
    """Pede ao `claude -p` um prompt de imagem coerente com o journal.

    Retorna (prompt, usou_claude). Cai no fallback mecânico em qualquer erro.
    Com allow_all, instrui o claude a preservar os termos gráficos (gore,
    cicatrizes, ferimentos, olho cego) sem suavizar.
    """
    user_request = strip_prompt_echo(user_request)
    style = style_keywords(style_key)
    allow_line = ""
    if allow_all:
        allow_line = (
            "\nThis is mature/adult tabletop fiction for ADULT characters. Keep EVERY detail "
            "from the GM request EXACTLY as asked — graphic, violent, gory, injury, scar, "
            "blind-eye, wound, disfigurement AND nudity/nakedness. Do NOT soften, sanitize, "
            "tone down, censor, clothe, or omit anything. If the GM asks for a nude/naked "
            "figure, describe the character fully nude (do NOT add clothing). Translate the "
            "request faithfully and keep its exact framing (full body head-to-toe, etc.). "
            "Emphasize key terms with weight like (milky blind eye:1.4), (full body nude:1.3), "
            "(huge scar across the face:1.5).")
    framing_line = ""
    if framing and FRAMING_HINT.get(framing):
        framing_line = f"\nCAMERA FRAMING (MANDATORY): frame the shot as {FRAMING_HINT[framing]}"
    instruction = f"""You write prompts for an SDXL image generator used in a tabletop RPG.
Turn the GM's short request into a single-line English image prompt: comma-separated visual descriptors, 40-70 words.

Depict EXACTLY what the GM asks for. Do NOT default to a human/character unless the request is clearly about a person. If the request is an object, place, scene, symbol, map or title card, depict that — not a person.
This image is {_KIND_HINT.get(kind, 'an illustration')}.
Make it visually CONSISTENT with the established world below (same era, tone, palette, materials, lighting).
Desired visual style to bake in: {style or 'realistic, cinematic'}.{framing_line}{allow_line}

OBEY THE DETAILS LITERALLY. The model tends to drift — fight it:
- Clothing: render EXACTLY the garments asked, weighted, e.g. (white tank top:1.3). Never leave the character shirtless/nude unless the GM explicitly asked for that.
- Weapons/objects: render the EXACT object asked, weighted and described by shape so it is not confused for a similar one, e.g. a cleaver = (a straight rectangular kitchen cleaver, flat broad blade:1.4) — NOT a sword. Keep each object as a SEPARATE item properly held in a hand (never fused to the hand/arm).
- Keep the GM's count: if one weapon in one hand, do not add extra weapons.
- Weight any injury/scar/eye the GM asks for, concretely, e.g. (left eye blind, milky white clouded dead eye with no pupil:1.6), (deep raised scar cutting vertically through the eye:1.6).

=== CAMPAIGN JOURNAL (context) ===
{context or '(no extra context yet)'}

=== GM REQUEST ===
{user_request}

Output EXACTLY two lines and nothing else (no preamble, no quotes, no markdown):
PROMPT: <the single-line image prompt>
NEGATIVE: <comma-separated things to AVOID that would contradict the request — above all the WRONG versions of the clothing, weapons and body the GM specified (tank top requested -> add: shirtless, bare chest, topless; cleaver requested -> add: sword, scimitar, curved blade, katana, machete; one weapon -> add: extra weapons, duplicate weapon; weapon fused to hand -> add: weapon merged with hand, extra fingers). Do NOT put scars, blindness, gore, nudity or the requested clothing/weapon in NEGATIVE. Keep it under 20 words.>"""

    resolved = shutil.which(claude_bin) or claude_bin
    cmd = [resolved, "-p", "--allowedTools", ""]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            cwd=tempfile.gettempdir(),  # neutro: não carrega CLAUDE.md do projeto
        )
    except FileNotFoundError:
        return _mechanical_prompt(user_request, style_key, kind), False, ""

    box = {}

    def _run():
        try:
            box["out"], box["err"] = proc.communicate(input=instruction)
        except Exception as exc:  # noqa: BLE001
            box["exc"] = exc

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    start = time.monotonic()
    while th.is_alive():
        if time.monotonic() - start > timeout:
            proc.kill()
            th.join(timeout=5)
            return _mechanical_prompt(user_request, style_key, kind), False, ""
        time.sleep(1)
    th.join()

    if box.get("exc"):
        return _mechanical_prompt(user_request, style_key, kind), False, ""
    out = (box.get("out") or "").strip()
    prompt, auto_neg = _parse_prompt_and_negative(out)
    if len(prompt) < 10:
        return _mechanical_prompt(user_request, style_key, kind), False, ""
    return prompt[:1200], True, auto_neg[:500]


def _parse_prompt_and_negative(out):
    """Extrai (prompt, negative) da saída do claude no formato de duas linhas
    'PROMPT: ...' / 'NEGATIVE: ...'. Tolerante: se não houver marcadores, usa tudo
    como prompt (compatível com saídas antigas de uma linha só)."""
    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    prompt_parts, neg = [], ""
    seen_marker = False
    cur = "prompt"
    for ln in lines:
        low = ln.lower()
        if low.startswith("prompt:"):
            seen_marker = True
            cur = "prompt"
            ln = ln.split(":", 1)[1].strip()
        elif low.startswith("negative:"):
            seen_marker = True
            cur = "neg"
            ln = ln.split(":", 1)[1].strip()
        if cur == "neg":
            neg = (neg + " " + ln).strip()
        else:
            if ln:
                prompt_parts.append(ln)
    prompt = " ".join(prompt_parts).strip().strip('`"\' ').strip()
    neg = neg.strip().strip('`"\' ').strip()
    # Sem marcadores: a saída inteira é o prompt (nada de negativo).
    if not seen_marker:
        prompt = " ".join(lines).strip().strip('`"\' ').strip()
        neg = ""
    return prompt, neg


def _run_claude_text(instruction, claude_bin="claude", model="sonnet", timeout=120):
    """Roda `claude -p` com a instrução no stdin. Retorna (texto, ok)."""
    resolved = shutil.which(claude_bin) or claude_bin
    cmd = [resolved, "-p", "--allowedTools", ""]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", cwd=tempfile.gettempdir(),
        )
    except FileNotFoundError:
        return "", False
    box = {}

    def _run():
        try:
            box["out"], box["err"] = proc.communicate(input=instruction)
        except Exception as exc:  # noqa: BLE001
            box["exc"] = exc

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    start = time.monotonic()
    while th.is_alive():
        if time.monotonic() - start > timeout:
            proc.kill(); th.join(timeout=5)
            return "", False
        time.sleep(1)
    th.join()
    if box.get("exc"):
        return "", False
    return (box.get("out") or "").strip(), True


def _fallback_storyboard(user_request, style_key, target_seconds, seconds_per_shot=2):
    """Storyboard mecânico se o claude falhar: repete o pedido em N tomadas."""
    n = max(3, min(round(target_seconds / seconds_per_shot), 120))
    base = style_keywords(style_key)
    shot_prompt = (f"{base}, {user_request}" if base else user_request)
    shots = [{"prompt": shot_prompt, "seconds": seconds_per_shot} for _ in range(n)]
    return {"mood": "epic", "shots": shots}, False


def write_storyboard_via_claude(context, user_request, style_key, target_seconds,
                                available_images=None,
                                claude_bin="claude", model="sonnet", timeout=150):
    """Pede ao claude um STORYBOARD (várias tomadas) pra um vídeo anime coerente
    com o journal. Retorna (dict {mood, shots:[{prompt, seconds}]}, usou_claude).

    Cada 'prompt' é uma linha em inglês pronta pro AnimateDiff (estilo anime +
    descrição da tomada). Fallback mecânico em qualquer erro."""
    style = style_keywords(style_key) or "anime style, cinematic"
    seconds_per_shot = 2  # Modo Consistência: 1 clipe = 1 janela de 16 frames
    n_shots = max(3, min(round(target_seconds / seconds_per_shot), 120))
    images = [str(x) for x in (available_images or []) if x]
    if images:
        img_block = (
            "\nAVAILABLE CHARACTER IMAGES (use their EXACT names): "
            + ", ".join(images[:30])
            + "\nFor shots that feature a specific character, set that shot's \"image\" to the "
              "character's EXACT name from the list above, so the video uses that character's look. "
              "For wide/establishing/scenery shots with no single character, use \"image\": \"\".")
        img_field = ', "image": "<exact character image name from the list, or empty>"'
    else:
        img_block = ""
        img_field = ""
    instruction = f"""You are a storyboard director for a SHORT ANIME-STYLE recap/opening video of a tabletop RPG.
Produce a JSON storyboard of about {n_shots} shots that together last ~{target_seconds} seconds, telling what happened, CONSISTENT with the campaign world below (same era, tone, characters, palette).{img_block}

Output ONLY valid JSON, no markdown fences, no comments, shaped exactly:
{{"mood": "<one of: {', '.join(MOODS)}>", "shots": [{{"prompt": "<english anime image/motion prompt, comma-separated, 20-45 words, include 'anime style' and camera/motion>", "seconds": 2{img_field}}}, ...]}}

Each shot's prompt must bake in this visual style: {style}.
Vary the shots (different angles, moments, characters) so the montage feels like an anime episode opening.

=== CAMPAIGN JOURNAL (context) ===
{context or '(no extra context yet)'}

=== GM REQUEST (what happened) ===
{user_request}

Output only the JSON storyboard."""

    out, ok = _run_claude_text(instruction, claude_bin, model, timeout)
    if not ok or not out:
        return _fallback_storyboard(user_request, style_key, target_seconds, seconds_per_shot)
    # Extrai o JSON mesmo com texto em volta.
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        return _fallback_storyboard(user_request, style_key, target_seconds, seconds_per_shot)
    try:
        data = json.loads(m.group(0))
        shots = data.get("shots") or []
        clean = []
        for s in shots:
            p = (s.get("prompt") or "").strip()
            if not p:
                continue
            secs = s.get("seconds") or seconds_per_shot
            try:
                secs = max(1, min(int(secs), 2))
            except (TypeError, ValueError):
                secs = seconds_per_shot
            shot = {"prompt": p[:400], "seconds": secs}
            img = (s.get("image") or "").strip()
            if img:
                shot["image"] = img[:200]
            clean.append(shot)
        if not clean:
            return _fallback_storyboard(user_request, style_key, target_seconds, seconds_per_shot)
        mood = (data.get("mood") or "epic").strip().lower()
        if mood not in MOODS:
            mood = "epic"
        return {"mood": mood, "shots": clean[:40]}, True
    except Exception:  # noqa: BLE001
        return _fallback_storyboard(user_request, style_key, target_seconds, seconds_per_shot)


def write_beat_prompt_via_claude(context, project_request, prior_beats, this_prompt,
                                 correction="", style_key="anime", ref_name="",
                                 render_style="anime",
                                 claude_bin="claude", model="sonnet", timeout=120):
    """Escreve o prompt de UM beat (cena), de forma CUMULATIVA.

    `prior_beats` é a lista (em ordem) dos prompts expandidos dos beats anteriores,
    pra o claude manter coerência (mesmos personagens/look/paleta/continuidade).
    `this_prompt` é o que o GM ditou pra ESTE beat; `correction` é uma instrução
    opcional pra corrigir uma tentativa anterior. `ref_name` é o nome da imagem de
    referência do journal (personagem) se houver. `render_style` ("anime"|"realism")
    decide se o prompt pede ARTE de anime ou live-action FOTORREALISTA — sem isso o
    claude escreve "anime style" mesmo num projeto realista e briga com o checkpoint.
    Retorna (prompt, usou_claude); fallback mecânico em qualquer erro."""
    realism = (render_style or "").lower() == "realism"
    # Em realismo, ignora o preset anime de style_keywords: o "look" é fotorrealista.
    if realism:
        style = "photorealistic, cinematic, natural lighting, realistic film still"
        medium = "PHOTOREALISTIC LIVE-ACTION"
        look_token = "photorealistic"
        ban = (" Do NOT use the words 'anime', 'cartoon', 'cel shaded', 'illustration', "
               "'drawing' or 'stylized' — this is a live-action, photoreal video of real people.")
        final_word = "photorealistic"
    else:
        style = style_keywords(style_key) or "anime style, cinematic"
        medium = "ANIME-STYLE"
        look_token = "anime style"
        ban = ""
        final_word = "anime"
    prior = [str(p).strip() for p in (prior_beats or []) if str(p).strip()]
    if prior:
        prior_block = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(prior[-20:]))
        story_so_far = f"\n=== BEATS SO FAR (the video up to now, in order) ===\n{prior_block}\n"
    else:
        story_so_far = "\n(This is the FIRST beat of the video.)\n"
    ref_block = ""
    if ref_name:
        ref_block = (f"\nThis beat features the character \"{ref_name}\" — keep their established "
                     "appearance EXACTLY (face, hair, outfit, colors).")
    corr_block = ""
    if (correction or "").strip():
        corr_block = (f"\n=== CORRECTION (the previous attempt at THIS beat was wrong; fix it) ===\n"
                      f"{correction.strip()}\n")
    instruction = f"""You write ONE shot prompt for a single beat (scene) of a SHORT {medium} recap video of a tabletop RPG.
Output ONLY one single-line English image/motion prompt: comma-separated descriptors, 20-45 words, include '{look_token}' and a camera/motion cue. No preamble, no quotes, no markdown.{ban}

The beat must be VISUALLY CONSISTENT with the beats so far (same era, tone, palette, characters, continuity) and with the campaign world below.{ref_block}
Bake in this visual style: {style}.
{story_so_far}{corr_block}
=== CAMPAIGN JOURNAL (context) ===
{context or '(no extra context yet)'}

=== OVERALL VIDEO (what the GM wants the whole video to be) ===
{project_request or '(not specified)'}

=== THIS BEAT (what the GM dictated for this scene) ===
{this_prompt}

Now output only the final single-line {final_word} shot prompt for THIS beat."""

    out, ok = _run_claude_text(instruction, claude_bin, model, timeout)
    if not ok or not out:
        mech = (f"{style}, {this_prompt}" if style else this_prompt).strip()
        return mech[:400], False
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    prompt = " ".join(lines).strip().strip('`"\' ').strip()
    if len(prompt) < 10:
        mech = (f"{style}, {this_prompt}" if style else this_prompt).strip()
        return mech[:400], False
    return prompt[:400], True


def write_wan_motion_prompt(context, action_text, ref_name="", render_style="realism",
                            claude_bin="claude", model="sonnet", timeout=120):
    """Transforma a instrução do GM (PT) numa frase de MOVIMENTO em inglês pro Wan
    (imagem + texto -> vídeo com ação). O Wan parte da imagem como quadro 1 e
    OBEDECE o texto, então a frase precisa: (1) descrever a cena da imagem pra
    manter continuidade, (2) descrever a AÇÃO com verbos de movimento claros,
    (3) pedir que a identidade/aparência do personagem seja mantida.
    Retorna (prompt_en, usou_claude); fallback = o texto cru num scaffold inglês."""
    action_text = (action_text or "").strip()
    realism = (render_style or "").lower() != "anime"
    look = ("photorealistic, cinematic, realistic film, natural lighting"
            if realism else "anime style, cel shaded, cinematic")
    ref_block = (f" The main subject is \"{ref_name}\"; keep their exact face, hair, beard, "
                 "outfit and the background from the starting image." if ref_name else
                 " Keep the subject's exact appearance and the background from the starting image.")
    instruction = f"""You write ONE English video-motion prompt for an image-to-video model (Wan).
The video STARTS from a given still image and must ANIMATE the action described below while
keeping the SAME character and scene as the starting image.{ref_block}

Output ONLY one single line: comma-separated, 30-60 words. Describe (a) the scene/subject briefly
(so it matches the image), then (b) the ACTION as clear motion with verbs (what moves, how), then
(c) style cues. Bake in: {look}, smooth natural motion, consistent character, detailed.
No preamble, no quotes, no markdown.

=== CAMPAIGN CONTEXT (optional) ===
{context or '(none)'}

=== THE ACTION THE GM WANTS (translate to English, make it concrete motion) ===
{action_text or '(subtle motion, the subject breathes and the camera slowly pushes in)'}

Now output only the final single-line English motion prompt."""
    out, ok = _run_claude_text(instruction, claude_bin, model, timeout)
    if not ok or not out:
        mech = f"{action_text}, {look}, smooth natural motion, consistent character, detailed"
        return mech.strip()[:500], False
    prompt = " ".join(ln.strip() for ln in out.splitlines() if ln.strip()).strip('`"\' ').strip()
    if len(prompt) < 10:
        mech = f"{action_text}, {look}, smooth natural motion, consistent character, detailed"
        return mech.strip()[:500], False
    return prompt[:500], True


def write_kontext_edit_prompt(edit_text, ref_name="", render_style="realism",
                              claude_bin="claude", model="sonnet", timeout=120):
    """Transforma a instrução do GM (PT) numa frase de EDIÇÃO ADITIVA em inglês pro
    Flux Kontext. A edição deve SOMAR o que o GM pediu (acender os olhos, pôr magia
    na mão) e MANTER todo o resto (rosto, pose, roupa, fundo) idêntico — por isso a
    frase sempre reforça "keep ... exactly the same". Edita a imagem parada (não é
    movimento). Retorna (prompt_en, usou_claude); fallback = scaffold com o texto cru."""
    edit_text = (edit_text or "").strip()
    realism = (render_style or "").lower() != "anime"
    look = "photorealistic, cinematic dramatic lighting, highly detailed" if realism \
        else "anime style, cel shaded, cinematic, highly detailed"
    keep = (f"Keep {ref_name}'s face, identity, hairstyle, outfit, pose and the background "
            "exactly the same" if ref_name else
            "Keep the face, identity, pose, outfit and the background exactly the same")
    instruction = f"""You write ONE English image-EDIT instruction for Flux Kontext (an additive
image editor). The edit must ADD ONLY what is asked and leave everything else identical — do NOT
redraw the character. Start with the change to add, then the "keep ... the same" clause.

Output ONLY one single line, 20-45 words, no quotes, no markdown, no preamble.

=== THE EDIT THE GM WANTS (translate to English, keep it additive) ===
{edit_text or '(make the eyes glow and add a subtle magical aura to the hands)'}

Now output only the final single-line English edit instruction, ending with: {keep}, {look}."""
    out, ok = _run_claude_text(instruction, claude_bin, model, timeout)
    if not ok or not out:
        mech = f"Add: {edit_text}. {keep}, {look}."
        return mech.strip()[:500], False
    prompt = " ".join(ln.strip() for ln in out.splitlines() if ln.strip()).strip('`"\' ').strip()
    if len(prompt) < 10:
        mech = f"Add: {edit_text}. {keep}, {look}."
        return mech.strip()[:500], False
    return prompt[:500], True
