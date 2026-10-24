"""Worker de geração de mapas por IA (Claude headless).

Roda na MÁQUINA HOST (o PC que hospeda o app + túnel). Faz heartbeat, pega os
pedidos ``pending`` da fila (``MapGenRequest``), dispara ``claude -p`` com um
prompt-template pra gerar um SVG de battle map na escala do tabletop, e marca
``done`` (ou ``failed``). Não depende do resto do app — se este worker não
estiver rodando, os pedidos expiram por timeout (o serviço nunca quebra).

Uso:
    python manage.py mapgen_worker                # loop contínuo
    python manage.py mapgen_worker --once         # processa 1 pedido e sai (teste)
    python manage.py mapgen_worker --interval 4   # intervalo do poll (s)

Requer o CLI ``claude`` instalado e logado no host (mesma assinatura, sem custo
de API separado).
"""
import re
import shutil
import subprocess
import tempfile
import threading
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from gurps import ai_context
from gurps.models import GenWorkerStatus, MapGenRequest

# Extrai o <svg>...</svg> mesmo que o modelo cuspa texto extra em volta.
_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.DOTALL | re.IGNORECASE)

PROMPT_TEMPLATE = """You are a top-down RPG battle-map generator. Output ONLY a single self-contained SVG. No markdown fences, no explanation, no text before or after — just <svg ...>...</svg>.

Requirements:
- Top-down (bird's-eye) tactical battle map for a tabletop RPG.
- Scale: {grid} pixels = 1 meter. Cap the map at ABOUT 20x15 meters no matter what the request says; set viewBox and width/height accordingly.
- BE EFFICIENT AND FAST: produce a clean, moderate SVG (target ~150-400 shapes MAX). Use simple vector shapes and a few patterns/gradients. Do NOT emit thousands of tiny elements or huge repeated path data — it must render quickly and generate fast.
- Style: clean cartographic / medieval-fantasy, readable at a glance. Draw walls, floors, doors, furniture, terrain, water as relevant to the scene.
- Self-contained: inline all styles; NO external images, fonts, or scripts.
- Do NOT draw a hex or square grid overlay — the app renders its own grid on top.

Scene to draw: {prompt}
"""


class Command(BaseCommand):
    help = "Worker de geração de mapas (Claude headless): pega pending e gera SVG."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=4.0,
                            help="segundos entre polls quando a fila está vazia")
        parser.add_argument("--claude", default="claude",
                            help="caminho/nome do executável claude")
        parser.add_argument("--model", default="sonnet",
                            help="modelo do claude (sonnet é rápido; opus é lento). Vazio = default da sessão.")
        parser.add_argument("--timeout", type=int, default=300,
                            help="timeout (s) por geração")
        parser.add_argument("--once", action="store_true",
                            help="processa 1 pedido e sai (útil pra teste)")

    def handle(self, *args, **opts):
        interval = opts["interval"]
        gen_timeout = opts["timeout"]
        once = opts["once"]
        model = (opts.get("model") or "").strip()

        # Resolve o executável (no Windows o npm instala `claude.CMD`, que o
        # subprocess não acha via PATHEXT — shutil.which resolve o caminho real).
        claude_bin = shutil.which(opts["claude"]) or opts["claude"]

        self.stdout.write(self.style.SUCCESS(
            f"mapgen_worker iniciado (claude={claude_bin}, model={model or 'default'}, "
            f"timeout={gen_timeout}s). Ctrl+C pra parar."))
        try:
            while True:
                GenWorkerStatus.beat()
                req = (MapGenRequest.objects.filter(status="pending")
                       .order_by("created_at").first())
                if req is None:
                    if once:
                        self.stdout.write("fila vazia; --once, saindo.")
                        break
                    time.sleep(interval)
                    continue
                self._process(req, claude_bin, gen_timeout, model)
                if once:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\nmapgen_worker parado.")

    def _process(self, req, claude_bin, gen_timeout, model=""):
        req.status = "processing"
        req.save(update_fields=["status", "updated_at"])
        self.stdout.write(f"#{req.id} gerando: {req.prompt[:60]!r} ...")

        # Injeta o contexto do journal pra o mapa combinar com o mundo da campanha.
        scene = req.prompt
        try:
            ctx = ai_context.build_campaign_context(req.campanha)
        except Exception:  # noqa: BLE001
            ctx = ""
        if ctx:
            scene = (f"{req.prompt}\n\nKeep it consistent with this campaign world "
                     f"(era, materials, mood):\n{ctx[:1500]}")
        prompt = PROMPT_TEMPLATE.format(grid=req.grid_size_px or 64, prompt=scene)
        cmd = [claude_bin, "-p", "--allowedTools", ""]
        if model:
            cmd += ["--model", model]
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                # cwd NEUTRO: fora do projeto pra o claude NÃO carregar o CLAUDE.md
                # (senão vira "assistente do projeto" e responde conversando).
                cwd=tempfile.gettempdir(),
            )
        except FileNotFoundError:
            self._fail(req, f"CLI '{claude_bin}' não encontrado no host.")
            return

        # A geração roda numa thread: communicate() escreve o prompt no stdin e
        # lê stdout/stderr sem deadlock de pipe. A main loop mantém o heartbeat
        # fresco (geração passa de 45s; sem isso o status marcaria failed).
        box = {}

        def _run():
            try:
                box["out"], box["err"] = proc.communicate(input=prompt)
            except Exception as exc:  # noqa: BLE001
                box["exc"] = exc

        th = threading.Thread(target=_run, daemon=True)
        th.start()
        start = time.monotonic()
        while th.is_alive():
            GenWorkerStatus.beat()
            if time.monotonic() - start > gen_timeout:
                proc.kill()
                th.join(timeout=5)
                self._fail(req, "timeout na geração")
                return
            time.sleep(3)
        th.join()

        if box.get("exc"):
            self._fail(req, f"erro ao rodar claude: {box['exc']}")
            return
        out = box.get("out") or ""
        err = box.get("err") or ""
        match = _SVG_RE.search(out)
        if not match:
            self._fail(req, "saída sem SVG. " + (err or out)[:500])
            return

        req.result_svg = match.group(0)
        req.status = "done"
        req.error = ""
        req.save(update_fields=["result_svg", "status", "error", "updated_at"])
        self.stdout.write(self.style.SUCCESS(
            f"#{req.id} OK — {len(req.result_svg)} bytes de SVG (aguardando aprovação)."))

    def _fail(self, req, msg):
        req.status = "failed"
        req.error = msg
        req.save(update_fields=["status", "error", "updated_at"])
        self.stdout.write(self.style.ERROR(f"#{req.id} FALHOU: {msg}"))
