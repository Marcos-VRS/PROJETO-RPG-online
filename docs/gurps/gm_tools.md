# GURPS 4e — GM Tools & Game Worlds (Cap 18, 19, 20 Campaigns)

> **Fonte:** *Basic Set: Campaigns*, capítulos 18 (Game Mastering, pp 151-169), 19 (Game Worlds, pp 170-187), 20 (Infinite Worlds setting, pp 188-211), Apêndice Tables (pp 212-227).

## Cap 18 — Game Mastering

### Reaction Rolls (Influence)
NPCs reagem a PCs com **3d ± modifiers** contra **Reaction Table** (p560):
- 6 ou menos: hostil/violento
- 7-9: ruim/desconfiado
- 10-12: neutro
- 13-15: bom/cooperativo
- 16+: excelente/leal

Modifiers: Appearance, Reputation, Status, Charisma, Voice, social skill use.

### Influence Skills
Acting, Diplomacy, Fast-Talk, Intimidation, Savoir-Faire, Sex Appeal, Streetwise. Cada um cria opportunity de melhor reação via Quick Contest.

### Bonuses for Character Points
GM dá pts por:
- Boa interpretação (1-3 pts)
- Atingir objetivo de aventura (3-5 pts)
- Sobreviver a perigo extremo (1-3 pts)
- Insights criativos (1-2 pts)

### Awarding Earned Points
Range típico: 1-5 pts por sessão. Ver Char Development p290.

### Style of Play
- **Realistic** vs **Cinematic** vs **Silly**
- GM decide tech level, magic level, supernatural availability
- Disadvantage Limit (p11): geralmente -40 a -75 pts

## Cap 19 — Game Worlds

### Components of a Setting
- **Tech Level (TL)**: 0 (stone age) a 12 (singularity sci-fi). TL 8 = "atual" (2010s).
- **Mana Level**: no mana, low, normal, high, very high — define magia.
- **Sanctity**: para clérigos (Power Investiture).
- **Psionic Level**: nenhum, baixo (raro), normal, alto.
- **Cinematic/Realistic**: switches que afetam diversas regras.

### Genre conventions
- **Fantasy** (medieval, swords & sorcery): TL 3-4, magic typical.
- **Modern** (mundane): TL 7-8.
- **Sci-Fi**: TL 9-12.
- **Horror**: cinematic ou supernatural, geralmente mundane TL com toque sobrenatural.
- **Super-heroic**: alto-cinematic, supers everywhere.
- **Historical**: realista, foco em precisão histórica.

### Houserules
GM customiza:
- Disadvantage Limit
- Allowed character points (starting)
- Race/template availability
- Combat detail (basic vs tactical)

## Cap 20 — Infinite Worlds (setting próprio)

Setting de campanha incluído no Basic Set: **mundo onde Infinity Unlimited e ISWAT exploram parallel timelines**. NPCs, conflitos (Centrum vs Infinity), tecnologia (parachronic projectors, conveyors), worlds notáveis. Não-essencial mecanicamente — só se for usar.

## Apêndice Tables (pp 212-227)

Tabelas consolidadas pra consulta rápida:
- **Reaction Table** (p560)
- **Damage Table** (Characters p16 — já em attributes.json)
- **Speed/Range Table** (p550)
- **Fright Check Table** (p360)
- **Standard Modifiers**

Essas tabelas estão também espalhadas pelo livro; o apêndice consolida. Para o app, os dados-chave já estão em `combat_tables.json` (combat) e `attributes.json` (damage table).

---

## Implementação no app

Pra GM tools no app desktop:
1. **Dice roller** com reactions (3d + bônus → tabela)
2. **Secret rolls** — GM rola sem mostrar pros jogadores (Sense rolls, Fright Checks).
3. **NPC reaction tracker** — manter reactions persistentes por NPC.
4. **Campaign settings** — TL, mana level, sanctity, psionic level, disad limit definidos por Campanha.
5. **Earned points award** — botão "+X pts" pro GM aplicar a cada player no fim da sessão.

Adicionar campos `tech_level`, `mana_level`, `disadvantage_limit` em `Campanha` model quando for implementar.
