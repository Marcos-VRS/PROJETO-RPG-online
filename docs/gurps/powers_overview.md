# GURPS 4e — Powers (Resumo do livro Powers)

> **Fonte:** *GURPS 4e Powers* (243 pp). Suplemento que expande sistema de poderes pra super-heróis, habilidades extraordinárias, abilities sobrenaturais.

## O que é "Power"?

Em GURPS, **Power** é um conjunto de habilidades temáticas com **mesma origem** (mística, psi, divina, científica, etc.). Cada power tem:
- **Source**: mágico, divino, psi, tech, mutante, chi, espiritual...
- **Talent**: vantagem que dá bônus em todas as abilities daquele power
- **Pré-requisitos**: a ability requer o Talent

Ex: "Cosmic Power: Stellar" = abilities baseadas em estrelas; talent Stellar Talent (10 pts/nv) adiciona ao roll de cada ability.

## Estrutura do livro

### Cap 1 — Building Powers (pp 8-39)
- Como definir o **source** do power
- **Countermeasures**: itens/condições que anulam (kryptonite, sunlight, etc.)
- **Required Disadvantages**: power obriga ter certas desvantagens
- **Sample Modifiers** específicos
- **Pricing Talents**: 5/10/15 pts por nível conforme escopo

### Cap 2 — Building Abilities (pp 40-121)
- Reutiliza vantagens do Basic Set como abilities
- **New Advantages** (pp 92-100): Affliction, Affliction-based abilities, Affliction-like, etc.
- **New Modifiers** (pp 109-114): mais Enhancements/Limitations específicas pra Powers (Backlash, Costs HP, Drained Powers, Maximum Duration etc.)
- **Special Effects**: cosmetic effects que não custam pts (fogo visível, raio audível)

### Cap 3 — Examples (pp 122-153)
Templates prontos:
- **Cosmic Power**: forças primordiais
- **Cybernetic Power**: implants
- **Magical Power**: subtipo de Magery
- **Psionic Power**: psi expandido
- **Spirit Power**: anjos/demônios/espíritos
- **Super Power**: comic-book

### Cap 4 — Powers in Action (pp 154-180)
- Combinar abilities (Linked, Alternative)
- Drain/recovery
- Power burnout
- Combat com powers
- Counter-powers

### Cap 5 — Power Games (pp 181-204)
- Designing campanhas em torno de powers
- NPCs e villains
- Power equipment

### Cap 6 — Empowered Genres (pp 205-236)
- Super-heroic
- Wuxia/martial arts
- Sci-fi
- Cinematic horror
- Fantasy

## Relação com Basic Set

**Power = bundle conceitual + Talent + abilities**. Mecanicamente, abilities continuam sendo **vantagens com modifier especial** (ex: -10% Psionic, -20% Magical, etc.).

Para o app:
- Não exige schema novo se já modela `advantages.json` com modifiers
- Adicionar campo `power_source` opcional ao `CharacterSheet.advantages` items
- Talents (Stellar, Magic, etc.) já cobertos em `advantages.json` (Talent generic + standard talents)

## New Advantages introduzidas no Powers (sample)

Listar todas demanda extensão de `advantages.json`. Os mais importantes:

| Vantagem | Custo | Conceito |
|---|---|---|
| **Affliction (expanded)** | 10 + N | Permite muito mais condições aplicáveis (sleep, paralysis, command) |
| **Affliction-like Innate Attack** | varia | Combina afflict + dano |
| **Cosmic Cosmic** | +200% | Para abilities "Cosmic" mesmo nesse setting |
| **Detect (Powers)** | varia | Detecta uso de power específico |
| **Wildcard Skill** | 12pts/nv | Skill que cobre área inteira |

Catalogação completa pode vir num batch futuro `advantages_powers_supplement.json` se necessário.

## New Modifiers (sample)

| Modifier | Tipo | Valor |
|---|---|---|
| **Backlash** | Limitation | -10 a -30% (sofre dano em falha) |
| **Costs HP** | Limitation | -5%/HP |
| **Drained Powers** | Limitation | -25% a -50% (power falha quando drenado) |
| **Maximum Duration** | Limitation | -5% a -50% |
| **Reduced Wave Length** | Enhancement | +20% (signal harder to detect) |
| **Wall-Crawling** | Enhancement | +20% (auto-clinging) |

Detalhes completos demandam JSON expansion futura.

## Decisão pragmática

Powers é primarily expansion — não introduz mecânica radicalmente nova, mas adiciona granularidade. Para o app desktop neste momento, o catálogo já existente em `advantages.json` + `modifiers.json` é **suficiente para implementar fichas de personagens com powers**. Refinamentos virão sob demanda.
