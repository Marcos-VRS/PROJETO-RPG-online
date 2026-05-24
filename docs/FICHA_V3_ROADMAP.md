# Ficha V3 — Roadmap (planejado, não iniciado)

> **Quando:** depois que o tabletop estiver funcional (todas as fases do `TABLETOP_MAP_PLAN.md` completas).
> **Por quê:** user antecipou: *"em algum ponto vamos reconstruir a ficha para que atenda as regras de gurps a risca com o mapa"*.

---

## Motivação

A **V2 atual** funciona como uma ficha de papel digitalizada. Os campos são fiéis a GURPS, mas não falam com o mapa. Pra o tabletop, queremos:

1. **Reach por arma** explícito no equipamento (não em texto livre).
2. **Range table** consultada automaticamente ao calcular hit modifier.
3. **Cover bonuses** automáticos baseado em obstáculos no mapa.
4. **Active defense** computada em tempo real considerando facing, retreat, all-out.
5. **Movement allowance** rastreado por turno (Move budget = Basic Move; All-Out Attack consome half; etc.).
6. **Status effects** persistentes (stunned, aiming, concentrating) sincronizados com token.

A V2 não foi desenhada pra isso. Migrar campo-a-campo seria muito retrabalho; melhor um V3 com **schema novo**.

---

## Princípios da V3

1. **JSON-first**: tudo serializado em estruturas claras, sem strings livres no que pode ser estruturado.
2. **Reusa catálogo**: cada skill/advantage referencia o ID em `gurps/data/*.json`, não duplica nome.
3. **Computed fields**: secondary attributes calculados server-side a cada save (já existe parcialmente em V2).
4. **Audit trail**: cada mudança em HP/FP guarda quem, quando, por que (pra GM rolar back).
5. **Métrico nativo**: BL em kg, distâncias em metros, sem conversão na hora de exibir.

---

## Migração V2→V3

Schema mais limpo, mas precisa **converter ficha existente**.

Plano:
1. Criar `CharacterSheetV3` lateral à V2 (segue padrão).
2. Implementar `convert_v2_to_v3(v2)` que mapeia campo a campo.
3. UI mostra "Migrar pra V3" botão por ficha. Não há migração automática.
4. V3 vira primary; V2 fica pra fichas não migradas.
5. Eventual sunset da V2 (low priority).

---

## Schema preliminar (rascunho)

```python
class CharacterSheetV3(models.Model):
    # Vínculos
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE)
    owner = models.ForeignKey(RegisterUser, on_delete=models.CASCADE)
    nome_personagem = models.CharField(max_length=80)

    # Atributos primários (somente os 4 base)
    primary_attributes = models.JSONField()  # {"st":10, "dx":12, ...}

    # Computed sub-attributes (calculado, não editável manualmente)
    computed_subs = models.JSONField()       # {"hp_max":10, "fp_max":12, "speed":5.50, ...}

    # Runtime / estado dinâmico
    runtime = models.JSONField(default=dict)
    # {
    #   "hp_atual": 8,
    #   "fp_atual": 12,
    #   "shock_penalty_next": -1,
    #   "aim_accumulated": 0,
    #   "posture": "standing",
    #   "facing": 0,
    #   "status": ["bleeding"],
    #   "encumbrance_level": 0,
    #   "active_status_effects": [
    #     {"id":"bleeding", "duration": "minutes", "applied_at": "..."}
    #   ]
    # }

    # Equipment estruturado (referencia equipment.json)
    equipped_weapons = models.JSONField(default=list)
    # [
    #   {
    #     "catalog_id": "longsword",
    #     "skill_id": "broadsword",
    #     "reach": [1],            # arrays pra reach 1,2
    #     "damage_base": "sw",     # ou "thr"
    #     "damage_mod": "+1",
    #     "damage_type": "cut",
    #     "min_st": 10,
    #     "weight_kg": 1.4,        # já em métrico
    #     "tags": ["balanced", "fine"]
    #   },
    #   ...
    # ]
    equipped_armor = models.JSONField(default=list)
    # [
    #   {"catalog_id":"chainmail_suit", "location":"torso", "dr":4, "weight_kg":11.3}
    # ]
    inventory = models.JSONField(default=list)

    # Skills com level computado
    skills = models.JSONField(default=list)
    # [
    #   {"catalog_id":"broadsword", "attribute":"DX", "difficulty":"A",
    #    "points":4, "computed_level":13, "specialization":null}
    # ]

    # Advantages/Disads (mesma estrutura V2 + computed_cost)
    advantages = models.JSONField(default=list)
    disadvantages = models.JSONField(default=list)

    # Maneuvers padrão (atalhos pra side nav)
    favorite_attacks = models.JSONField(default=list)
    favorite_defenses = models.JSONField(default=list)

    # Pontos
    points_total = models.IntegerField(default=150)
    points_breakdown = models.JSONField(default=dict)
    # {"attributes":0, "sub":0, "advantages":0, "disadvantages":0, "skills":0}

    # Visuais
    photo = models.ImageField(upload_to='character_photos_v3/', blank=True, null=True)
    token_color = models.CharField(max_length=20, default="#c9a55c")

    # Métricos físicos (opcional)
    height_cm = models.IntegerField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)

    is_quick_npc = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## O que muda no comportamento

### Roll de ataque com V3

V2 hoje: player clica botão "Rolar" na manobra Ataque → pede skill, modifier manual.

V3 + mapa:
1. Player seleciona "Attack" + clica num alvo no mapa.
2. Sistema calcula automaticamente:
   - Skill base = `skills[broadsword].computed_level`
   - Range modifier = lookup na size_speed_range pela distância em hex
   - Posture modifier = baseado em `runtime.posture` do atacante
   - Hit location penalty = ver dropdown
   - Cover penalty = ver obstáculos na linha
3. Mostra preview do modificador total antes de rolar.
4. Roll executa, resultado vai pro chat (já existe).

### Aplicação automática de dano

V2 hoje: GM ajusta HP manualmente.

V3:
1. Sistema rola dano → multiplica wound → subtrai DR (do `equipped_armor[location]`) → aplica.
2. Decrementa `runtime.hp_atual` automaticamente.
3. Triggers automáticos: shock penalty, major wound check, knockdown.
4. Atualiza token no mapa via WS.

---

## Open questions (decidir antes de começar V3)

1. **Esperar a V2 ser usada por todos os players?** (já foi, todos migraram). ✅ Pode começar.
2. **Permitir coexistência V2/V3?** Provavelmente sim, mesmo padrão V1↔V2.
3. **UI: editor V3 single-page como V2, ou wizard multi-step?** TBD.
4. **Animations**: dano aparece como número flutuante no token? Cool-to-have.

---

## Não fazer agora

Este doc é só placeholder. Implementação real só depois que tabletop estiver pronto e validado em sessões reais. Não comecar a V3 antes de ter feedback do tabletop em jogo.
