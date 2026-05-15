# Claude Code — Contexto do projeto roll3d6 RPG

Este arquivo é carregado automaticamente em toda conversa deste repositório. Ele serve de índice para os documentos detalhados em `docs/`, que devem ser lidos conforme a tarefa exigir.

## Pivô em andamento (decidido 2026-05-14)

O produto migra de **SaaS hospedado no GCP** para **aplicativo desktop com dois cliques** (Windows). SQLite no lugar de Postgres, in-memory channel layer no lugar de Redis, Cloudflare Quick Tunnel para o multiplayer. SaaS GCP entra em sunset gradual. Detalhes em [`docs/AGENT_PROMPT.md`](docs/AGENT_PROMPT.md) e [`docs/DESKTOP_DISTRIBUTION.md`](docs/DESKTOP_DISTRIBUTION.md).

## Documentos

- [Estado da sessão — última parada e plano de continuação](docs/SESSION_STATE.md) — **leia primeiro ao retomar**
- [Prompt do agente — missão, papel, stack, responsabilidades](docs/AGENT_PROMPT.md)
- [Arquitetura de distribuição desktop — instalador, launcher, túnel, empacotamento](docs/DESKTOP_DISTRIBUTION.md)
- [Arquitetura RAG — em hibernação até voltar com vector store SQLite-friendly](docs/RAG_ARCHITECTURE.md)
- [Base de conhecimento GURPS 4e — visão geral + plano de catalogação](docs/GURPS_KNOWLEDGE.md)
  - [Atributos e características secundárias](docs/gurps/attributes.md) — dados em `gurps/data/attributes.json`

Novos documentos (arquitetura, roadmap, decisões, catálogos específicos em `docs/gurps/`) serão criados sob demanda e indexados aqui.

## Regras invioláveis

Resumo rápido — detalhes em `docs/AGENT_PROMPT.md`:

1. **Nunca altere models removendo campos ou informação.** Fichas existentes precisam migrar intactas do GCP para o SQLite do desktop. Migrações são aditivas ou transformadoras, nunca destrutivas.
2. **Não recomece do zero.** Evolua o código existente.
3. **Mudanças estruturais exigem confirmação do usuário** antes da implementação (troca de banco, framework JS pesado, troca de empacotamento, novo serviço externo).
4. **Sem dependência de Python/Postgres/Redis pré-instalados no usuário final.** O instalador entrega tudo bundleado, dois cliques, zero terminal.
5. **Priorize desempenho e baixo consumo de dados.** O app roda na máquina do usuário; banda do Cloudflare Tunnel tem limites.
6. **Trabalho por partes.** Conclua e valide uma etapa antes de avançar.
7. **Mantenha os docs atualizados.** Quando uma diretriz mudar, atualize o arquivo `.md` correspondente em vez de criar um novo.

## Comunicação

- Idioma: português (pt-BR).
- Usuário opera em Windows 11 + PowerShell; comandos sugeridos devem ser compatíveis.
- Sandbox do Claude Code não consegue elevar UAC — ações que exigem admin são instruídas ao usuário.
