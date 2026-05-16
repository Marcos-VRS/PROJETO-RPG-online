# GURPS Powers — Cap 1: Building Powers (pp 8-39)

> **Fonte:** *GURPS Powers*, capítulo 1.

Cap 1 do livro Powers explica como **construir poderes do zero** (não usar os existentes). É framework conceitual essencial para qualquer feature do app que envolva powers customizados.

## 1. O que é um Power?

Um **power** é um conjunto temático de habilidades exóticas/sobrenaturais com fonte comum. Cada power tem:

- **Source** (fonte): origem da energia — psionic, magical, divine, spirit, cosmic, chi, super, etc.
- **Focus** (foco): conceito ou item manipulado — fogo, sombra, morte, animais, computadores, etc.
- **Abilities**: vantagens do Basic Set + Powers reinterpretadas como manifestações do power
- **Power Modifier**: enhancement OU limitation (geralmente -10%) que marca a vantagem como parte do power
- **Talent**: vantagem (5-15 pts/nv) que dá bônus em rolagens com qualquer ability do power

**Power modifier é obrigatório** — sem ele, a vantagem é "wild" (não conta como parte do power).

## 2. Choosing Abilities

Critérios pra incluir uma vantagem no power:
1. **Faz sentido pro focus?** Necromantic deve cobrir morte/mortos. Light não inclui Healing exceto via lore criativa.
2. **Faz sentido pra source?** Psionic deve sentir "mental". Divine deve sentir "divino".
3. **Variedade**: combat + stealth + transport + info + social + everyday. Não restringe demais.

Vantagens típicas a considerar por categoria:
- **Attacks**: Innate Attack, Affliction, Binding
- **Defenses**: Damage Resistance, Magic/Mind Resistance, Static, Resistant
- **Movement**: Flight, Insubstantiality, Jumper, Permeation, Walk on Air, Warp
- **Mental**: Empathy, Mind Reading, Telecommunication, Telesend
- **Physical Transformations**: Alternate Form, Morph, Shapeshifting, Growth, Shrinking

## 3. Evaluating Power Modifiers (pp 22-30)

O valor (%) do power modifier depende de:

### Countermeasures
Materiais/condições que negam o power. Mais comuns = limitation maior.
- **Common** (cold iron contra faerie, mistletoe contra druids): -15%
- **Occasional** (silver contra werewolves): -10%
- **Rare** (radiation contra mages): -5%

### Required Disadvantages
Powers que forçam disads (Vow, Code of Honor): -5% a -15% conforme severidade do disad.

### Channeled Energies
Powers que dependem de fonte externa (mana, sanctity, chi) — restringe por presença/ausência da fonte.
- **Mana-Sensitive** (sem mana → sem power): -10%
- **Sanctity-Dependent** (precisa de área sagrada): -10%
- **Local Energies** (precisa fonte local específica): -15% a -30%

### Other Factors
- **Pact** (já no Basic): -5% a -15%
- **Affected by powers of opposite source**: -5% a -10%
- **Visible**: -10%

### Finalizing the Modifier
Soma os componentes; arredonda. Cada power tem UM modifier net que vai em todas suas abilities. Ex: "Magical -10%" pode somar countermeasures + required disad + visible.

## 4. Pricing Talents (pp 31-32)

Talent custa baseado no número de abilities cobertas + utilidade:

| Talent | Cost/level |
|---|---|
| Small power (≤4 abilities) | 5 pts/nv |
| Medium power (5-9 abilities) | 10 pts/nv |
| Large power (10+ abilities) | 15 pts/nv |
| Cosmic power (deus-tier) | 20 pts/nv |

Talent geralmente dá +1/nv em todas rolagens das abilities, max 4 níveis sem permissão.

## 5. Relationships Between Powers (pp 32-34)

- **Sames source, different focus**: Antipsi + ESP + Psychic Healing + PK + Telepathy + Teleportation — todos psi mas focuses diferentes
- **Power vs Power**: Antipsi cancela qualquer psi; outras interações similares
- **Hierarchy**: cosmic > divine > magical/psi > super > mundane (em settings que valorizem isso)

## 6. Powers, Great and Small (pp 34-35)

Powers de escala variada:
- **Minor**: 1-3 abilities, talent 5 pts/nv. Ex: leve regeneração + um touch attack.
- **Mid-tier**: 4-8 abilities. Ex: Telepathy completo do Basic Set.
- **Major**: 9-15 abilities. Ex: full elemental.
- **Cosmic**: 15+ abilities, deus-tier. Ex: Storm God.

## 7. Adding and Improving Powers in Play (pp 35-39)

Personagens podem adquirir/melhorar powers durante a campanha:

### Starting Out With Powers
- Comprar Talent + 1+ abilities iniciais
- GM aprova fonte narrativa (gene mutation, blessed by god, exposure to artifact)

### Adding in Play
- Pagar pts pelo Talent (se ainda não tem) + pts pela nova ability
- Justificar narrativamente: meditation, training, "level up" experience
- GM controla pace (1 ability adicional por arc, etc.)

### Improving Powers
- Subir Talent (limite 4 sem perm GM)
- Subir level das abilities existentes (DR, Innate Attack damage, etc.)
- Trocar ability por outra do mesmo power: refund pts da antiga + comprar nova (GM aprova)

---

## Implementação no app

Para o app, sugiro:

```python
class Power(models.Model):
    name = models.CharField(max_length=80)
    source = models.CharField(choices=['psi','magic','divine','spirit','cosmic','chi','super','custom'])
    focus = models.CharField(max_length=120)
    power_modifier_id = models.CharField()  # reference em modifiers.json
    talent_id = models.CharField()  # reference em advantages.json
    character_sheet = models.ForeignKey(CharacterSheet, related_name='powers')
```

E `CharacterSheet.advantages` ganha campo opcional `power_id` apontando pra qual Power a vantagem pertence (ou null = wild).

UI mostra advantages agrupadas por Power na ficha (Telepathy box com Mind Reading, Telesend, etc. dentro).

Validação: ability tem que ter o power_modifier do Power correspondente; senão erro.
