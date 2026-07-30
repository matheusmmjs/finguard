# FinGuard — Backlog, DoR e critério de aceite

Hoje: 27/07. Entrega: 30/07. Sem mais planejamento depois deste documento — a partir daqui é execução.

## Definition of Ready (DoR) — já cumprido, confirma antes de começar a codar

- [x] Dataset disponível (`docs/dataset_finguard_desafio_3 (3).csv`)
- [x] Política interna disponível (`docs/KS_POLITICA_INTERNA (2).pdf`)
- [x] Guardrail Bedrock provisionado e testado (ID + version 1)
- [x] Repo git criado, PRD/SPECS/ADR/COMPLIANCE commitados
- [x] Modelo baseline definido (Nova Micro em todos os agentes no Bedrock; ajuste pontual depois)
- [x] Client de LLM abstraído definido (`OpenAIClient` dev / `BedrockClient` prod)
- [ ] Ambiente Python local configurado (venv + `pyproject.toml`) — primeiro passo da implementação, ainda não feito
- [ ] `OPENAI_API_KEY` pessoal disponível no `.env` local
- [ ] Confirmação por escrito da organização sobre uso da conta de dev do projeto (não bloqueia começar a codar, mas fica pendente — ver `COMPLIANCE.md` §2)

## Backlog — Nível 1: Classificador — ✅ CONCLUÍDO (validado com chamada real, 27/07)

| # | Tarefa | Critério de aceite | Status |
|---|---|---|---|
| 1.1 | Setup do projeto (estrutura `src/finguard/`, `pyproject.toml`, `.env.example`, venv) | `python -m finguard.run --help` roda sem erro | ✅ |
| 1.2 | Schemas Pydantic de entrada/saída do `agente_triagem` (SPECS §5) | Schema rejeita valor fora do enum de categoria/produto/sentimento/urgência | ✅ |
| 1.3 | `LLMClient` (interface) + `OpenAIClient` | Chamada de teste simples retorna resposta do modelo em `OPENAI_MODEL_TRIAGEM` | ✅ |
| 1.4 | Prompt + lógica do `agente_triagem`, com regra dura de urgência Crítica forçada por código (fraude/Bacen/Procon/vulnerabilidade) | Rodando o exemplo do desafio + 3 casos do dataset (incluindo 1 caso Banco Central) retorna JSON no schema certo, urgência Crítica correta nos casos que exigem | ✅ |
| 1.5 | Loop que processa o CSV inteiro e salva saída `.json` | Processa as ~500 linhas sem erro fatal | ✅ (parse das 500 linhas confirmado; chamada real com `--limit 5` validada pelo usuário em 27/07) |

**Achado corrigido durante a validação real**: o modelo, sem instrução explícita, classificou uma ameaça condicional de escalar pro Banco Central (`REC-2026-00509`) como urgência Crítica — mesmo padrão do exemplo oficial do desafio, que espera Alta. Prompt do `agente_triagem` foi ajustado com a distinção explícita (já registrado ≠ ameaça futura) e o exemplo oficial como âncora. Reconfirmado com nova chamada real: corrigido.

**Regra de qualidade adicionada nesta fase**: cobertura de testes ≥ 90% obrigatória (`pyproject.toml`, `--cov-fail-under=90`), aplicada por padrão em qualquer `pytest`, mais workflow de CI em `.github/workflows/tests.yml`. Ver `SPECS.md` §9. Cobertura atual: 99%.

**Rastreamento de custo adicionado nesta fase** (ver `SPECS.md` §10 e `docs/COST_REPORT.md`, gerado automaticamente por `python -m finguard.cost_report`). Nota de transparência: as ~10 chamadas reais feitas durante a validação do Nível 1 *antes* dessa instrumentação existir (os dois `--limit 5` e a verificação isolada do `REC-2026-00509`) não ficaram no log com token exato — não são perda relevante (mesmo modelo `gpt-4o-mini`, mesma ordem de grandeza de tokens do registro real capturado depois, ~700 tokens por chamada, bem abaixo de US$ 0,01 no total), mas fica registrado que o log só é completo a partir daqui.

## Backlog — Nível 2: Orquestrador (LangGraph)

| # | Tarefa | Critério de aceite |
|---|---|---|
| 2.1 | ✅ Grafo `start → triagem → risco → end` por reclamação (sem guardrail ainda) — ver nota de desvio abaixo | Validado com LangGraph real (não fake) em 3 reclamações do dataset |
| 2.2a | ✅ RAG da política: chunking (15 chunks) + embeddings (dual client) + índice FAISS | Validado com chamada real: reclamação de Banco Central → seções 4.3+2.4; cartão → 3.1; seguro → 3.5; CPF/LGPD → seção 5. Todos corretos |
| 2.2b | ✅ `agente_risco` usando o RAG acima | 5 casos de teste manuais (baixa/média/alta/crítica + 1 ambíguo) retornam `nivel_risco` e `clausula_referencia` coerentes com a política |
| 2.3 | ✅ `agente_relatorio` (dashboard + críticas + recomendações) | Relatório `.html` + `.json` gerado a partir do dataset completo; soma por categoria bate com o total |
| 2.4 | ✅ Logging por agente (entrada, saída, tempo) | Log real: 6 entradas (2 agentes x 3 reclamações), `reclamacao_id` + `timestamp` + `tempo_ms` em cada uma |

## Nível 2 — status: todas as tarefas concluídas. Pendência antes do Nível 3

✅ `run.py` (CLI) já chama o pipeline completo (`pipeline.processar_completo`) por padrão — `.json` + `.html` + `logs_execucao.json` + `bloqueadas.json`. `--so-triagem` mantém o caminho antigo (só Nível 1) pra depuração isolada do classificador. Validado com `python -m finguard.run --limit 5` real.

**RAG (2.2a) concluído** — ver ADR 0002 e `src/finguard/rag/`. Embeddings: `text-embedding-3-small` (dev) / `amazon.titan-embed-text-v2:0` (Bedrock), índice FAISS `IndexFlatIP`. Custo por consulta: ~US$ 0,0000003 (irrelevante).

**Desvio deliberado do diagrama de exemplo do desafio**: o diagrama oficial (nível 2/3) mostra `agente_relatorio` como nó do grafo, depois de `agente_risco`, por reclamação. Isso não faz sentido pro que `agente_relatorio` de fato calcula — dashboard, distribuição por categoria/produto/urgência, lista de críticas — que é agregado sobre **o lote inteiro**, não sobre 1 reclamação por vez. O próprio desafio chama esse diagrama de "estrutura mínima" e diz explicitamente: "os participantes são encorajados a ir além da estrutura mínima". Decisão: o grafo LangGraph processa 1 reclamação por vez até `agente_risco`; `agente_relatorio` roda 1 vez, fora do grafo, depois que todas as reclamações do lote passaram por ele — arquitetura mais correta pro que o agente realmente faz, documentada aqui pra não parecer desvio não-intencional.

## Backlog — Nível 3: Escudo de Compliance

| # | Tarefa | Critério de aceite | Status |
|---|---|---|---|
| 3.1 | Guardrail de entrada como primeiro nó do grafo | 100% dos ~10 casos de prompt injection identificados no dataset são bloqueados; qualquer caso que passar é documentado e o guardrail ajustado antes do evento | ⚠️ Código pronto. Validado na conta Zup/Vivo: guardrail inicial (só Prompt Attacks) bloqueou 1/10; depois de adicionar Denied Topic específico pra extração de instrução, bloqueou a maioria — **2/10 casos ainda não confirmados bloqueados** (`REC-2026-00413` e mais 1). Aceito como risco conhecido e documentado, não escondido — mitigado pelo fato de os agentes não terem nenhuma capacidade de acessar dado de outro cliente (ver COMPLIANCE.md), então mesmo um miss não vaza dado real. |
| 3.2 | Resposta de bloqueio padrão (fixa, português, sem eco da instrução, sem detalhe interno) | Testada nos mesmos casos de 3.1 | ✅ (testado que nunca vaza termo interno) |
| 3.3 | Guardrail de saída + regex de reforço (CPF, número de conta) | Reclamação sintética de teste com CPF no texto → relatório final não contém o CPF em nenhum campo | ✅ regex sempre ativo; Bedrock Sensitive Information Filters (Mask) configurado no guardrail novo como reforço adicional |
| 3.4 | ADR revisado pós-implementação | ADR bate com o que foi de fato implementado, sem divergência | ✅ ver ADR 0001, seção "Atualização pós-implementação" |
| 3.5 | Bateria de validação com `LLM_PROVIDER=bedrock` na conta do projeto (Vivo/Zup) | Mesmos casos de teste dos níveis 1–3 rodados no Bedrock; divergência de comportamento vs. baseline OpenAI documentada e prompt ajustado se necessário | ✅ rodado. 3 bugs reais achados e corrigidos nessa validação: (1) 1 reclamação com erro derrubava o lote inteiro (sem try/except por item), (2) sem limite de `max_tokens` nos dois LLM clients, (3) `agente_risco` citava seção de produto (3.x) em vez de urgência/canal (2.x/4.x) numa reclamação real. Todos corrigidos e re-testados. |

**Gaps conhecidos, não fechados por falta de tempo (eventos de hoje) — registrar na apresentação se perguntado:**
- Content filters padrão do Bedrock (Hate/Violence/Insults/Sexual/Misconduct) não confirmados habilitados — cobrem "ameaça a pessoas/instituições", hoje sem defesa confirmada além do que o modelo já recusaria por conta própria.
- Nenhum Denied Topic específico pra "conteúdo que não é reclamação válida" (ex: pedido fora de escopo bancário) — não testado.
- Tom profissional/neutro da saída não tem verificação automatizada, só instrução de prompt.

**Sobre a máquina pessoal**: `LLM_PROVIDER=openai` usa `PassthroughGuardrail` (nunca bloqueia, avisa em todo uso) porque não existe guardrail Bedrock equivalente pra testar aqui. Isso deixa rodar o pipeline inteiro localmente pra validar JSON/HTML/logs, mas **não prova que o bloqueio de ataque funciona** — essa prova só vem da tarefa 3.5, na conta Zup/Vivo com Bedrock de verdade.

## Backlog — Pitch e demo

| # | Tarefa | Critério de aceite |
|---|---|---|
| P.1 | Roteiro de pitch (5 min) com 1 caso de injection para rodar ao vivo | Ensaiado, cronometrado, cabe em 5 min |
| P.2 | Resposta pronta para a pergunta obrigatória da banca ("quais ferramentas de IA você usou e como contribuíram") | Resposta escrita cobrindo Bedrock Guardrails, RAG, LangGraph, Nova Micro/DeepSeek V3.2 |
| P.3 | Checklist do dia do evento | Inclui: gerar relatório final antes de desligar, deletar Guardrail/recursos da conta AWS ao término (ver `COMPLIANCE.md` §3) |

## Definition of Done (DoD)

Já definida em [`SPECS.md`](./SPECS.md) §8 — não duplicar aqui, é a referência única.
