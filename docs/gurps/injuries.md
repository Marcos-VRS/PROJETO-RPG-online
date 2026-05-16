# GURPS 4e — Injuries, Illness, and Fatigue (Cap 14 Campaigns, pp 83-109)

> **Fonte:** *Basic Set: Campaigns*, capítulo 14. Dados estruturados em [`gurps/data/diseases_poisons.json`](../../gurps/data/diseases_poisons.json).

Cobre o que acontece com o personagem **depois** do dano: estado de HP/FP, ferimentos persistentes, doenças, venenos, perigos ambientais, recuperação.

## 1. Effects of Injury (pp 84-89)

### Shock
Qualquer dano (≥1 HP) inflinge **shock penalty** = HP perdido, max -4, em IQ/DX e skills baseados nesses atributos, no PRÓXIMO turno.
- **High Pain Threshold**: anula shock
- **Low Pain Threshold**: dobra shock, max -8
- Composto: -4 max, mesmo após múltiplos hits

### Major Wound (Knockdown/Stunning)
Disparado por:
- Dano em UMA hit ≥ HP/2
- Hit em skull, face, vitals, ou groin

**HT roll** (modificado por HPTHR, Hard to Subdue):
- Sucesso: continua
- Falha por <5: stunned 1 turno
- Falha por ≥5: stunned + knocked down
- Falha crítica: knockout

### Crippling Injury
Dano em arm/leg/hand/foot/eye que **excede o max** (HP/2 para arm/leg, HP/3 para hand/foot, HP/10 para eye):
- Membro crippled (não-funcional)
- Dano > 2× max = **destroyed/severed** (não cura mesmo com Healing)
- Eye <HP/10 dano = crippling permanente

### Bleeding (p420)
Cut/imp/pi ataques que penetram DR causam sangramento:
- **HT roll cada minuto**; falha = 1 HP a mais
- **First Aid** (3 minutos + roll) pode parar
- 4 sucessos consecutivos = bleeding para naturalmente

## 2. HP Thresholds & Death (p380)

| HP atual | Efeito |
|---|---|
| `> HP/3` | Normal (com shock) |
| `≤ HP/3` | Move e Dodge ½ |
| `≤ 0` | HT cada turno para ficar consciente; -1 cumulativo |
| `≤ -HP` | HT para evitar morte; falha = morre |
| `≤ -2×HP, -3×HP, -4×HP` | Mais HT rolls cumulativos |
| `≤ -5×HP` | **Morte automática** |
| `≤ -10×HP` | Corpo desintegrado |

## 3. Recuperação (Recovery)

### HP Natural
- 1 HP por dia de descanso + boa nutrição. HT roll daily: falha = 0; crítica = 2.
- **Rapid Healing** (+5 em HT effective); **Very Rapid Healing** (2 HP por sucesso, HT 12+)
- **Regeneration** advantage: 1 HP por 12h/1h/1min/1seg conforme nível

### FP
- 1 FP a cada 10 min descansando
- 1 FP por minuto se totalmente parado/sentado/deitado
- **Fit** dobra recovery; **Very Fit** dobra + reduz loss

### Unconsciousness Recovery
HT roll cada 15 min para acordar. Falha = continua. Tempo total: depende de quão fundo está.

### Crippling Recovery
- Sem Healing advantage: dano cura como HP, e ao chegar a 0 HP perdido pela lesão, membro recupera (com 2/3 funcionalidade enquanto curando)
- **Healing advantage**: IQ-6 roll + cura todos HP da lesão = membro restaurado em 1 tentativa

## 4. Fatigue Effects (p426)

FP loss causa estados:
- **FP ≤ ⅓ FP normal**: -1 em todos rolls, Move/Dodge -1
- **FP ≤ 0**: -1 IQ/DX/Per/Will (cumulativo); precisa Will roll para continuar atividade extenuante
- **FP ≤ -FP**: cai inconsciente; HT roll cada 5 min, falha = morte

### Causas de Fatigue
- **Exertion**: combat/sprint extenso (1 FP/10 min)
- **Hunger/Thirst** (Starvation/Dehydration): ver §6
- **Hot/Cold weather**: ver §6
- **Lack of sleep** (Missed Sleep): ver §6
- **Spells/Psi**: power abilities com Costs Fatigue

## 5. Disease (pp 442-443)

Doenças definidas por:
- **Vector** (blood, contact, digestive, respiratory)
- **Resistance Roll** (HT a HT-6)
- **Delay** (incubation period — default 24h)
- **Damage** (típico 1 ponto tox/ciclo; max 1d para virulentos)
- **Cycles** (default 1×/dia; pode durar 30+ cycles)
- **Symptoms** (advantage/disad/penalty após perda de fração de HP)
- **Contagion** (mildly contagious ou highly contagious)

Diagnóstico: **Diagnosis** ou **Expert (Epidemiology)** roll quando sintomas aparecem.

Tratamento: medicação reduz penalty em resistance roll. Magia (Cure Disease spell) acelera recovery.

Ver `diseases_poisons.json` para amostras: Common Cold, Flu, Cholera, Typhoid, Bubonic Plague, Tetanus, Tuberculosis, Smallpox, AIDS, Ebola.

## 6. Poison (pp 437-440)

Definição similar a disease mas:
- **Cycles** geralmente menos (1-5)
- **Delay** geralmente curto (1d minutos a 1d hours)
- **Antitoxin** disponível como cure imediata

Tipos: 
- **Blood Agent**: ferida aberta/membrana
- **Contact Agent**: pele exposta
- **Digestive (Ingested)**: comida/bebida
- **Respiratory**: inalado

Ver `diseases_poisons.json`: Curare, Strychnine, Cobra Venom, Hemlock, Hydrogen Cyanide, Sleep Gas, Nerve Gas.

## 7. Environmental Hazards

### Heat (p434)
Em temperatura > comfort zone (>90°F para humano):
- Cada hora: HT roll, falha = 1 FP perdido
- Penalty por extremo: -1 a -5 conforme magnitude
- **Temperature Tolerance** estende comfort zone

### Cold (p430)
< 35°F:
- HT roll por hora; falha = 1 FP
- < 0°F: também 1 HP por falha
- **Temperature Tolerance** + **Fur**/clothing protegem

### Dehydration (p426)
- 2 days sem água: 1d FP/dia + Will roll para resistir cravings
- 4-6 days: morte sem rehidratação

### Starvation (p426)
- 3 days sem comida: 1d FP/dia
- 1-2 weeks: 1 HP/dia adicional
- **Doesn't Eat or Drink** anula
- **Reduced Consumption** mitiga

### Drowning/Suffocation (p436)
- Holding breath (HT seconds normal): Breath Holding extends
- Submerged sem ar: 1d HP/30 seg
- **Doesn't Breathe** imune

### Falling (p431)
- Damage = `velocity² × weight / 12` em geral
- Mais comum: 1d-1 cr per yard fallen, com max 100d
- **Catfall**: subtract 5 yds, halve damage on DX
- **Acrobatics roll**: reduce 5 yds

### Electrical Shock (p432)
- Damage = burn baseado em voltage
- Side effect: HT vs stun, paralysis
- **DR** ajuda mas com Armor Divisor reduzido

### Radiation (p435)
- 1 rad por point inflicted
- Symptoms cumulativos: nausea, sickness, sterility, death
- **Radiation Tolerance** divide rad dose
- **Resistant (Radiation)** dá HT bonus

### Explosion (p414)
- Damage por distância: divide por (3 × distance)
- Fragmentation: skill 15, damage por dado adicional

## 8. Healing (médico/magia)

### First Aid (p424)
- 30 min trabalhando: recover **1d-3 HP** (min 0) one-shot
- Skill First Aid + equipment + boa condição = melhor recovery
- Aplicável apenas uma vez por lesão

### Physician (p424)
- Profissional cuidando: HT roll daily +2 (em vez de normal); recovery duplicado
- Hospital moderno: +3 a +5

### Surgery (p424)
- Necessária pra repair internal damage; First Aid e Healing ajudam
- TL dependent (cirurgia primitiva muito mais perigosa)

### Esoteric Medicine (p192)
- Trad. healing (acupuntura, herbalismo): alternativa cultural a Physician

## 9. Diseases & Poisons table

Ver `diseases_poisons.json` (catalogo estruturado).
