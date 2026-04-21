# Claude Code — Contexto do projeto roll3d6 RPG

Este arquivo é carregado automaticamente em toda conversa deste repositório. Ele serve de índice para os documentos detalhados em `docs/`, que devem ser lidos conforme a tarefa exigir.

## Documentos

- [Estado da sessão — última parada e plano de continuação](docs/SESSION_STATE.md) — **leia primeiro ao retomar**
- [Prompt do agente — missão, papel, stack, responsabilidades](docs/AGENT_PROMPT.md)
- [Arquitetura RAG — busca semântica sobre regras e estado do jogo](docs/RAG_ARCHITECTURE.md)
- [Base de conhecimento GURPS 4e — visão geral + plano de catalogação](docs/GURPS_KNOWLEDGE.md)
  - [Atributos e características secundárias](docs/gurps/attributes.md) — dados em `gurps/data/attributes.json`

Novos documentos (arquitetura, roadmap, decisões, catálogos específicos em `docs/gurps/`) serão criados sob demanda e indexados aqui.

## Regras invioláveis

Resumo rápido — detalhes em `docs/AGENT_PROMPT.md`:

1. **Nunca altere models removendo campos ou informação.** Site em produção; fichas existentes devem permanecer intactas. Migrações são aditivas ou transformadoras, nunca destrutivas.
2. **Não recomece do zero.** Evolua o código existente.
3. **Mudanças estruturais exigem confirmação do usuário** antes da implementação (nova stack front, troca de framework, reorganização de apps, troca de banco).
4. **Priorize desempenho e baixo consumo de dados.** Tráfego no Google Cloud é pago.
5. **Trabalho por partes.** Conclua e valide uma etapa antes de avançar.
6. **Mantenha os docs atualizados.** Quando uma diretriz mudar, atualize o arquivo `.md` correspondente em vez de criar um novo.

## Comunicação

- Idioma: português (pt-BR).
- Usuário opera em Windows 10 + PowerShell 5.1; comandos sugeridos devem ser compatíveis.
- Deploy e acesso à VM: ver memória do agente (`/memory/project_infra_gcp.md`).
