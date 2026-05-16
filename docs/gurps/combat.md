# GURPS 4e — Combate (resumo de regras)

> **Fonte:** *Basic Set: Campaigns*, capítulos 11–14 (pp 27–109).
> **Arquivo de dados:** [`gurps/data/combat_tables.json`](../../gurps/data/combat_tables.json)
> **Última atualização:** 2026-05-16

Este documento condensa as regras essenciais de combate de GURPS 4e — o que o backend/UI precisam pra (a) processar uma rolada de ataque, (b) aplicar dano, (c) tracking de turn order. Detalhes em prosa narrativa ficam no livro; aqui só o esqueleto mecânico.

---

## 1. Combat Turn Sequence

Tempo em GURPS é dividido em **turnos de 1 segundo**. Cada combatente age na ordem do **Basic Speed** (maior primeiro; empate → maior DX; ainda empate → roll).

Em cada turno o personagem escolhe **uma maneuver** (ver §2). Free actions (falar curto, soltar item, abrir mão) são permitidas em paralelo.

### Maneuvers principais

| Manobra | Move | Active Defense | Notas |
|---|---|---|---|
| **Do Nothing** | 0 | nenhuma sem stun | Stunned ou knocked out |
| **Move** | full | qualquer | Sem ataque |
| **Change Posture** | 0 | qualquer | Standing ↔ crouching ↔ kneeling ↔ sitting ↔ lying down |
| **Aim** | step (1) | qualquer | Acumula Accuracy do weapon; +1 extra por seg após o primeiro (max +2) |
| **Attack** | step | qualquer | Um ataque com melee ou ranged weapon |
| **Feint** | step | qualquer | Quick Contest of weapon skill; vitória dá penalty igual à margem na próxima defesa do alvo |
| **All-Out Attack** | half (Determined/Strong) ou full (Move) | **NENHUMA** | Variants: Determined +4 to hit, Double 2 ataques, Strong +2 dano, Suppression Fire |
| **All-Out Defense** | step | dobrada (+2 a Dodge/Parry/Block) ou 2 defesas | Sem ataque |
| **Move and Attack** | full | só Dodge | -4 to hit (melee) ou Bulk penalty cap +2 (ranged) |
| **Ready** | step | qualquer | Saca/prepara arma, recarrega, etc. |
| **Concentrate** | step | qualquer | Magic, psi, mental abilities |
| **Wait** | none | qualquer | Reage; comportamento triggerável |

---

## 2. Ataque (Attack roll)

**Roll** 3d ≤ **skill effective** (skill + modifiers).
- **Hit modifiers (alvo)**: SM, distância (Size/Speed/Range table), darkness, cover.
- **Hit location penalty** (atacante mira): ver §4.

**Crítica/Falha:**
- 3-4 = sempre crítica (efeitos: ver Critical Hit Table p556 do livro)
- 17-18 (ou natural max-falha por skill) = falha crítica (ver Critical Miss Table)

### Active Defenses

Após ataque acertar, alvo rola **active defense**:
- **Dodge** = `Basic Speed + 3` truncado (sem fração) − encumbrance penalty
- **Parry (weapon)** = `(weapon skill / 2) + 3` truncado, ou `(Karate skill/2)+3` p/ unarmed Karate, ou `(DX/2)+3` p/ unarmed sem skill
- **Block (shield)** = `(Shield skill / 2) + 3` truncado + shield DB

**Modifiers comuns**: Combat Reflexes +1 a todas; Retreat +1 (Dodge) ou +1 (Parry) ou +2 (Boxing Parry); pego de lado -2, pelas costas só Dodge sem retreat; surpreso = sem defesa.

**Multiple defenses**: cada defesa subsequente no mesmo turno sofre penalty (Parry -4 cumulativo, Block max 1×, Dodge sem penalty).

---

## 3. Dano

### Damage roll
Arma indica dano em **thrust** (thr) ou **swing** (sw) baseado em ST (ver tabela p16 Characters). Format: `2d-1`, `1d+2` etc. Innate Attacks usam `damage × N dice`.

### Penetration
Dano final atravessa armadura via subtração: `damage rolled - target DR = penetrating damage`. Se penetrating ≤ 0, sem dano (mas blunt trauma cr/pi/imp ainda pode causar 1 HP por 5/10 pts).

### Wounding multipliers (tipo de dano)

| Tipo | Multiplicador | Notas |
|---|---|---|
| `cr` (Crushing) | ×1 | knockback |
| `cut` (Cutting) | ×1.5 | causa knockback |
| `imp` (Impaling) | ×2 | em flesh; menos em Unliving/Homogenous/Diffuse |
| `pi-` (Small Piercing) | ×0.5 | em flesh |
| `pi` (Piercing) | ×1 | |
| `pi+` (Large Piercing) | ×1.5 | |
| `pi++` (Huge Piercing) | ×2 | em flesh |
| `burn` (Burning) | ×1 | |
| `cor` (Corrosion) | ×1 | reduz DR alvo em 1/5 pts |
| `tox` (Toxic) | ×1 | dano celular |
| `fat` (Fatigue) | ×1 | reduz FP em vez de HP |

**Injury Tolerance** modifica:
- **Unliving** (máquinas, corpóreos undead): imp ×1, pi-/pi/pi+/pi++ todos ×½
- **Homogenous** (golems, trees): imp ×½, pi-/pi/pi+/pi++ todos ×⅓
- **Diffuse** (líquido, energia): pi-/pi/pi+/pi++ max 1 HP; imp/cut max 2 HP

### Hit Locations + modifiers + special effects

| Local | Penalty | Wounding Mult | Effect |
|---|---|---|---|
| Torso | 0 | ×1 (padrão) | — |
| Vitals | -3 | ×3 (imp/pi/cr*) | *fragmentation reduz; cr não duplica |
| Skull | -7 | ×4 (qualquer dano) | DR natural +2 (skull); max wound = 10×HP/N por blow |
| Eye | -9 | ×4 | Bypassa head DR exceto visor; ≥HP/10 = crippling permanent |
| Face | -5 | ×1.5 (cut), ×1 outros | Major wound forces HT vs knockdown |
| Neck | -5 | ×1.5 cr/cor; ×2 cut/imp/pi | Cutting pode decapitar |
| Arm/Leg | -2 | ×1; max wound = HP/2 | >HP/2 dano = crippling |
| Hand/Foot | -4 | ×1; max wound = HP/3 | >HP/3 = crippling |
| Groin | -3 | ×1; ×2 cr | HT-5 ou stunned (homens) |

### Knockback

Crushing e cutting ataques: cada `(dano basic - 2)` jds = 1 jd knockback. Vítima HT roll para evitar knockdown (-1 por jd além do 1º).

### Shock

Qualquer dano (mesmo após DR e ×0) inflinge **shock penalty** = HP perdido (max -4) em IQ/DX/skills no PRÓXIMO turno. *High Pain Threshold* anula. *Low Pain Threshold* dobra (max -8).

### Knockdown / Stunning (Major Wound)

Dano em UMA hit ≥ HP/2 ou em qualquer skull/face/vitals/groin → HT roll:
- Sucesso: continua
- Falha por <5: stunned (1 turno)
- Falha por 5+: stunned + knocked down
- Falha crítica: knockout

*High Pain Threshold* +3 nesses rolls; *Hard to Subdue* +1/nível; *Low Pain Threshold* -4.

### Crippling

Dano em arm/leg/hand/foot/eye que excede o máximo (HP/2, HP/3 etc.) causa **crippling**. Se dano > 2× max = membro destruído/severed. Healing pode reverter crippling se cura até full HP perdido pela lesão, com IQ-6 (ver Healing advantage).

### Death

| HP atual | Efeito |
|---|---|
| `> HP/3` | Funciona normal (com shock) |
| `≤ HP/3` | Move/Dodge ½ |
| `≤ 0` | HT roll cada turno pra ficar consciente |
| `≤ -HP` | HT roll pra evitar morte instantânea |
| `≤ -2×HP` | mesma + cumulative |
| `≤ -3×HP` | mesma |
| `≤ -4×HP` | mesma |
| `≤ -5×HP` | **morte automática** |
| `≤ -10×HP` | corpo desintegrado |

*Hard to Kill* +1/nível nesses HT rolls.

### Recovery

- HP: 1 HP por dia de descanso + boa nutrição (HT roll daily; falha = 0; crítica = 2).
- FP: 1 FP a cada 10 minutos descansando, ou 1 a cada minuto se totalmente parado.
- Stunning: HT/IQ roll a cada turno pra sair.
- Unconsciousness from knockout: 15 min × (sem HP / 10) ou similar; ver tabela p423 Characters.
- Bleeding (cut/imp/pi com penetração): HT roll cada minuto; falha = 1 HP a mais. First Aid pode parar.

---

## 4. Outros mecanismos

### Aim
Aim maneuver acumula **Acc** do weapon. Default = full Acc após 1 turno; +1 extra a cada turno adicional, max **+2**. Brace (mãos firmes no chão/parede) = +1.

### Rapid Strike (1 turno, 2 ataques melee)
-6 em cada ataque (Weapon Master / Trained by Master: -3). Não pode combinar com All-Out Attack.

### Suppression Fire / All-Out Attack (Suppressing Fire) — RoF
Cobre área; alvos sem cover devem checar.

### Range modifiers (Size/Speed/Range Table p550)
Aplicado por distância em jds. Speed/Range combinados pra ranged.

### Encumbrance e Move

| Nível | Carga | Move × | Dodge |
|---|---|---|---|
| None | ≤ BL | 1.0 | base |
| Light | 2× BL | 0.8 | -1 |
| Medium | 3× BL | 0.6 | -2 |
| Heavy | 6× BL | 0.4 | -3 |
| Extra-Heavy | 10× BL | 0.2 | -4 |

Sprinting: +20% Move.

### Posture modifiers

| Postura | Move | Ranged hit penalty | Melee penalties |
|---|---|---|---|
| Standing | full | 0 | 0 |
| Crouching | ⅔ | 0 | -2 atk, -2 defense |
| Kneeling | ⅓ | -2 | -2 atk, -2 defense |
| Sitting | 0 | -2 | -2 atk, -2 defense |
| Lying down | 1 (crawl) | -4 | -4 atk, -3 defense (alvo +3 ranged a hit) |

---

## 5. Recursos no JSON auxiliar

Ver `gurps/data/combat_tables.json` para dados estruturados:
- `maneuvers` — todas as manobras com Move/Defense/notas
- `damage_types` — tipo + multiplicador
- `hit_locations` — local + penalty + multiplier + max wound
- `posture_modifiers`
- `encumbrance_levels`
- `range_speed_modifiers` — tabela completa Size/Speed/Range

Esses dados podem ser usados pelo backend para:
- Calcular dano final automaticamente
- Validar ataques (hit location, range)
- Aplicar efeitos secundários (shock, knockdown, crippling)
- Computar Active Defenses corretamente
