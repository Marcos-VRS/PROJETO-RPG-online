"""Worker do Estúdio de Imagem (ComfyUI local, GPU do host).

Pega os pedidos ``pending`` de ImageGenRequest, chama o ComfyUI pra gerar o PNG,
salva em media/imagegen/ e marca ``done`` (ou ``failed``). Não depende do resto
do app — se o ComfyUI não estiver de pé, os pedidos expiram por timeout.

Uso:
    python manage.py imagegen_worker              # loop contínuo
    python manage.py imagegen_worker --once       # processa 1 e sai (teste)
    python manage.py imagegen_worker --url http://127.0.0.1:8188
"""
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from gurps import ai_context, comfyui_client
from gurps.models import ImageGenRequest


class Command(BaseCommand):
    help = "Worker de geração de imagem (ComfyUI): pega pending e gera PNG."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=3.0)
        parser.add_argument("--url", default=comfyui_client.DEFAULT_URL)
        parser.add_argument("--ckpt", default=comfyui_client.DEFAULT_CKPT)
        parser.add_argument("--timeout", type=int, default=300)
        parser.add_argument("--claude", default="claude",
                            help="executável do claude (pra escrever prompts a partir do journal)")
        parser.add_argument("--model", default="sonnet",
                            help="modelo do claude pros prompts (sonnet é rápido)")
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **opts):
        base_url = opts["url"]
        ckpt = opts["ckpt"]
        gen_timeout = opts["timeout"]
        once = opts["once"]
        interval = opts["interval"]
        self.claude_bin = opts.get("claude") or "claude"
        self.claude_model = (opts.get("model") or "").strip()

        st = comfyui_client.status(base_url)
        # Resolve o melhor checkpoint disponível (RealVisXL se já baixou, senão turbo).
        if st.get("online"):
            ckpt = comfyui_client.pick_checkpoint(ckpt, base_url)
        self.stdout.write(self.style.SUCCESS(
            f"imagegen_worker iniciado (comfyui={base_url}, online={st.get('online')}, "
            f"gpu={st.get('device')}, ckpt={ckpt}). Ctrl+C pra parar."))
        try:
            while True:
                req = (ImageGenRequest.objects.filter(status="pending")
                       .order_by("created_at").first())
                if req is None:
                    if once:
                        break
                    time.sleep(interval)
                    continue
                self._process(req, base_url, ckpt, gen_timeout)
                if once:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\nimagegen_worker parado.")

    def _resolve_ref(self, req):
        """Bytes da imagem de referência (IP-Adapter): asset do journal escolhido
        pelo GM tem prioridade; senão o upload manual. (None, nome) se não houver."""
        # 1) asset do journal (só raster — IP-Adapter não lê SVG)
        if (req.ref_asset_id and req.ref_asset and req.ref_asset.image
                and not req.ref_asset.image.name.lower().endswith(".svg")):
            try:
                req.ref_asset.image.open("rb")
                data = req.ref_asset.image.read()
                req.ref_asset.image.close()
                name = os.path.basename(req.ref_asset.image.name) or "ref.png"
                self.stdout.write(f"  -> referência do journal: {req.ref_asset.name} (peso {req.ref_weight})")
                return data, name
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  -> ref do journal ignorada: {e}"))
        # 2) upload manual
        if req.ref_image:
            try:
                req.ref_image.open("rb")
                data = req.ref_image.read()
                req.ref_image.close()
                name = os.path.basename(req.ref_image.name) or "ref.png"
                self.stdout.write(f"  -> referência enviada: {name} (peso {req.ref_weight})")
                return data, name
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  -> ref ignorada (erro ao ler): {e}"))
        return None, "ref.png"

    def _process(self, req, base_url, ckpt, gen_timeout):
        req.status = "processing"
        req.save(update_fields=["status", "updated_at"])
        # Re-resolve o checkpoint a cada pedido (o download do RealVisXL pode ter
        # terminado depois que o worker subiu).
        ckpt = comfyui_client.pick_checkpoint(ckpt, base_url)
        self.stdout.write(f"#{req.id} [{req.kind}] gerando ({ckpt}): {req.prompt[:50]!r} ...")

        # Monta o prompt. Com use_context, o claude -p LÊ O JOURNAL (descrição,
        # regras, contexto acumulado, assets, personagens) e escreve um prompt
        # coerente com o mundo. Sem contexto (ou se o claude falhar), cai no modo
        # mecânico (palavras-chave do estilo + enquadramento).
        used_claude = False
        if req.use_context:
            try:
                ctx = ai_context.build_campaign_context(req.campanha)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"  -> contexto falhou: {e}"))
                ctx = ""
            full_prompt, used_claude = ai_context.write_image_prompt_via_claude(
                ctx, req.prompt, req.style, req.kind,
                claude_bin=self.claude_bin, model=self.claude_model,
            )
        else:
            full_prompt = ai_context._mechanical_prompt(req.prompt, req.style, req.kind)

        # Guarda o prompt final pro GM ver o que foi realmente gerado.
        req.expanded_prompt = full_prompt
        req.save(update_fields=["expanded_prompt", "updated_at"])
        self.stdout.write(
            f"  -> prompt {'(claude/journal)' if used_claude else '(mecânico)'}: {full_prompt[:90]!r}")

        # Imagem de referência (IP-Adapter): preferência pro asset do journal
        # escolhido pelo GM; senão o upload manual.
        ref_bytes, ref_name = self._resolve_ref(req)

        try:
            png = comfyui_client.generate_png(
                prompt=full_prompt, width=req.width, height=req.height,
                steps=req.steps, cfg=req.cfg, seed=req.seed, ckpt=ckpt,
                base_url=base_url, timeout=gen_timeout,
                ref_image_bytes=ref_bytes, ref_image_filename=ref_name,
                ref_weight=req.ref_weight,
            )
        except Exception as e:  # noqa: BLE001
            req.status = "failed"
            req.error = str(e)[:500]
            req.save(update_fields=["status", "error", "updated_at"])
            self.stdout.write(self.style.ERROR(f"#{req.id} FALHOU: {req.error}"))
            return

        rel = f"imagegen/gen_{req.id}.png"
        full = os.path.join(settings.MEDIA_ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(png)

        req.result_file = rel
        req.status = "done"
        req.error = ""
        req.save(update_fields=["result_file", "status", "error", "updated_at"])
        self.stdout.write(self.style.SUCCESS(
            f"#{req.id} OK — {len(png)} bytes (aguardando aprovação)."))
