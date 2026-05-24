# Fluxo de Combate no Tabletop — passo a passo

> **Propósito:** descrever EXATAMENTE como uma rodada de combate funciona no roll3d6 com o mapa, da iniciativa até o registro do dano. Serve de referência ao implementar a UI.
> **Pressupõe:** [`TABLETOP_MAP_PLAN.md`](TABLETOP_MAP_PLAN.md) (arquitetura) e [`GURPS_TABLETOP_RULES.md`](GURPS_TABLETOP_RULES.md) (regras).

---

## A. Início do combate

### A.1 — GM coloca tokens no mapa

1. GM abre a campanha, escolhe o mapa ativo (botão "Mapa" na side nav).
2. Pra cada combatente, GM clica em "Adicionar token" → escolhe ficha (V2 ou quick NPC) → arrasta pra posição inicial.
3. Token nasce no hex onde foi solto. GM ajusta facing arrastando a "seta" do token.

### A.2 — Cena cria iniciativa

1. GM abre o "Controle de cena" (menu lateral GM).
2. Marca quem está em cena (já existe esse fluxo).
3. Sistema **ordena automaticamente** por `Basic Speed` (truncado, depois decimal pra desempate). Tie → DX. Tie → roll oculto.
4. GM pode reordenar manualmente arrastando.

### A.3 — Turno atual ativo

1. UI mostra "Turno: <nome>" na barra superior (já existe).
2. Token do turno atual ganha **highlight visual no mapa** (borda dourada pulsante).
3. Apenas o **owner do token** + **GM** podem mover/agir naquele turno.
4. Os demais players veem mas não interagem.

---

## B. Turno de um personagem (1 segundo in-game)

### B.1 — Player escolhe manobra

Side nav esquerda ganha um botão novo: **🗡 MANOBRA**. Click abre uma lista das 13 manobras principais:

| Manobra | Move permitido | Defesa permitida |
|---|---|---|
| Do Nothing | 0 | qualquer |
| Move | full (=Basic Move) | qualquer |
| Change Posture | 0 | qualquer |
| Aim | step (1) | qualquer |
| Evaluate | step | qualquer |
| Attack | step | qualquer |
| Feint | step | qualquer |
| All-Out Attack | half/full | **NENHUMA** |
| All-Out Defense | step | dobrada |
| Move and Attack | full | só Dodge |
| Ready | step | qualquer |
| Concentrate | step | qualquer |
| Wait | none | qualquer |

Cada manobra mostra ícone + nome + 1 linha de descrição. Quando selecionada, o mapa fica em modo "executando manobra X".

### B.2 — Move

Sistema rastreia movimento:
1. Token fica "destacável". Mouse drag arrasta.
2. À medida que o token passa por hexes, conta **distância acumulada** (em hex).
3. Limite = Basic Move efetivo (já com encumbrance).
4. Counter no canto da tela: `Move: 3 / 6 m`.
5. Ao soltar, broadcast `map_token_move`.

### B.3 — Step (toda manobra que não é Move/AoA)

Sistema permite 1 hex de movimento livre antes ou depois da ação principal. Visual: highlight os 6 hexes adjacentes ao token quando manobra é selecionada.

### B.4 — Attack (e variantes)

1. Player seleciona "Attack" (ou aoa_*).
2. UI destaca **hexes alcançáveis** baseado no Reach da arma equipada.
3. Player clica num token-alvo dentro do alcance.
4. Modal "Ataque" abre com pré-preenchidos:
   - Skill efetivo (skill do char + range modifier + posture modifier + facing modifier)
   - Hit location dropdown (default Torso)
   - Bônus / Penalty extras (manual)
5. Player clica "Rolar". Roll executa server-side, resultado vai pro chat.
6. Se acertou → server marca state "esperando defesa do <alvo>".

### B.5 — Defesa do alvo

1. Owner do token alvo (ou GM se for NPC) recebe notificação no chat e modal "Defender contra <ataque>".
2. Opções: Dodge / Parry / Block (greyed out se não tem skill).
3. Aplica modificadores (facing, retreat?, all-out defense?).
4. Player rola. Resultado define se acerto se concretiza.

### B.6 — Dano

1. Se defesa falhou, atacante rola dano automaticamente (ou clica "rolar dano" se preferir manual).
2. Sistema aplica: dano − DR do alvo = penetration → × wounding multiplier (pelo damage type) = HP perdido.
3. Servidor decrementa `runtime_stats.hp_atual` do alvo via `adjust_character_vitals` (já existe).
4. Token-alvo atualiza HP bar em tempo real (já existe via WS).
5. Checks adicionais (server-side):
   - Shock penalty pro próximo turno
   - Major wound? HT roll → stunned/knockdown
   - Major wound em local específico (skull, vitals, etc.)
   - HP ≤ 0 → checks de morte / unconsciousness
6. Status effects aplicados ao token aparecem como ícones.

### B.7 — Fim do turno

Player clica "Próximo turno" (ou o GM avança). Token perde highlight. Próximo token na ordem ganha.

---

## C. Cenas múltiplas

GURPS não tem múltiplas cenas simultâneas, mas usuário pode querer (party split). Modelo atual já suporta: cada cena tem `character_ids` próprio e `current_turn_id`. Cada cena tem **seu próprio mapa ativo** (ou compartilha o mesmo).

Implementação: `Scene.active_map_id` → `CampanhaAssets.id`.

---

## D. Estados especiais visualizados no token

Cada um vira ícone pequeno (16px) no canto do token:

| Estado | Ícone (proposta) | Origem | Efeito |
|---|---|---|---|
| Standing | (sem ícone — default) | — | — |
| Crouching | 🟦 (quadrado pequeno) | Change Posture | -2 melee atk/def |
| Kneeling | 🔻 | Change Posture | -2 atk, -2 def, -2 ranged a hit |
| Sitting | 🪑 | Change Posture | sem move |
| Lying down | 🛌 | Change Posture / Knocked down | crawl, -4 atk |
| Aiming | 🎯 | Aim maneuver acumulando | +Acc bônus |
| Stunned | 💫 | Major wound fail | só Do Nothing, defesas -4 |
| Bleeding | 🩸 | cut/imp/pi com penetração | HT/min, perde HP |
| Unconscious | 😵 | HP ≤ 0 + HT fail | sem ações |
| Grappled | 🤝 | Grapple | -4 DX/skills |
| Crippled arm | 🩼 | Dano > HP/2 em braço | sem usar braço |
| Crippled leg | 🦽 | Dano > HP/2 em perna | sem mover normal |
| Major wound | ⚠️ | Dano ≥ HP/2 num hit | trigger HT roll |

Implementação: `token.status_effects = ["stunned", "bleeding"]` (array de strings).

---

## E. Régua, medidas e visualizações auxiliares

### E.1 — Régua de distância

Toolbar tem ícone 📏. Click ativa modo régua. Click 1 + click 2 = mostra distância em hexes / metros.

### E.2 — Highlight de Reach ao selecionar token

Quando token está selecionado e manobra de ataque está ativa, hexes alcançáveis aparecem com tint verde claro.

### E.3 — Movement preview

Ao arrastar um token, sistema desenha:
- **Trajetória**: linha pontilhada do hex original ao atual.
- **Custo**: "3 hex" no cursor.
- **Limite**: se exceder Basic Move, cor da linha vira vermelha.

### E.4 — LOS (linha de visão)

Simplificação v1: GM coloca "obstáculos" como retângulos no layer drawing. Não há cálculo automático de LOS. Atacante a ranged confia: "tem como ver dali?". GM aprova.

v2 talvez: drawings com flag `blocks_los = true` automatizam.

### E.5 — Cover

GURPS p407: cover dá penalty no atacante.

| Cover | Penalty |
|---|---|
| Light cover (50% body) | -2 |
| Heavy cover (only head exposed) | -5 |
| Full cover (nothing exposed) | impossível atingir |

Implementação v1: manual (GM aplica modifier). v2: automatizar baseado em obstáculos no path.

---

## F. Magia e Concentração

Algumas magias precisam **Concentrate** maneuver (1 turno) antes de ativar. Sistema marca token com ícone "🧘 Conjurando: <spell>".

Após N turnos de Concentrate, magia dispara: rola Skill da magia, aplica efeito (dano, área, etc.).

Implementação v1: GM trata manualmente. v2: parser de spells do `spells.json`.

---

## G. Eventos do chat

Cada ação no mapa gera mensagem no chat com formato padronizado:

```
[Hector] Move: (5,3) → (7,4). 3 hex / 6 m disponíveis.
[Hector] Attack (Sword, skill 14) → Goblin. NH 14 + 0 = 14, rolou 9 = sucesso (margem 5).
[Goblin] Dodge (8) vs ataque margem 5: rolou 12 = falha por 4.
[Hector] Damage: 1d+2 cut → rolou 5, DR 2 = 3 penetrating × 1.5 cut = 4 HP. Goblin: 10/14 HP.
[Goblin] Major wound? HP/2 = 7, dano 4 < 7. Sem check.
```

Mensagens com tipo `roll`, color-coded (acerto verde, falha cinza, etc.). Aproveitar a infra atual.

---

## H. Comandos de teclado (atalhos)

Quando token está selecionado:

| Tecla | Ação |
|---|---|
| `1`-`5` | Mudar postura (1=stand, 2=crouch, 3=kneel, 4=sit, 5=lie) |
| `F` | Mudar facing (gira sentido horário) |
| `Shift+F` | Mudar facing anti-horário |
| `M` | Manobra Move |
| `A` | Manobra Attack |
| `D` | Manobra All-Out Defense |
| `Space` | Next turn (GM only) |
| `R` | Toggle régua |
| `Esc` | Desselecionar / cancelar manobra |

---

## I. Casos especiais GURPS que afetam UI

### I.1 — Reach 1, 2 (arma versátil)
Algumas armas (lança, alabarda) têm múltiplos reaches. UI mostra "Reach: 1, 2" e highlight inclui ambos os anéis de hex.

### I.2 — Close combat
Reach C = hex do próprio personagem. Permite ataque com arma curta a oponente no MESMO hex (rara situação: derrubaram, vc parou em cima).

### I.3 — Múltiplos atacantes em close combat
Quando 2+ tokens estão atacando 1 mesmo alvo no mesmo hex, sistema oferece +1 hit por aliado extra (max +5).

### I.4 — Mounted combat
Token a cavalo é um cluster de 2 hexes (SM +1 cavalo + rider em cima). Trate como "veículo + passageiro" — feature de v2.

### I.5 — Aerial / underwater
Mapa 2D pode anotar altitude/profundidade como label do token ("alt 5m"). Sistema não modela 3D na v1.

---

## J. Estados que persistem entre turnos

Token tem `runtime_state`:

```json
{
  "aiming_accumulated": 2,        // bônus de Aim acumulado (max +2 sobre Acc)
  "shock_penalty_next_turn": -3,  // penalty pro próximo turno
  "rapid_fire_recoil": 0,         // recoil de full-auto
  "concentrating_on": "spell_fireball",  // se em Concentrate
  "wait_trigger": "any enemy in reach"   // se em Wait
}
```

Server resolve ao começo de cada turno (limpa shock anterior, decrementa aim se manobra mudou, etc.).

---

## K. Que NÃO está no escopo da v1

- Cálculo automático de LOS (linha de visão por obstáculos)
- Cálculo automático de cover
- Magia automatizada (spells aplicam efeito sozinhos)
- IA de NPCs (autonomous turns)
- Combate naval/aéreo 3D
- Fog of war dinâmico (só fog estática controlada pelo GM)
- Combate mass-scale (>20 tokens lerdo até validar perf)

Tudo isso vira v2/v3.

---

## L. Métricas de sucesso da implementação

Quando v1 estiver pronto, validamos com:
1. ✅ GM cria mapa, ajusta grid em <30 segundos.
2. ✅ GM coloca 4 tokens (party) + 6 tokens (inimigos) em <2 minutos.
3. ✅ Player move token e sistema mostra distância em hex/metro.
4. ✅ Ataque flow completo (Attack → Defesa → Dano → HP atualiza) em <30s.
5. ✅ Todos veem cada ação em tempo real (<1s latência).
6. ✅ Round de combate completo (party + inimigos) em <5 min.
