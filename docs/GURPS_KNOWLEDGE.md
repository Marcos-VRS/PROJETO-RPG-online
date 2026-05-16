# Base de conhecimento GURPS 4ª Edição

> Documento vivo. Atualizar conforme o conhecimento for sendo extraído dos PDFs em `books/`. Objetivo final: servir como (1) referência para o agente tomar decisões informadas, (2) fonte de dados/validação para features (autocomplete, validação de ficha, cálculos automáticos), sem alterar o schema atual do `CharacterSheet`.

---

## O que é GURPS

GURPS (*Generic Universal RolePlaying System*) é um sistema de RPG de mesa **universal** e **genérico** da Steve Jackson Games, publicado em sua 4ª Edição em 2004. Diferentemente de sistemas amarrados a um cenário (D&D → fantasia medieval, Vampiro → horror gótico), GURPS fornece um conjunto de regras aplicável a qualquer gênero: fantasia, ficção científica, horror, histórico, moderno, super-heróis.

### Características centrais do sistema

1. **Baseado em 3d6** — quase toda rolagem é `3d6`, buscando valor **menor ou igual** a um atributo/skill. Resultado em sino (média 10,5) dá probabilidades estáveis e previsíveis.
2. **Compra de personagem por pontos** — jogadores têm um orçamento (ex: 100, 150, 250 pts) para distribuir entre atributos, vantagens, skills. Desvantagens devolvem pontos (até um limite).
3. **Quatro atributos primários**: ST (Força), DX (Destreza), IQ (Inteligência), HT (Vigor). Cada um custa 10 pts por ponto acima de 10.
4. **Atributos secundários** derivados: HP, Will, Per, FP, Basic Speed, Basic Move, Dodge.
5. **Vantagens / Desvantagens** — traços que custam ou devolvem pontos. Podem ter **modificadores** (Enhancements aumentam custo, Limitations reduzem).
6. **Skills** — perícias com nível relativo a um atributo (ex: *Broadsword (DX/A)* custa mais conforme sobe).
7. **Combat** — baseado em turnos, com manobras (Attack, All-Out Attack, Defend, Feint…), ataques ativos e defesas (Parry, Block, Dodge).
8. **Dano** — calculado via thrust/swing baseado em ST, com tipos de dano (cortante, perfurante, esmagador, etc.) que interagem com armadura e locais do corpo.

### O papel do mestre (GM) e dos jogadores

- **GM** narra o mundo, arbitra regras, controla NPCs e ambiente. Precisa de: mapa dinâmico, tokens, chat, acesso às fichas dos jogadores, gerador de encontros/rolagens secretas.
- **Jogadores** controlam personagens. Precisam de: ficha editável dentro das regras, rolagem de dados, chat, visualização do mapa, inventário.

Isso mapeia diretamente nas features que o projeto precisa ter.

---

## Relação com o código atual

Em `gurps/models.py`, o `CharacterSheet` guarda praticamente toda a informação de GURPS como **`JSONField` livre**:

- `atributos`, `sub_attributes`
- `advantages`, `disadvantages`
- `skills`
- `equipment_melee`, `equipment_ranged`, `equipment_armor`
- `maneuvers_melee`, `maneuvers_ranged`, `maneuvers_defense`

**Consequência**: não há validação estrutural — uma vantagem inexistente, com custo errado ou nome grafado de outra forma é aceita. O catálogo construído neste documento (e artefatos derivados) é a base para adicionar validação sem alterar o schema.

Estratégia: **não migrar para tabelas relacionais agora** (mudança estrutural, exige aprovação; risco de perda de dados em produção). Em vez disso:

1. Construir o catálogo como **dados estáticos** (Markdown aqui + JSON/YAML em `gurps/data/` quando necessário).
2. Usar o catálogo para validação no save da ficha e autocomplete no front.
3. Se no futuro o usuário aprovar a migração para relacional, o catálogo já está pronto como fonte das tabelas.

---

## Livros disponíveis (em `docs/gurps/`, não commitados — gitignored)

| Livro | Conteúdo | Páginas PDF | Prioridade |
|---|---|---|---|
| `Gurps - Basic Set 4Th Characters.pdf` | Criação de personagens: atributos, vantagens, desvantagens, skills, modificadores, técnicas, templates, magic, equipment. **O mais importante para a ficha.** | 338 | Alta — primeiro |
| `SJG01-0002 - GURPS 4e - Basic Set - Campaigns (OEF).pdf` | Regras de jogo: combate, dano, ferimentos, movimento, GM tools, game worlds, Infinite Worlds setting. | 242 | Alta — segundo |
| `GURPS 4e - Powers.pdf` | Sistema de poderes (super-heróis, habilidades extraordinárias) — expansão de vantagens. | 243 | Média — após Basic Set |

### Mapa de capítulos — Basic Set: Characters (pp PDF)

| Cap | Tópico | pp PDF | Notas |
|---|---|---|---|
| Intro | Introduction | 5–9 | Não-mecânico |
| 1 | Creating a Character | 10–31 | Inclui Attributes (14–17), Build/SM (18–19), Age/Appearance (20–22), Social Background/TL/Language (22–24), Wealth/Status/Rank (25–30), Friends/Foes/Identities (31) |
| 2 | Advantages | 32–118 | List 34–100, Perks 100, Modifiers (Enhancements 102–109 / Limitations 110–116), New Advantages 117–118 |
| 3 | Disadvantages | 119–166 | List 122–161, Quirks 162–165 |
| 4 | Skills | 167–233 | List 174–226, Techniques 229–233, Wildcard Skills 175 |
| 5 | Magic | 234–253 | Sistema padrão de magia + Spell List por colégio |
| 6 | Psionics | 254–257 | Resumo (expandido no livro Psionic Powers) |
| 7 | Templates | 258–263 | Character Templates, Racial Templates, Meta-Traits |
| 8 | Equipment | 264–289 | Cost of Living, Weapons (melee/ranged/heavy), Armor, Shields |
| 9 | Character Development | 290–296 | Improvement, Body Modification, Mind Transfer |
| Apêndice | Trait Lists (índices) | 297–306 | Listas alfabéticas de Advantages/Disadvantages/Modifiers/Skills/Techniques/Spells |
| Apêndice | Iconic Characters (NPCs prontos) | 307–323 | Sample chars |
| Apêndice | Combat Lite (resumo) | 324–328 | Versão simplificada |
| Apêndice | Index | 329–334 | |
| Apêndice | Character Sheet (template) | 335 | |

### Mapa de capítulos — Basic Set: Campaigns (pp PDF)

| Cap | Tópico | pp PDF |
|---|---|---|
| Intro | Introduction | 7 |
| 10 | Success Rolls | 8–26 |
| 11 | Combat | 27–48 |
| 12 | Tactical Combat | 49–57 |
| 13 | Special Combat Situations | 58–82 |
| 14 | Injuries, Illness, and Fatigue | 83–109 |
| 15 | Creating Templates | 110–119 |
| 16 | Animals and Monsters | 120–126 |
| 17 | Technology and Artifacts | 127–150 |
| 18 | Game Mastering | 151–169 |
| 19 | Game Worlds | 170–187 |
| 20 | Infinite Worlds (setting) | 188–211 |
| Apêndice | Tables (referência rápida) | 212–227 |
| Apêndice | Glossary | 228 |
| Apêndice | Sheets & Index | 232–242 |

### Mapa de capítulos — Powers (pp PDF)

| Cap | Tópico | pp PDF |
|---|---|---|
| Intro | Introduction | 6 |
| 1 | Building Powers | 8–39 |
| 2 | Building Abilities (advantages + new modifiers) | 40–121 |
| 3 | Examples | 122–153 |
| 4 | Powers in Action | 154–180 |
| 5 | Power Games | 181–204 |
| 6 | Empowered Genres | 205–236 |

---

## Plano de catalogação — STATUS

Modo "Catalogar tudo de uma vez" aprovado pelo usuário em 2026-05-16 e executado nessa mesma sessão. Estado final dos catálogos abaixo.

### Bloco A — Criação de personagem (Characters book)

1. ✅ **Atributos** — `attributes.md` + `attributes.json` (pp 14–21)
2. ✅ **Vantagens** — `advantages.json` (240 entries cobrindo pp 32–100 + Talents pp 89–91 + Perks pp 100–101)
3. ✅ **Modificadores** — `modifiers.json` (47 enhancements + 33 limitations + 3 gadget limitations, pp 101–117)
4. ✅ **Desvantagens** — `disadvantages.json` (179 desvantagens, pp 119–166; Quirks p162-165 ainda como categoria separada se necessário)
5. ✅ **Skills** — `skills.json` (223 skills, pp 167–233, `detail_level: list_only` — descrições sob demanda)
6. ⚠️ **Traços físicos auxiliares** — pendente como `physical_traits.md` (Build, Size Modifier, Age, Appearance, etc., pp 18–22). Tinha sido marcado "etapa 1b" no histórico — agora explícito.
7. ✅ **Equipment** — `equipment.json` (67 items core: melee/ranged/armor/shields, pp 264–289). Listas extensas (Low-Tech, High-Tech, Ultra-Tech) ficam pra expansion futura.
8. ✅ **Templates + Meta-traits** — `templates.json` (6 meta-traits + 3 character templates + 5 racial templates samples)
9. ✅ **Magic (sistema padrão + Spell List)** — `spells.json` (63 spells, pp 234–253, `list_only`)
10. ✅ **Psionics (resumo)** — `psionics.md` (pp 254–257). Stub — expansão real em livro separado.
11. ✅ **Character Development** — `character_development.md` (cap 9, pp 290–296)

### Bloco B — Jogo (Campaigns book)

12. ✅ **Success Rolls** — `success_rolls.md` (pp 8–26)
13. ✅ **Combate** — `combat.md` + `combat_tables.json` (caps 11–14, pp 27–109; 20 maneuvers + 11 damage types + 11 hit locations + defenses/posture/encumbrance/death)
14. ✅ **GM Tools / Game Worlds** — `gm_tools.md` (caps 18–20, pp 151–227)

### Bloco C — Powers (livro Powers)

15. ✅ **Powers overview** — `powers_overview.md`. Sistema reaproveita advantages.json + modifiers.json existentes — expansion específica do livro Powers (new advantages, new modifiers) fica pendente como `_supplement` files.

### Bloco D — Pós-catálogo (próximos passos)

Catálogo Bloco A+B+C entregue. Agora dá pra construir:
- **Schema validador** no `CharacterSheet.save()` usando os JSONs
- **Autocomplete** no front-end ficha (advantages/disadvantages/skills/spells/equipment)
- **Calculadora de dano** (combat_tables.json)
- **Criador guiado de personagem** (templates.json + advantages/disadvantages)
- **Roll engine** (3d com modifiers, criticals, margem)
- **Reaction roll table** (gm_tools.md)

### Pendências menores

- **Traços físicos** (`physical_traits.md`): Build/Size Modifier/Age/Appearance — partial em attributes.md, faltam detalhes específicos
- **Tactical combat detalhado** (cap 12-13 Campaigns pp 49-82): regras avançadas (hex map, facing, close combat, posture transitions) — combat_tables.json cobre o essencial
- **Injuries detalhado** (cap 14 Campaigns pp 83-109): regras de doença/fadiga avançadas
- **Animals/Bestiary + Technology** (caps 16-17 Campaigns): referência, não-essencial
- **Powers new advantages/modifiers**: expansion do `advantages.json`/`modifiers.json` com material específico do livro Powers (Affliction expandida, Wildcard Skills, Backlash limitation, etc.)
- **Skills/Spells detail expansion**: list_only → full (descrições, defaults, durations) sob demanda
- **Quirks list** (Characters p162-165): pequenos -1pt traits

---

## Registro de etapas concluídas

### Etapa 1 — Atributos e características secundárias
- **Status:** entregue, aguardando validação do usuário
- **Data:** 2026-04-21
- **Fonte:** *Basic Set: Characters*, pp. 14-21
- **Entregáveis:**
  - [`docs/gurps/attributes.md`](gurps/attributes.md) — referência humana
  - [`gurps/data/attributes.json`](../gurps/data/attributes.json) — dados estruturados
- **Cobre:** 4 atributos primários (ST/DX/IQ/HT) + secundários (HP, Will, Per, FP, Basic Speed, Basic Move, Dodge, Basic Lift, dano) + tabela completa de dano + níveis de encumbrance + escala de interpretação (humana e não-humana)
- **Não cobre** (fica para etapa posterior): traços físicos (Build, Size Modifier, Dwarfism/Gigantism, Age, Appearance), Handedness, Fashion Sense e demais "other physical features". Propor nova etapa **"1b — Traços físicos"** se o usuário quiser manter escopo enxuto por etapa.
