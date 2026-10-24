# Estúdio de Imagem por IA local (ComfyUI na GPU do mestre) — Plano técnico

> **Status:** planejamento aprovado (2026-09-12). Fundação (detecção) iniciada.
> **Objetivo:** ferramenta poderosa de geração de imagem **para tudo** — retratos de personagem (artísticos, com controle de estética e consistência) **e** mapas (raster, com controle geométrico) — rodando na **GPU de quem estiver mestrando**, offline/local.

## Decisões cravadas (user, 2026-09-12)

1. **Motor = ComfyUI local** (não embutido no `.exe` — modelos têm GB + CUDA). Roda como serviço separado expondo API HTTP em `http://127.0.0.1:8188` na máquina host; o app conversa via localhost (mesmo padrão do worker de mapas).
2. **Instalação = "Conectar"** (por ora): o mestre instala o ComfyUI uma vez (guia próprio); o app **detecta** e usa. Empacotar (auto-download portátil + modelo) fica pra depois.
3. **Modelo v1 = SDXL / SDXL-Lightning** — cabe nos 6 GB da RTX 1000 Ada do user (~20-60s/img). FLUX = "modo qualidade" opcional pra GPUs ≥12 GB (lento em 6 GB).
4. **1ª fatia = painel genérico servindo personagem E mapa** (kind unificado).
5. **Degradação graciosa:** ComfyUI offline → "gerador de imagem offline" (não quebra o serviço), igual ao map-gen.

## GPU de referência (do user)
RTX 1000 Ada Laptop, **6 GB VRAM**, compute 8.9 (bf16/fp8 ok), driver 596.36. → SDXL com `--lowvram`/`--medvram-sdxl`; Lightning/Turbo (4-8 passos) pra responsividade.

## Arquitetura (reaproveita ~80% do map-gen)
```
App (host) → painel "Estúdio de Imagem" (kind=personagem|mapa|cena; prompt; estilo/LoRA;
             imagem de referência; controlnet; tamanho)
   → worker monta um WORKFLOW ComfyUI e POST /prompt (localhost:8188) → roda na GPU do host
   → poll /history/<id> → baixa o PNG (/view) → salva como CampanhaAssets(show=False)
   → Aprovar/Descartar (fluxo existente) → vira avatar da ficha / fundo de cena
   → sem ComfyUI rodando → offline (graceful)
```
- **Generalizar `MapGenRequest` → pedido de geração unificado** (`kind`, `engine=comfyui`, `model`, `style`, `reference_asset_id`, `controlnet`, `width/height`, `steps/cfg/seed`). Reusar aprovação/asset.
- **Detecção:** `gurps/comfyui_client.py` → `comfyui_status()` pinga `/system_stats` (online + device/VRAM).

## Controles de estética (onde mora o "poder/precisão")
- **Modelo/checkpoint + LoRAs** → estilo (realista, anime, óleo, dark fantasy…).
- **IP-Adapter / img2img** → **consistência de personagem** a partir de foto de referência.
- **ControlNet** → **geometria** (rascunho de layout → battlemap pintado; escala 1 hex ≈ 1 m).
- Tamanho/proporção, passos, CFG, seed (reprodutível).

## Fases
- **Fase 0 — Fundação (EM ANDAMENTO):** `comfyui_client.comfyui_status()` + endpoint `/imagegen/status/` (online/offline + GPU). Testável já (offline enquanto o ComfyUI não sobe).
- **Fase 1 — Geração básica SDXL (texto→imagem):** worker monta workflow SDXL mínimo, gera, salva, aprova. Painel com prompt + tamanho + estilo. Kind personagem e mapa.
- **Fase 2 — Estética:** presets de estilo/LoRA, proporção, passos; escolha de checkpoint.
- **Fase 3 — Consistência de personagem:** upload de referência → IP-Adapter.
- **Fase 4 — Mapas com ControlNet:** rascunho/layout → battlemap na escala; substitui/complementa o SVG (claude -p).
- **Fase 5 — Empacotar/auto-instalar** ComfyUI pra outros mestres.

## Dependência do usuário (pré-requisito da Fase 1)
Mestre instala **ComfyUI Portable (Windows)** + 1 checkpoint SDXL em `models/checkpoints/`, e sobe com a API em 8188 (`--lowvram` pra 6 GB). Guia detalhado passado ao user em 2026-09-12.

## Relação com o map-gen atual (claude -p / SVG)
O map-gen SVG (Fases 1-4 de `MAP_GEN_PLAN.md`) continua como fallback leve. Mapas "impressionantes" passam a vir do ComfyUI (raster + ControlNet). O fluxo de fila/aprovação é compartilhado.
