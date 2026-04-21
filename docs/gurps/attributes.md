# GURPS 4e — Atributos e Características Secundárias

> **Fonte:** *Basic Set: Characters*, páginas 14–21.
> **Arquivo de dados:** [`gurps/data/attributes.json`](../../gurps/data/attributes.json)
> **Modificado pela última vez:** 2026-04-21

---

## Visão geral

Toda ficha GURPS parte de **4 atributos primários** (ST, DX, IQ, HT), cada um com base 10 = "humano médio". Desses derivam **características secundárias** (HP, Will, Per, FP, Basic Speed, Basic Move, Dodge, Basic Lift, dano). O jogador paga pontos para elevar e recupera pontos reduzindo — cada ponto representa uma escolha concreta de orçamento.

### Escala de referência (humana)

| Valor | Interpretação |
|---|---|
| ≤6 | Incapacitante |
| 7 | Pobre (mínimo p/ "capaz") |
| 8–9 | Abaixo da média |
| 10 | Média |
| 11–12 | Acima da média |
| 13–14 | Excepcional |
| ≥15 | Impressionante |
| >20 | Divino / não-humano (requer autorização do GM) |

Para não-humanos, ler cada ponto acima/abaixo de 10 como **±10% sobre a norma da raça**.

---

## Atributos primários

Todos partem de **10** (grátis). Valores acima ou abaixo custam/devolvem pontos lineares por nível.

### ST — Strength (Força)
- **Custo:** ±10 pontos/nível
- **O que mede:** poder físico e massa. Essencial em combate corpo a corpo e para qualquer aventureiro (carregar, empurrar, arremessar).
- **Deriva:** Basic Lift (BL), dano básico (thrust/swing), HP, influencia Build.
- **Observação:** mais "aberto" que os demais — valores acima de 20 são comuns para monstros, animais grandes e robôs. Pode ter limitações: *No Fine Manipulators* (-40%), *Size* (-10% × Size Modifier, até -80%).

### DX — Dexterity (Destreza)
- **Custo:** ±20 pontos/nível
- **O que mede:** agilidade, coordenação e motricidade fina. Governa a maioria das skills atléticas, de combate, veículos e ofícios com toque delicado.
- **Deriva:** Basic Speed, Basic Move.
- **Limitação possível:** *No Fine Manipulators* (-40%).

### IQ — Intelligence (Inteligência)
- **Custo:** ±20 pontos/nível
- **O que mede:** criatividade, intuição, memória, percepção, razão, sanidade, força de vontade. Governa skills "mentais", ciências, interação social, magia.
- **Deriva:** Will, Per (Perception).
- **Notas de sentiência/sapientia:** IQ 0 = não-sentiente (-200 pts). IQ ≤5 = não-sapiente (não aprende skills tecnológicos nem idiomas).

### HT — Health (Vigor)
- **Custo:** ±10 pontos/nível
- **O que mede:** energia, vitalidade, resistência (veneno, doença, radiação), "grit". Vital para guerreiros de baixa tecnologia.
- **Deriva:** FP (Fatigue Points), Basic Speed, Basic Move.

---

## Características secundárias

Partem de uma **fórmula default** sobre os atributos e podem ser ajustadas pagando/recuperando pontos. Ajustá-las **não altera** o atributo-base correspondente.

| ID | PT | Fórmula default | Custo/nível | Notas |
|---|---|---|---|---|
| **HP** | Pontos de Vida | `= ST` | ±2 pts por ±1 | Realista: limitar a ±30% de ST. Supers/não-humanos isentos. |
| **Will** | Vontade | `= IQ` | ±5 pts por ±1 | Resistência a estresse mental, tortura, magia, psi. Max 20, min IQ-4 sem GM. |
| **Per** | Percepção | `= IQ` | ±5 pts por ±1 | Alerta geral; base de Sense Rolls. Max 20, min IQ-4 sem GM. |
| **FP** | Pontos de Fadiga | `= HT` | ±3 pts por ±1 | Realista: limitar a ±30% de HT. Sem teto superior (ao contrário de HT). `N/A` para Machine meta-trait. |
| **Basic Speed** | — | `(HT + DX) / 4`, sem arredondar | ±5 pts por ±0.25 | 5.25 > 5 para todo fim de desempate. Realista: alterar no máximo ±2.00. |
| **Basic Move** | — | `= Basic Speed` truncado | ±5 pts por ±1 yd/s | Velocidade de corrida sem carga (yd/s). |
| **Dodge** | Esquiva | `= Basic Speed + 3` truncado | — (não comprável isolado) | Reduzido pela encumbrance. |
| **Basic Lift (BL)** | — | `(ST × ST) / 5` lbs | — | Peso máx. sobre a cabeça com uma mão em 1 s. Arredondar p/ inteiro se ≥10 lbs. |
| **Damage (thrust/swing)** | Dano básico | Tabela p. 16 | — | `+1d` em ambos a cada 10 pts de ST acima de 100. |

### Exemplo
Para **HT 12, DX 15**:
- Basic Speed = (12 + 15) / 4 = **6.75**
- Basic Move = **6** (truncado)
- Dodge = **9** (6 + 3, truncado — *não* 6.75 + 3)

---

## Tabela de dano (ST → thrust/swing)

A tabela completa está em `attributes.json` (`damage_table`). Amostra:

| ST | thrust | swing |
|---|---|---|
| 10 | 1d-2 | 1d |
| 12 | 1d-1 | 1d+2 |
| 14 | 1d | 2d |
| 16 | 1d+1 | 2d+2 |
| 20 | 1d+2 | 3d+2 |

`ld` na extração do PDF é OCR incorreto de `1d` — foi corrigido na versão JSON.

---

## Encumbrance (carga)

Níveis (indexados 0–4) que reduzem Basic Move e Dodge conforme a carga relativa ao BL:

| Nível | Nome | Carga máx | Move × | Dodge |
|---|---|---|---|---|
| 0 | None | BL | 1.0 | base |
| 1 | Light | 2×BL | 0.8 | -1 |
| 2 | Medium | 3×BL | 0.6 | -2 |
| 3 | Heavy | 6×BL | 0.4 | -3 |
| 4 | Extra-Heavy | 10×BL | 0.2 | -4 |

Frações descartadas. Move e Dodge nunca caem abaixo de 1.

---

## Traços físicos relacionados (resumo)

Serão detalhados em `docs/gurps/physical_traits.md` numa etapa posterior. Incluem:

- **Handedness** (0 pts, canhoto é feature de 0 pts)
- **Build** (Skinny -5, Overweight -1, Fat -3, Very Fat -5, com tabela por ST)
- **Size Modifier (SM)** (tabela por dimensão)
- **Dwarfism** (-15 pts, SM -1), **Gigantism** (0 pts, SM +1)
- **Age** (sem custo; efeitos mecânicos em aging thresholds)
- **Appearance** (Horrific -24 a Transcendent +20)
- **Other Physical Features** (Fashion Sense, Mistaken Identity, etc.)

---

## Usos no sistema (roadmap)

1. **Validação no save da ficha**: garantir que os campos `atributos` e `sub_attributes` do `CharacterSheet` contenham apenas atributos válidos com fórmulas coerentes.
2. **Cálculo automático** das secundárias a partir das primárias no front-end (preview) e checagem no backend.
3. **Autocomplete** e tooltips com custos.
4. **Budget tracking**: validar que a soma de custos está dentro dos `pontos_de_ficha` da `Campanha`.
