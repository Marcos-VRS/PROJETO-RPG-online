# GURPS 4e — Creating Templates (Cap 15 Campaigns, pp 110-119)

> **Fonte:** *Basic Set: Campaigns*, capítulo 15.

Cap 15 explica como **construir templates de raça/personagem** que jogadores podem usar. Templates aceleram criação de PCs ao agrupar traits comuns.

## Tipos de Templates

### Character Templates
Pacote de traits que define um "tipo" de personagem (Soldier, Wizard, Scholar). Não é raça — é background/profissão.

**Estrutura:**
- Base attributes recomendados
- Required advantages
- Required skills
- Optional advantages/skills
- Custo total em pts (geralmente 50-150 pts)
- Customization budget (extra pts pro jogador alocar)

### Racial Templates
Define características inatas de uma raça/espécie (Dwarf, Elf, Orc, Vampire).

**Estrutura:**
- Attribute modifiers
- Racial advantages (Acute Vision, Night Vision, etc.)
- Racial disadvantages (Bestial, Bad Temper for orcs)
- Meta-trait inclusions (Machine, Spirit, etc.)
- Total custo da raça (positive = mais caro que humano; negative = mais barato)

## Designing a Template

1. **Concept**: Que conceito o template representa?
2. **Stats**: Atributos base que fazem sentido
3. **Power**: Quão poderoso vs PC normal humano?
4. **Required vs Optional**: O que TEM que estar; o que pode ser ajustado
5. **Customization Points**: 20-50 pts pro jogador personalizar
6. **Cost Balance**: Soma os pts dos required traits + flexibility budget

## Examples

`gurps/data/templates.json` tem samples:
- Soldier (character, 50 pts)
- Wizard (character, 75 pts)
- Thief (character, 50 pts)
- Human (racial, 0 pts — baseline)
- Dwarf (racial, 35 pts)
- Elf (racial, 35 pts)
- Halfling (racial, 0 pts)
- Orc (racial, -10 pts)

## Meta-Traits

Meta-traits são "templates micro" — bundle de advantages relacionadas (Machine, Spirit, Quadruped, etc.). Ver `templates.json` seção `meta_traits` ou `docs/gurps/templates.md` (catalogado anteriormente).

## Implementação no app

Pra criador de personagem guiado:
1. Player escolhe **racial template** (define base attributes + racial traits)
2. Player escolhe **character template** (Soldier, Wizard, etc.) ou "freeform"
3. Player gasta **customization points** em atributos, advantages, disads, skills
4. Sistema valida: cost total = starting points; required traits all set; disad limit respected

UI sugerida:
```
[Step 1: Race]  → Dwarf  (35 pts, +1 ST, Hard to Kill 2, etc.)
[Step 2: Template] → Soldier (50 pts, Combat Reflexes, Guns 12, etc.)
[Step 3: Customize] → 65 pts remaining
  - Spend on atributos | advantages | skills | optional disads
[Step 4: Final review] → 150 / 150 pts spent, validation OK
```
