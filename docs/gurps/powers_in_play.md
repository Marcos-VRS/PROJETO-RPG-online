# GURPS Powers — Caps 4, 5, 6 (resumo)

> **Fonte:** *GURPS Powers* caps 4 (Powers in Action, pp 154-180), 5 (Power Games, pp 181-204), 6 (Empowered Genres, pp 205-236).

## Cap 4 — Powers in Action

### Combat com Powers

Ataques baseados em powers seguem regras do Innate Attack (Basic Set p61), Affliction (p35), Binding (p40). Modificações importantes:
- **Hit location** vale pra hit ranged/melee normalmente
- **Active defenses** funcionam contra powers (Dodge sempre; Parry/Block conforme natureza do ataque)
- **Static, Magic Resistance, Mind Shield, Damage Resistance (limited)** podem negar parcialmente

### Drain de Power

Algumas situações esgotam o power:
- **FP cost** (modifier Costs Fatigue): pagam FP por uso
- **Drained Powers limitation**: -25% a -50% — power falha quando você está abaixo de X FP
- **Burnout**: falha crítica em rolagem de power pode "queimar" o power por 1d horas/dias

### Recovery

- FP regenera normal (1/10min descansando)
- Power burnout: GM define recovery (descanso, ritual, transfusion, etc.)
- Drained abilities: subir FP regenera

### Power vs Power Combat

Quando duas powers conflitam:
- **Source-based**: Antipsi cancela Psionic, Anti-Magic cancela Magical, etc.
- **Quick Contest** quando ambos tentam controlar mesmo recurso (Telekinesis vs Telekinesis)
- **Static, Resistance abilities** geralmente vencem em quick contest mas com penalties

### Sensitive Information

Powers que revelam info (Detect, Mind Reading, Precognition) NÃO substituem investigação — GM controla revelação narrativa. Roll bem-sucedido = clue, não solução total.

## Cap 5 — Power Games

### Campaign Design

- **Power Level**: defina escala (street vigilante até cósmico)
- **Common origin** ou origin diversa (mutantes só vs mundo com magia+psi+super juntos)
- **Disadvantage Limit** geralmente aumentado em settings de power (-100 a -150 typical)
- **Starting Points**: 150 (street) a 500+ (cosmic supers)

### Power NPCs

- **Power Tier** estabelecida no setting
- Villains com powers oferecem desafios narrativos específicos
- Counter-power NPCs (Antipsi, Anti-Magic) servem de tools narrativos
- Patrons com powers podem ser deus/mentor figures

### Power Equipment

Artifacts que dão powers:
- Custo cash típico em vez de pts (se disponível em mercado)
- **Signature Gear** (Basic p85) com Powers add-on
- Items podem ser broken/stolen — limitações Breakable e Can Be Stolen (Basic p116)
- Ritual items (sacred objects) podem ser destruídos por opposing power

## Cap 6 — Empowered Genres

Convenções de gênero pra powers:

### Super-heroic
- Powers visíveis e dramáticos (Visible -10%)
- Reduced disadvantages (-50% disad limit)
- Cinematic rules ligadas (Damage Resistance comum, Luck comum, etc.)
- Secret Identity comum disadvantage

### Wuxia / Martial Arts
- Powers de chi: Trained By A Master, internal disciplines
- Powers físicos disfarçados (Combat Reflexes, Flying Leap, Power Blow)
- Ki-based: chi source modifier (-10%)

### Sci-Fi
- Powers tecnológicos: Gadgeteer, cybernetics, exotic substances
- Powers psi como variant científica (Psionic Powers livro)
- Powers ligados a hardware (Breakable, Can Be Stolen)

### Cinematic Horror
- Powers sobrenaturais raros e devastadores
- Players geralmente NÃO têm powers; vilões têm
- Powers tem cost narrativo (corrupção, sanity loss)

### Fantasy
- Magery, Power Investiture, True Faith mais comuns
- Required disadvantages (Vows, Disciplines of Faith)
- Pact limitation comum

### Modern Conspiracy
- Powers escondidos (Secret disadvantage)
- Powers limitados ou raros (Static blocks most)
- "Wild Talent" justifies one-off abilities

---

## Para o app

Esses capítulos são primarily GM guidance e não introduzem mecânica catalogável adicional. Para implementação:

1. **Campaign.power_level** field: 'street' / 'cinematic' / 'super' / 'cosmic'
2. **Campaign.disad_limit** ajustável (default -75)
3. **Campaign.starting_points** ajustável
4. **Genre presets** que pré-configuram esses valores

Documentação completa do livro Powers cap 4-6 está aqui pra referência futura quando expandir features.
