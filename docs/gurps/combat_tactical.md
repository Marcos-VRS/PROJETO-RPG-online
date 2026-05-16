# GURPS 4e — Tactical Combat & Special Combat (Cap 12-13 Campaigns)

> **Fonte:** *Basic Set: Campaigns*, capítulos 12 (Tactical Combat, pp 49-57) e 13 (Special Combat Situations, pp 58-82).

Esses capítulos detalham combate em **hex map** com **facing** (direção que o personagem está virado) e regras especiais para situações fora do "duelo padrão". Combat básico em [`combat.md`](combat.md).

## Cap 12 — Tactical Combat

### Hex Map (p49)
- 1 hex = 1 jarda (yard, ~0.9 m)
- Cada combatente ocupa 1 hex (SM 0 humano)
- SM +1 = 2 hexes (large; ex: cavalo)
- SM +2 = 4 hexes (ex: elefante)
- SM -1 = ½ hex (small; halfling cabe com outro)

### Facing (p50)
Cada combatente tem **front** (3 hexes à frente: front + diagonais), **side** (2 hexes laterais), **back** (1 hex direto atrás).
- **Front**: ataques full normais; defesas normais
- **Side**: -2 ataques saindo; defesas -2 (no Retreat)
- **Back**: NO ataques sem turn; defesas apenas Dodge (sem Retreat)

### Movement (p52)
- 1 Move = 1 hex em terreno aberto
- Diagonal não custa extra
- Costs:
  - Mudar facing: livre durante Move/Step
  - Subir 1 hex de altura: 2 Move
  - Atravessar dificultoso (lama, brush): 2 Move
  - Atravessar muito difícil: 3+ Move

### Attacks (p53-54)
- **Reach C**: só hex próprio (close combat)
- **Reach 1**: hex adjacente
- **Reach 2, 3...**: hex(es) mais distante(s)
- **Reach C, 1** = arma versátil em ambos

### Multiple Close Combat (p55)
Quando ≥ 2 vs 1 em close combat:
- Numerical superiority: +1 hit por aliado extra (max +5)
- Pode "swarm" alvo grande (multiple no mesmo hex)
- Cada atacante interfere com defesas dos outros (cooperação)

### Surprise & Initiative (p56)
- Em surprise round, surpresos perdem 1 turno
- **Combat Reflexes**: +1 a +2 em surprise initiative
- **Danger Sense**: GM rola Per em segredo pra avisar

## Cap 13 — Special Combat Situations

### Visibility (p58-60)
- **Darkness**: -1 a -10 hit/vision penalty conforme luz
- **Fog/Smoke**: -1 a -10 hit por intensidade
- **Night Vision** (advantage): reduz penalty
- **Dark Vision**: imune a darkness penalty
- **Infravision**: vê alvos quentes

### Special Movement (pp 60-65)
- **Climbing combat**: -2 a -5 ataque/defesa
- **Swimming combat**: ½ Move, -2 a tudo (sem Swimming skill); ⅓ underwater
- **Fall position**: ataque +3 contra, defesa -3
- **Flight combat**: 3D positioning; Aerobatics + Flight skill

### Mounted Combat (pp 65-72)
- **Mounted**: Reach +1 (cavalo dá altura); +1 hit advantage
- **Lance charge**: full mounted Move + lance: damage += rider ST + mount Move/2
- Roll **Riding** para manter na sela após hit/dodge/maneuver
- Falha = unhorsed (queda)

### Vehicular Combat (pp 72-79)
- Veículos têm HT/HP/DR como personagens
- **Driving** skill controla; **Gunner** skill atira embarcado
- Crash damage: fall damage scaled by velocity
- Vehicle types: ground (cars, tanks), naval, aerial, sci-fi

### Naval Combat (pp 79-80)
- Rolagens: **Boating** (small craft), **Seamanship** (large)
- Boarding actions: melee normal mas restricted by deck space
- Cannon/artillery via **Artillery** skill

### Aerial Combat (pp 80-82)
- 3D movement com facing 360°
- Dogfighting: Quick Contests
- Crash damage by altitude + speed
- Anti-aircraft: range modifiers ajustados

### Conditions Especiais

#### Stun & Knockdown variants
- **Mental stun**: IQ roll para sair
- **Physical stun**: HT roll
- **Knockdown only**: pode rolar pra ficar em pé (DX-3)
- **Knockout**: HT roll cada 15 min

#### Submission Holds
- Grapple + arm/leg lock: opponent suffers Will pra resistir
- After lock, can break limb (cripple) or strangle

#### Surrender
- Voluntary: lay arms down, automatic
- Forced: HT roll under intimidation/pain
- Surrendered prisoner can't actively defend

## Tactical resources em JSON

`gurps/data/combat_tables.json` já tem:
- maneuvers (20)
- damage_types (11)
- hit_locations (11)
- posture_modifiers (5)
- encumbrance_levels (5)
- active_defenses + formulas
- knockback rules
- shock_penalty
- major_wound system
- death_thresholds
- recovery rules

Extensões pendentes (em revision futura):
- `facing_modifiers` table
- `visibility_penalties` table
- `mounted_combat_modifiers`
- `vehicle_combat_rules`

Por hora, combat funcional baseado no que está em combat_tables.json é suficiente; tactical/special detail vira expansion quando for implementar features avançadas.
