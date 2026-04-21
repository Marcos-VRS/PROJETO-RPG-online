# Base de conhecimento GURPS 4ª Edição

> Documento vivo. Atualizar conforme o conhecimento for sendo extraído dos PDFs em `books/`. Objetivo final: servir como (1) referência para o agente tomar decisões informadas, (2) fonte de dados/validação para features (autocomplete, validação de ficha, cálculos automáticos), sem alterar o schema atual do `CharacterSheet`.

---

## O que é GURPS

GURPS (*Generic Universal RolePlaying System*) é um sistema de RPG de mesa **universal** e **genérico** da Steve Jackson Games, publicado em sua 4ª Edição em 2004. Diferentemente de sistemas amarrados a um cenário (D&D → fantasia medieval, Vampiro → horror gótico), GURPS fornece um conjunto de regras aplicável a qualquer gênero: fantasia, ficção científica, horror, histórico, moderno, super-heróis.

### Características centrais do sistema

1. **Baseado em 3d6** — quase toda rolagem é `3d6`, buscando valor **menor ou igual** a um atributo/skill. Resultado em sino (média 10,5) dá probabilidades estáveis e previsíveis.
2. **Compra de personagem por pontos** — jogadores têm um orçamento (ex: 100, 150, 250 pts) para distribuir entre atributos, vantagens, skills. Desvantagens devolvem pontos (até um limite).
3. **Quatro atributos primários**: ST (Força), DX (Destreza), IQ (Inteligência), HT (Vigor). Cada um custa 10 pts por ponto acima de 10.
4. **Atributos secundários** derivados: HP, Will, Per, FP, Basic Speed, Basic Move, Dodge.
5. **Vantagens / Desvantagens** — traços que custam ou devolvem pontos. Podem ter **modificadores** (Enhancements aumentam custo, Limitations reduzem).
6. **Skills** — perícias com nível relativo a um atributo (ex: *Broadsword (DX/A)* custa mais conforme sobe).
7. **Combat** — baseado em turnos, com manobras (Attack, All-Out Attack, Defend, Feint…), ataques ativos e defesas (Parry, Block, Dodge).
8. **Dano** — calculado via thrust/swing baseado em ST, com tipos de dano (cortante, perfurante, esmagador, etc.) que interagem com armadura e locais do corpo.

### O papel do mestre (GM) e dos jogadores

- **GM** narra o mundo, arbitra regras, controla NPCs e ambiente. Precisa de: mapa dinâmico, tokens, chat, acesso às fichas dos jogadores, gerador de encontros/rolagens secretas.
- **Jogadores** controlam personagens. Precisam de: ficha editável dentro das regras, rolagem de dados, chat, visualização do mapa, inventário.

Isso mapeia diretamente nas features que o projeto precisa ter.

---

## Relação com o código atual

Em `gurps/models.py`, o `CharacterSheet` guarda praticamente toda a informação de GURPS como **`JSONField` livre**:

- `atributos`, `sub_attributes`
- `advantages`, `disadvantages`
- `skills`
- `equipment_melee`, `equipment_ranged`, `equipment_armor`
- `maneuvers_melee`, `maneuvers_ranged`, `maneuvers_defense`

**Consequência**: não há validação estrutural — uma vantagem inexistente, com custo errado ou nome grafado de outra forma é aceita. O catálogo construído neste documento (e artefatos derivados) é a base para adicionar validação sem alterar o schema.

Estratégia: **não migrar para tabelas relacionais agora** (mudança estrutural, exige aprovação; risco de perda de dados em produção). Em vez disso:

1. Construir o catálogo como **dados estáticos** (Markdown aqui + JSON/YAML em `gurps/data/` quando necessário).
2. Usar o catálogo para validação no save da ficha e autocomplete no front.
3. Se no futuro o usuário aprovar a migração para relacional, o catálogo já está pronto como fonte das tabelas.

---

## Livros disponíveis (em `books/`, não commitados)

| Livro | Conteúdo | Prioridade |
|---|---|---|
| `Gurps - Basic Set 4Th Characters.pdf` | Criação de personagens: atributos, vantagens, desvantagens, skills, modificadores, técnicas, templates. **O mais importante para a ficha.** | Alta — primeiro |
| `SJG01-0002 - GURPS 4e - Basic Set - Campaigns (OEF).pdf` | Regras de jogo em si: combate, dano, ferimentos, movimento, mágia básica, regras do GM. | Alta — segundo |
| `GURPS 4e - Powers.pdf` | Sistema de poderes (super-heróis, habilidades extraordinárias) — expansão de vantagens. | Média — após Basic Set |
| `GURPS - 4th - GM Screen.pdf` | Tabelas de referência rápidas (modificadores, alcance, etc.). | Baixa — consulta durante implementação |

---

## Plano de catalogação

Executado em etapas, cada uma com deliverable. Cada etapa precisa de validação do usuário antes de ir pra próxima.

1. **Etapa 1 — Atributos e características secundárias** (Basic Set Characters, ~20 pág)
   - Deliverable: `docs/gurps/attributes.md` + JSON estruturado com fórmulas de derivação.
2. **Etapa 2 — Vantagens** (Basic Set Characters, ~80 pág)
   - Deliverable: `docs/gurps/advantages.md` + `gurps/data/advantages.json` (nome, custo base, variantes, modificadores permitidos, página de referência).
3. **Etapa 3 — Desvantagens** (~60 pág)
   - Deliverable: `docs/gurps/disadvantages.md` + `gurps/data/disadvantages.json`.
4. **Etapa 4 — Skills** (~80 pág)
   - Deliverable: `docs/gurps/skills.md` + `gurps/data/skills.json` (nome, atributo base, dificuldade, pré-requisitos, especializações).
5. **Etapa 5 — Modificadores (Enhancements & Limitations)** (~30 pág)
   - Deliverable: `docs/gurps/modifiers.md` + `gurps/data/modifiers.json`.
6. **Etapa 6 — Combate e dano** (Basic Set Campaigns)
   - Deliverable: `docs/gurps/combat.md` com regras essenciais para o backend calcular/validar.
7. **Etapa 7 — Powers** (livro Powers, se/quando o usuário quiser suporte)
   - Deliverable: incremento em `advantages.json` com poderes derivados.

---

## Registro de etapas concluídas

### Etapa 1 — Atributos e características secundárias
- **Status:** entregue, aguardando validação do usuário
- **Data:** 2026-04-21
- **Fonte:** *Basic Set: Characters*, pp. 14-21
- **Entregáveis:**
  - [`docs/gurps/attributes.md`](gurps/attributes.md) — referência humana
  - [`gurps/data/attributes.json`](../gurps/data/attributes.json) — dados estruturados
- **Cobre:** 4 atributos primários (ST/DX/IQ/HT) + secundários (HP, Will, Per, FP, Basic Speed, Basic Move, Dodge, Basic Lift, dano) + tabela completa de dano + níveis de encumbrance + escala de interpretação (humana e não-humana)
- **Não cobre** (fica para etapa posterior): traços físicos (Build, Size Modifier, Dwarfism/Gigantism, Age, Appearance), Handedness, Fashion Sense e demais "other physical features". Propor nova etapa **"1b — Traços físicos"** se o usuário quiser manter escopo enxuto por etapa.
