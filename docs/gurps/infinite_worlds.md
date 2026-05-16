# GURPS 4e — Infinite Worlds (Cap 20 Campaigns, pp 188-211)

> **Fonte:** *Basic Set: Campaigns*, capítulo 20.

Cap 20 apresenta **Infinite Worlds**, o setting **incluído** no Basic Set. Você não é obrigado a usar — é uma campanha pronta que GMs podem rodar sem trabalho de world-building.

## Premissa

No 21º século, o **Homeline** (Earth alternativa = nosso mundo) descobre **parachronic travel**: máquinas que projetam pessoas/coisas para timelines paralelas. A corporação privada **Infinity Unlimited** controla a tecnologia, com supervisão governamental do **ISWAT** (Interworld Service for Worlds and Timeline-protection).

**Centrum** é um Earth paralelo rival que também tem tecnologia parachrônica e quer remodelar todas as timelines à sua imagem.

## Worlds Notáveis

### Homeline
Earth como conhecemos (modificada por presença secreta de I.U.). TL 8.

### Centrum
Earth utópica/distópica unificada por governo único; TL 8+. Inimigos principais de I.U.

### Roma Æterna
Império Romano nunca caiu; ainda existe TL 4-5 em 2050. Magia funciona (mana baixa).

### Reich-5
Earth onde Nazistas venceram WWII e ocuparam globalmente. TL 7. Horror premise.

### Caliph
Earth onde Islã se espalhou pra todo planeta; mahdi-esque. TL 5.

### Lucifer
Earth pós-apocalíptica com supernatural revealed; demons walk the earth. TL 7.

### Cliffhanger
Earth pulp 1936; aviadores aventureiros, dirigíveis, "lost worlds". TL 6.

### Coventry
Earth com magic dominante (TL 4 + Magery widespread).

### Britannica-3
Império britânico nunca caiu; ainda controla 1/3 do mundo em 2050. TL 8 com colonialismo.

### Yrth
Fantasy world (campanha GURPS Banestorm); pessoas terrestres "kidnapped" via banestorm. TL 3-4 + magic.

## Adversaries (pp 206-209)

### Centrum agents
Highly trained, technologically advanced. Same TL as I.U. but more centralized control. PCs frequently face Centrum operatives.

### Parachronozoids
Entidades hostis que vivem em parachronic space; só ataca em jump. Random encounter table.

### Reich-5 SS
Se PCs visitam Reich-5, encontros com nazistas equipados.

### Lucifer demons
Demônios literais; require holy power ou specific weapons pra derrotar.

## Time Travel

Em geral **time travel não é possível** em Infinite Worlds (só world-jumping). Algumas exceções narrativas:
- **Timeline shifts**: alguns eventos podem alterar timelines
- **Lost histories**: timelines onde história divergiu = "passado alternativo"

Real time travel é tópico de outros settings.

## Para o app

Infinite Worlds é setting opcional. Para o app desktop:
- **Não precisa codificar diretamente** — é content/lore, não mecânica
- Se quiser, criar tabela de NPCs notáveis (Infinity directors, Centrum agents, etc.) como JSON
- Mais relevante: o framework de **multiple settings** que o app permite. Cada `Campanha` pode ter `setting` field referenciando world data.

Para implementação, basta deixar `Campanha.descricao` aberta pra que GM escreva o setting. O app não precisa restringir.
