# FinGuard — Backlog, DoR e critério de aceite

Hoje: 27/07. Entrega: 30/07. Sem mais planejamento depois deste documento — a partir daqui é execução.

## Definition of Ready (DoR) — já cumprido, confirma antes de começar a codar

- [x] Dataset disponível (`docs/dataset_finguard_desafio_3 (3).csv`)
- [x] Política interna disponível (`docs/KS_POLITICA_INTERNA (2).pdf`)
- [x] Guardrail Bedrock provisionado e testado (ID + version 1)
- [x] Repo git criado, PRD/SPECS/ADR/COMPLIANCE commitados
- [x] Modelo baseline definido (Nova Micro em todos os agentes no Bedrock; ajuste pontual depois)
- [x] Client de LLM abstraído definido (`OpenAIClient` dev / `BedrockClient` prod)
- [ ] Ambiente Python local configurado (venv + `requirements.txt`) — primeiro passo da implementação, ainda não feito
- [ ] `OPENAI_API_KEY` pessoal disponível no `.env` local
- [ ] Confirmação por escrito da organização sobre uso da conta de dev do projeto (não bloqueia começar a codar, mas fica pendente — ver `COMPLIANCE.md` §2)

## Backlog — Nível 1: Classificador

| # | Tarefa | Critério de aceite |
|---|---|---|
| 1.1 | Setup do projeto (estrutura `src/finguard/`, `requirements.txt`, `.env.example`, venv) | `python -m finguard.run --help` roda sem erro |
| 1.2 | Schemas Pydantic de entrada/saída do `agente_triagem` (SPECS §5) | Schema rejeita valor fora do enum de categoria/produto/sentimento/urgência |
| 1.3 | `LLMClient` (interface) + `OpenAIClient` | Chamada de teste simples retorna resposta do modelo em `OPENAI_MODEL_TRIAGEM` |
| 1.4 | Prompt + lógica do `agente_triagem`, com regra dura de urgência Crítica forçada por código (fraude/Bacen/Procon/vulnerabilidade) | Rodando o exemplo do desafio + 3 casos do dataset (incluindo 1 caso Banco Central) retorna JSON no schema certo, urgência Crítica correta nos casos que exigem |
| 1.5 | Loop que processa o CSV inteiro e salva saída `.json` | Processa as ~500 linhas sem erro fatal |

## Backlog — Nível 2: Orquestrador (LangGraph)

| # | Tarefa | Critério de aceite |
|---|---|---|
| 2.1 | Grafo `start → triagem → risco → relatorio → end` (sem guardrail ainda) | Compila e roda ponta a ponta para 1 reclamação de teste |
| 2.2 | RAG da política (chunking por seção, ~15 chunks) + `agente_risco` | 5 casos de teste manuais (baixa/média/alta/crítica + 1 ambíguo) retornam `nivel_risco` e `clausula_referencia` coerentes com a política |
| 2.3 | `agente_relatorio` (dashboard + críticas + recomendações) | Relatório `.html` + `.json` gerado a partir do dataset completo; soma por categoria bate com o total |
| 2.4 | Logging por agente (entrada, saída, tempo) | Log mostra, por reclamação, os 3 registros de agente com timestamp e duração |

## Backlog — Nível 3: Escudo de Compliance

| # | Tarefa | Critério de aceite |
|---|---|---|
| 3.1 | Guardrail de entrada como primeiro nó do grafo | 100% dos ~10 casos de prompt injection identificados no dataset são bloqueados; qualquer caso que passar é documentado e o guardrail ajustado antes do evento |
| 3.2 | Resposta de bloqueio padrão (fixa, português, sem eco da instrução, sem detalhe interno) | Testada nos mesmos casos de 3.1 |
| 3.3 | Guardrail de saída + regex de reforço (CPF, número de conta) | Reclamação sintética de teste com CPF no texto → relatório final não contém o CPF em nenhum campo |
| 3.4 | ADR revisado pós-implementação | ADR bate com o que foi de fato implementado, sem divergência |
| 3.5 | Bateria de validação com `LLM_PROVIDER=bedrock` na conta do projeto (Vivo/Zup) | Mesmos casos de teste dos níveis 1–3 rodados no Bedrock; divergência de comportamento vs. baseline OpenAI documentada e prompt ajustado se necessário |

## Backlog — Pitch e demo

| # | Tarefa | Critério de aceite |
|---|---|---|
| P.1 | Roteiro de pitch (5 min) com 1 caso de injection para rodar ao vivo | Ensaiado, cronometrado, cabe em 5 min |
| P.2 | Resposta pronta para a pergunta obrigatória da banca ("quais ferramentas de IA você usou e como contribuíram") | Resposta escrita cobrindo Bedrock Guardrails, RAG, LangGraph, Nova Micro/Claude Haiku |
| P.3 | Checklist do dia do evento | Inclui: gerar relatório final antes de desligar, deletar Guardrail/recursos da conta AWS ao término (ver `COMPLIANCE.md` §3) |

## Definition of Done (DoD)

Já definida em [`SPECS.md`](./SPECS.md) §8 — não duplicar aqui, é a referência única.
