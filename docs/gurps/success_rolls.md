# GURPS 4e — Success Rolls (Cap 10 Campaigns)

> **Fonte:** *Basic Set: Campaigns*, capítulo 10 (pp 8-26).

Toda ação não-trivial em GURPS é resolvida por um **success roll**: `3d ≤ effective skill/attribute`. Ele é o coração mecânico do sistema.

## Mecânica básica

- **Roll 3d.** Soma das três (range 3-18, bell curve em 10-11).
- **Efetivo** = skill ou atributo base + modificadores de situação.
- **3, 4** = **crítica** (sempre). 17, 18 = **falha crítica**. Margens extremas adicionais (skill ≥16 → 5 também crítica).
- **Margem de sucesso/falha** = diferença entre efetivo e roll. Margem alta = melhor resultado.

## Modifiers (p10)

Modificadores adicionam/subtraem do skill antes de comparar. Cumulativos.

| Categoria | Exemplos típicos |
|---|---|
| Task difficulty | Easy +4, Trivial +5, Routine +2, Average 0, Tough -2, Hard -4 |
| Equipment | Excellent +1 a +2, Good 0, Improvised -2 a -5, Lacking -5 |
| Time | Extra time × 2 = +1, × 4 = +2, × 8 = +3 (until +4 max) |
| Hasty | -1 a -10 dependendo de quanto menos tempo |
| Distractions | -1 a -5 (chuva forte, combate ao redor) |
| Long Tasks | Roll por dia/semana de trabalho contínuo |

## Default Rolls

Quando você não tem skill, usa **default** (geralmente atributo controlador menos uma penalty). Cada skill lista seus defaults. Se nenhum default existe = não pode tentar.

## Quick Contests (p13)

Dois personagens rolam contra seus skills/atributos. **Quem ultrapassa por mais margem vence**. Empate = stalemate ou GM decide.

## Regular Contests (p14)

Roll repetido até alguém falhar. Cada falha reduz pool/score do perdedor; ganhador continua. Usado pra tug-of-war, negotiation, etc.

## Rule of 16 (p14)

Em quick contests, skill efetiva nunca conta acima de **16** quando rolando contra defesa de alvo (resistência, dodge, etc.). Skills muito altas não viram autossolução.

## Physical Activities

Rolagens específicas (Climbing, Jumping, Lifting, Running, Swimming, Throwing) têm regras detalhadas em pp 14-22. Resumo:

- **Climbing:** DX-based; surface determines penalty. Falha cumulativa = queda.
- **Jumping:** broad jump = `(2 × Basic Move + 1d-1) - 3` feet. High jump = `(Basic Move/4) ft`.
- **Lifting/Pushing:** ST-based. Basic Lift × 2-10 conforme effort + duration.
- **Running:** Basic Move per second sustentado; sprint = +20% por curtas distâncias.
- **Swimming:** ½ Basic Move por default; ST roll periodic for endurance.
- **Throwing:** distance = Basic Lift × multipliers from p355.

## Sense Rolls (p358)

GM rola **Per (ou Per-based)** secretamente quando algo importante poderia ser percebido. Vision, Hearing, Smell/Taste, Touch são specializations. Acute Senses + Talents melhoram.

## Fright Checks (p360)

Confronto com sobrenatural/horror: **Will roll** com modifiers de Fright Check Table (p25). Margem de falha define severidade (medo passageiro a insanidade temporária). Fearlessness, Combat Reflexes ajudam.

## Influence Rolls (p359)

Tentativas sociais (Diplomacy, Fast-Talk, Intimidation, Savoir-Faire, Sex Appeal, Streetwise) contra reaction-based resolução. Quick Contest comum.

## Will Rolls

Resistir corrupção mental, coerção, dor, supernatural. **Indomitable** anula influência ordinária.

---

## Implementação no app

Para implementar success rolls programaticamente:

```python
def roll_3d():
    return sum(random.randint(1,6) for _ in range(3))

def success_roll(effective_skill: int, *modifiers: int):
    eff = effective_skill + sum(modifiers)
    roll = roll_3d()
    margin = eff - roll
    if roll <= 4 or (eff >= 15 and roll <= 5) or (eff >= 16 and roll <= 6):
        return "critical_success", margin
    if roll >= 17 or (eff <= 15 and roll == 17) or roll == 18:
        return "critical_failure", margin
    return ("success" if margin >= 0 else "failure"), margin
```

Endpoints REST a implementar (futuro):
- `POST /game/<id>/roll` — body: `{skill, modifiers, roll_type, character_id}`. Response: result + margin + rolled dice.
- Histórico em `Message` model com tipo `roll`.
