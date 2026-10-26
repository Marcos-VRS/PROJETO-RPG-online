# Claude Code — Contexto do projeto roll3d6 RPG

Este arquivo é carregado automaticamente em toda conversa deste repositório. Ele serve de índice para os documentos detalhados em `docs/`, que devem ser lidos conforme a tarefa exigir.

## Pivô em andamento (decidido 2026-05-14)

O produto migra de **SaaS hospedado no GCP** para **aplicativo desktop com dois cliques** (Windows). SQLite no lugar de Postgres, in-memory channel layer no lugar de Redis, Cloudflare Quick Tunnel para o multiplayer. SaaS GCP entra em sunset gradual. Detalhes em [`docs/AGENT_PROMPT.md`](docs/AGENT_PROMPT.md) e [`docs/DESKTOP_DISTRIBUTION.md`](docs/DESKTOP_DISTRIBUTION.md).

## Documentos

- [Estado da sessão — última parada e plano de continuação](docs/SESSION_STATE.md) — **leia primeiro ao retomar**
- [Prompt do agente — missão, papel, stack, responsabilidades](docs/AGENT_PROMPT.md)
- [Arquitetura de distribuição desktop — instalador, launcher, túnel, empacotamento](docs/DESKTOP_DISTRIBUTION.md)
- [Arquitetura RAG — em hibernação até voltar com vector store SQLite-friendly](docs/RAG_ARCHITECTURE.md)
- [Base de conhecimento GURPS 4e — visão geral + plano de catalogação](docs/GURPS_KNOWLEDGE.md)

### V2 (refatoração — fundação F-1 estrutural mergeada)
- [Estado da Execução V2 — onde paramos](docs/V2_EXECUTION_STATE.md)
- [Prompt do Arquiteto V2 — produto, decisões, restrições](docs/PLATFORM_V2_PROMPT.md)
- [Plano de Execução V2 — fases F-0 → F-11 com passo a passo](docs/PLATFORM_V2_EXECUTION_PLAN.md)
- [Blueprint reutilizável do chatbot RAG](docs/CHATBOT_BLUEPRINT.md)
- [Atributos e características secundárias](docs/gurps/attributes.md) — dados em `gurps/data/attributes.json`

### Tabletop map system (planejamento — 2026-05-24)

- [Plano técnico do tabletop](docs/TABLETOP_MAP_PLAN.md) — arquitetura, modelo de dados, WS protocol, fases
- [Regras GURPS aplicadas ao mapa](docs/GURPS_TABLETOP_RULES.md) — hex, facing, reach, manobras, status effects
- [Fluxo de combate passo a passo](docs/TABLETOP_COMBAT_FLOW.md) — setup → turno → ataque → defesa → dano
- [Conversões de unidades](docs/UNIT_CONVERSIONS.md) — yard=m (fixed 1:1), lb→kg, helpers Py/JS
- [Ficha V3 — roadmap](docs/FICHA_V3_ROADMAP.md) — placeholder, só depois do tabletop estar funcional
- [Geração de mapas por IA](docs/MAP_GEN_PLAN.md) — GM manda prompt → Claude headless gera SVG na escala → aprovação → asset (feature aprovada 2026-08-09, em implementação)
  - **Catálogos JSON estruturados** em `gurps/data/`:
    - `attributes.json` — ST/DX/IQ/HT + características secundárias + tabela de dano + encumbrance
    - `advantages.json` — 246 vantagens (Basic Set + Powers cap 2)
    - `disadvantages.json` — 179 desvantagens
    - `modifiers.json` — 100 modifiers (57 enhancements + 43 limitations, Basic Set + Powers)
    - `skills.json` — 223 perícias (metadata, descrições sob demanda)
    - `spells.json` — 63 spells por colégio (metadata)
    - `equipment.json` — 67 items core (melee/ranged/armaduras/escudos) + cost of living
    - `templates.json` — meta-traits + character/racial templates samples
    - `combat_tables.json` — 20 maneuvers + 11 damage types + 11 hit locations + defenses/posture/encumbrance/morte/recuperação
    - `diseases_poisons.json` — 12 diseases + 12 poisons + 12 environmental hazards (cap 14 Campaigns)
    - `bestiary.json` — 20 animais/monstros com stat blocks (cap 16 Campaigns)
    - `technology.json` — 13 Tech Levels + 20 artifacts samples (cap 17 Campaigns)
    - `sample_powers.json` — 40 sample powers do livro Powers cap 3
    - `reference_tables.json` — Reaction Table, Size/Speed/Range, Fright Check, Standard Modifiers, Aging
  - **Documentos de regras** em `docs/gurps/`:
    - [Atributos](docs/gurps/attributes.md), [Combate](docs/gurps/combat.md), [Combate tático](docs/gurps/combat_tactical.md), [Injuries/Diseases](docs/gurps/injuries.md)
    - [Success Rolls](docs/gurps/success_rolls.md), [GM Tools / Game Worlds](docs/gurps/gm_tools.md), [Template Creation](docs/gurps/template_creation.md), [Infinite Worlds (setting)](docs/gurps/infinite_worlds.md)
    - [Psionics](docs/gurps/psionics.md), [Character Development](docs/gurps/character_development.md)
    - [Powers — overview](docs/gurps/powers_overview.md), [Building Powers (cap 1)](docs/gurps/powers_building.md), [Powers in Play (caps 4-6)](docs/gurps/powers_in_play.md)

**Cobertura final dos 3 livros (2026-05-16):**
- **Basic Set: Characters** (338 pp): Caps 1-9 + apêndices catalogados. Skills/Spells em `list_only`. Quirks pendentes.
- **Basic Set: Campaigns** (242 pp): Caps 10-20 + Tables. Bestiary/Tech samples; expansion futura para listas completas.
- **Powers** (243 pp): 6 capítulos resumidos; new advantages + modifiers + sample powers em JSON. Examples cap 3 completos.

Pendências menores documentadas em `docs/GURPS_KNOWLEDGE.md`. Catalogação executada em sessão única.

## Regras invioláveis

Resumo rápido — detalhes em `docs/AGENT_PROMPT.md`:

1. **Nunca altere models removendo campos ou informação.** Fichas existentes precisam migrar intactas do GCP para o SQLite do desktop. Migrações são aditivas ou transformadoras, nunca destrutivas.
2. **Não recomece do zero.** Evolua o código existente.
3. **Mudanças estruturais exigem confirmação do usuário** antes da implementação (troca de banco, framework JS pesado, troca de empacotamento, novo serviço externo).
4. **Sem dependência de Python/Postgres/Redis pré-instalados no usuário final.** O instalador entrega tudo bundleado, dois cliques, zero terminal.
5. **Priorize desempenho e baixo consumo de dados.** O app roda na máquina do usuário; banda do Cloudflare Tunnel tem limites.
6. **Trabalho por partes.** Conclua e valide uma etapa antes de avançar.
7. **Mantenha os docs atualizados.** Quando uma diretriz mudar, atualize o arquivo `.md` correspondente em vez de criar um novo.

## Comunicação

- Idioma: português (pt-BR).
- Usuário opera em Windows 11 + PowerShell; comandos sugeridos devem ser compatíveis.
- Sandbox do Claude Code não consegue elevar UAC — ações que exigem admin são instruídas ao usuário.
