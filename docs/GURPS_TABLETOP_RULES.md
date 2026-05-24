# GURPS 4e — Regras aplicadas ao Tabletop (Hex Map)

> **Propósito:** consolidar TODAS as regras GURPS 4e que afetam o tabletop interativo do roll3d6.
> **Audiência:** o próprio assistente de IA em sessões futuras — usar como base ao implementar features de mapa, tokens, turnos, ataques.
> **Fontes:** `docs/gurps/combat.md`, `docs/gurps/combat_tactical.md`, `docs/gurps/attributes.md`, `gurps/data/combat_tables.json`, `gurps/data/reference_tables.json`.

---

## 1. UNIDADES E CONVERSÕES (REGRA FIXA DO PROJETO)

GURPS usa sistema imperial. **No roll3d6 convertemos tudo pra métrico/brasileiro.** Regra de ouro do user: **1 yard = 1 metro** (simplificação intencional, mesmo que não seja exato — yard real = 0.914m).

### Tabela canônica de conversão

| GURPS (livro) | roll3d6 (UI/banco) | Notas |
|---|---|---|
| 1 yard | 1 metro | **fixed 1:1**, simplificação por preferência do user |
| 1 hex | 1 metro | 1 hex = 1 yard no livro → 1m no roll3d6 |
| 1 inch | 2.5 cm | conversão padrão (`× 2.54`, arredondado) |
| 1 foot | 30 cm | conversão padrão (`× 30.48`, arredondado) |
| 1 mile | 1.6 km | conversão padrão |
| 1 lb | 0.45 kg | usar **kg** como unidade canônica |
| 1 oz | 28 g | `oz × 28.35` |
| 1 gallon | 3.8 L | |
| Fahrenheit | Celsius | `(°F − 32) × 5/9` |

### Implementação prática

- **Todos os JSONs do catálogo** (`equipment.json`, `attributes.json`, etc.) podem manter valores originais; o frontend converte no display.
- **Banco de dados** deve guardar em **métrico** (kg, metros) para evitar drift.
- **Basic Lift (BL)**: fórmula é `(ST × ST) / 5` em lbs → no display, multiplicar por 0.45 e arredondar pra 1 casa decimal. Ex: ST 10 → BL 20 lbs → exibe "9 kg".
- **Velocidades**: `Basic Move` é "yd/s" no livro → no roll3d6 é **"m/s"** com mesmo valor numérico (1:1).
- **Range**: tabela Size/Speed/Range (`reference_tables.json:size_speed_range_table`) é em yards → ler como metros.

### Onde implementar a conversão

Helper centralizado em `gurps/units.py` (a criar) com funções:
```python
lb_to_kg(value: float) -> float
oz_to_g(value: float) -> float
inches_to_cm(value: float) -> float
feet_to_cm(value: float) -> float
yards_to_m = lambda y: y  # 1:1, mas mantemos a função pro alinhamento semântico
```

E no front, um helper JS equivalente: `roll3d6.units.lbKg(lb)`, etc.

---

## 2. ESCALA DO HEX MAP

### Tamanho do hex
- **1 hex = 1 metro** (= 1 yard original).
- Hex **flat-top** (lado plano em cima) ou **pointy-top**? GURPS Basic Set p49 mostra **flat-top** (lados verticais nas laterais). **Decisão para implementação: flat-top.**

### Quem ocupa quantos hexes (Size Modifier)
GURPS Basic Set p19 + Campaigns p49:

| Size Modifier (SM) | Exemplo | Hexes ocupados |
|---|---|---|
| -1 | Halfling, criança, gato | **½ hex** (pode dividir um hex com outro SM-1) |
| 0 | Humano padrão | **1 hex** |
| +1 | Cavalo, gorila grande, urso polar | **2 hexes** |
| +2 | Boi, elefante, dragão pequeno | **4 hexes** |
| +3 | T-Rex, cavalo enorme | **9 hexes** |
| +4 | Elefante grande, baleia | **16 hexes** |

Implementação: o **token** tem `size_modifier` (int) e o front desenha o cluster de hexes correspondente.

### Movimento

- 1 Move = 1 hex em terreno aberto (incluindo diagonais em hex, que não custam extra).
- Subir/descer 1m de altura: 2 Move (custa o dobro).
- Terreno difícil (lama, mato denso): 2 Move por hex.
- Terreno muito difícil (pântano, neve profunda): 3+ Move.
- Sprint: +20% Move (round down).

### Facing (direção)

Cada token tem **uma direção** de facing. O hex flat-top tem 6 lados → 6 facings possíveis.

| Zona | Hexes | Efeitos |
|---|---|---|
| **Front** | 3 hexes (frente + 2 diagonais frontais) | Ataques full, defesas full |
| **Side** | 2 hexes laterais | Atacar pelo lado: -2 hit. Defesa: sem Retreat |
| **Back** | 1 hex direto atrás | Atacar por trás: oponente só pode Dodge (sem Retreat, sem Parry/Block) |

Implementação: render uma "seta" ou ângulo no token mostrando facing. Mudar facing é **livre** durante Move ou Step.

---

## 3. ALCANCE (REACH)

Cada arma tem **Reach** (alcance em hexes):

| Reach | Alcança | Exemplo de arma |
|---|---|---|
| **C** | Mesmo hex (close combat) | Punhos, adagas pequenas |
| **1** | Hex adjacente | Espada curta, machado |
| **1, 2** | 1 ou 2 hexes | Espada longa |
| **2, 3** | 2 ou 3 hexes | Lança |
| **2, 3, 4** | até 4 hexes | Pique |
| **C, 1** | versátil | Adaga (lâmina curta) |

Implementação: ao selecionar uma manobra de Ataque com arma, **destacar visualmente** os hexes alcançáveis a partir do hex/facing do token atacante.

**Movimento + ataque:**
- **Step** (toda manobra de ataque): mover 1 hex antes/depois (sem perder facing).
- **Move + Attack**: mover full + atacar → -4 hit melee, ou Bulk penalty cap +2 ranged. Só permite **Dodge** como defesa.

---

## 4. ORDEM DOS TURNOS

### Initiative
**Basic Speed** ordena (maior primeiro). Empate → maior **DX**. Ainda empate → roll 1d.

Em **Surprise Round**, surpresos perdem 1 turno. *Combat Reflexes* dá +1 ou +2.

### Turno individual
- Duração: **1 segundo** in-game.
- Cada combatente escolhe **uma manobra** das 13 disponíveis (já em `combat_tables.json`).
- **Free actions** em paralelo: falar curta, soltar item, abrir/fechar mão.

### Maneuvers principais (resumo)

| Manobra | Move | Defesa permitida | Descrição |
|---|---|---|---|
| **Do Nothing** | 0 | qualquer (se não stunned) | Stunned/KO |
| **Move** | full | qualquer | só andar |
| **Change Posture** | 0 | qualquer | trocar postura |
| **Aim** | step | qualquer | acumular Acc |
| **Attack** | step | qualquer | 1 ataque |
| **Feint** | step | qualquer | Quick Contest |
| **All-Out Attack** | half/full | **NENHUMA** | +4 hit / 2 atks / +2 dano |
| **All-Out Defense** | step | dobrada ou +2 | sem ataque |
| **Move and Attack** | full | só Dodge | -4 melee |
| **Ready** | step | qualquer | sacar/recarregar |
| **Concentrate** | step | qualquer | magia/psi |
| **Wait** | none | qualquer | trigger reativo |

Implementação: pelo menos as **5 principais** (Move, Step, Attack, All-Out Attack, All-Out Defense, Move and Attack) precisam aparecer como ações na UI quando o turno é do jogador.

---

## 5. POSTURA

Custa **Change Posture** maneuver pra trocar (exceto: deitar de pé é livre se for queda involuntária).

| Postura | Move | Penalty Ranged (alvo) | Penalty Melee (atacante) |
|---|---|---|---|
| Standing | full | 0 | 0 |
| Crouching | 2/3 | 0 | -2 atk, -2 def |
| Kneeling | 1/3 | -2 | -2 atk, -2 def |
| Sitting | 0 | -2 | -2 atk, -2 def |
| Lying down | 1 (crawl) | -4 | -4 atk, -3 def, +3 ranged a hit contra |

Implementação: token tem `posture` enum; ícone visual de postura.

---

## 6. ATAQUE / DEFESA (em ordem de resolução)

1. Atacante escolhe manobra de ataque.
2. **Step** (mover 1 hex) opcional antes ou depois.
3. Hit modifiers acumulam:
   - Range (Size/Speed/Range table)
   - Hit location penalty (se mira local específico)
   - Posture do alvo
   - Cover, darkness
   - Facing (lado/costas)
4. Atacante rola **3d ≤ skill effective**. 3-4 = crítico; 17-18 = falha crítica.
5. Se acertou, alvo tem **active defense**:
   - **Dodge** = Basic Speed + 3, − encumbrance
   - **Parry** = (skill/2) + 3
   - **Block** = (Shield skill/2) + 3 + shield DB
6. Defesa falha → dano rolado.
7. Dano − DR do alvo = penetrating damage.
8. Aplicar wounding multiplier (cut ×1.5, imp ×2, etc.).
9. Reduzir HP do alvo. Aplicar **shock**, **major wound check**, **knockback**, etc.

Implementação: a UI já tem botão "Rolar" em cada Ataque/Defesa. O tabletop adiciona contexto (range, facing) automaticamente baseado no hex do atacante e alvo.

---

## 7. STATES E MARCADORES VISUAIS

Tokens precisam refletir estados que afetam mecânica:

| Estado | Origem | Efeito mecânico |
|---|---|---|
| **Stunned** | Major wound failure | Só Do Nothing por 1 turno; defesas a -4 |
| **Knocked down** | Major wound fail by 5+ | Lying down |
| **Unconscious** | HT roll fail at ≤0 HP | Sem ações |
| **Bleeding** | cut/imp/pi com penetração | HT roll/minuto, perde HP |
| **Aiming** | Aim maneuver acumulando | +1 a hit acumulado |
| **Crippled (arm/leg/etc.)** | Dano em local > max | Membro inútil |
| **Restrained / Grappled** | Grapple | DX/skills -4 |

Implementação: token tem array de `status_effects[]`. UI mostra ícones pequenos no canto do token.

---

## 8. DESENHOS NO MAPA (não-GURPS, decisão do user)

User pediu: linhas, círculos, quadrados. Sugestões de uso GURPS-relevante:

- **Linhas**: trajetória de movimento, mira de arma, linha de visão.
- **Círculos**: área de efeito (explosões, magia), aura de efeito (Combat Reflexes range, halo).
- **Quadrados / retângulos**: paredes temporárias, móveis (mesa, baú), zona de cover.
- **Cor**: differenciar autor (cada usuário com cor própria).

---

## 9. REFERÊNCIAS RÁPIDAS

| Conceito | Arquivo |
|---|---|
| Manobras (20) | `gurps/data/combat_tables.json` → `maneuvers` |
| Hit locations (11) | `gurps/data/combat_tables.json` → `hit_locations` |
| Damage types (11) | `gurps/data/combat_tables.json` → `damage_types` |
| Postura | `gurps/data/combat_tables.json` → `posture_modifiers` |
| Encumbrance | `gurps/data/combat_tables.json` → `encumbrance_levels` |
| Active defenses | `gurps/data/combat_tables.json` → `active_defenses` |
| Range table | `gurps/data/reference_tables.json` → `size_speed_range_table` |
| Reaction | `gurps/data/reference_tables.json` → `reaction_table` |

### Documentos prosa

- `docs/gurps/combat.md` — combate base (turnos, ataques, defesas, dano)
- `docs/gurps/combat_tactical.md` — hex map, facing, movimento, combate especial
- `docs/gurps/attributes.md` — atributos, secundárias, encumbrance
- `docs/gurps/injuries.md` — feridas, doenças, fadiga
- `docs/gurps/success_rolls.md` — roll mechanics gerais
