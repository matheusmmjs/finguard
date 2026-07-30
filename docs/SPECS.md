# FinGuard — Especificação técnica

Complementa [PRD.md](./PRD.md). Ver diagrama de arquitetura gerado na sessão (grafo: start → guardrail_entrada → [triagem → risco → relatorio → guardrail_saida → end] / [resposta_bloqueio → end]).

## 1. Estrutura de pastas (proposta)

```
finguard/
  docs/                  # PRD, specs, ADR, docs do desafio, dataset
  src/
    finguard/
      llm/
        base.py          # interface LLMClient
        openai_client.py # dev (máquina pessoal)
        bedrock_client.py# prod (máquina Zup)
      guardrails/
        bedrock_guardrail.py
      rag/
        policy_chunks.py # split da política em seções
        retriever.py
      agents/
        triagem.py
        risco.py
        relatorio.py
      graph.py           # definição do LangGraph
      schemas.py          # modelos Pydantic de entrada/saída
      logging_utils.py
    run.py                # CLI de entrada
  tests/
  .env.example
  pyproject.toml         # única fonte de dependências (runtime + [dev] opcional)
  README.md
```

## 2. Client de LLM abstraído

Interface única, implementação trocável por env var `LLM_PROVIDER=openai|bedrock`.

```python
class LLMClient(Protocol):
    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str: ...
```

- `OpenAIClient`: usa chave pessoal (`OPENAI_API_KEY`). **Único provider disponível na máquina pessoal** (sem acesso a Bedrock aqui) — todo agente, em todo teste local, roda em modelo OpenAI, independente de qual modelo Bedrock está mapeado pra ele em produção.
- `BedrockClient`: usa boto3 (`bedrock-runtime`), credenciais da conta AWS do projeto Vivo (cliente Zup do usuário) — acesso já testado e validado, Guardrail ID + version 1 já provisionado. Ver `COMPLIANCE.md` §2 para o registro de risco residual dessa escolha (ambiente corporativo de projeto, não conta pessoal isolada). Único client usado na validação real e na demo final; uso restrito à janela do desafio, sem testes extensivos, para limitar custo.

Cada agente resolve seu próprio modelo por variável de ambiente (ver §7), não é um único `MODEL_ID` global — assim dá pra trocar o modelo de um agente sem mexer nos outros.

**Decisão final: `agente_triagem` e `agente_relatorio` em Nova Micro, `agente_risco` em DeepSeek V3.2** (ver ADR 0001 §5) — DeepSeek entrega raciocínio comparável a Claude Haiku por ~40-63% menos custo, melhor relação custo/capacidade pra essa tarefa.

Mesma assinatura nos dois — resto do código (grafo, agentes, parsing) não muda ao trocar.

## 3. Guardrails (Bedrock)

- Guardrail ID e version já provisionados (fornecidos pelo usuário).
- **Nó de entrada** (`guardrail_entrada`, primeiro nó do grafo): chama `bedrock-runtime.apply_guardrail` sobre o texto bruto da reclamação, antes de qualquer outro processamento.
  - Bloqueia: prompt injection / jailbreak, tentativa de extração de system prompt/config interna, exposição de histórico, exfiltração de dados, conteúdo que não é reclamação válida, ameaças a pessoas/instituições.
  - Se `action == BLOCKED`: vai para `resposta_bloqueio` (mensagem educada, fixa, em português, sem detalhe interno) e termina (`__end__`).
  - Se `action == NONE`: segue para `agente_triagem`.
- **Nó de saída** (`guardrail_saida`, antes do `__end__` principal): valida a saída do `agente_relatorio` — nenhum CPF, número de conta ou dado sensível; tom profissional e neutro. Combinar guardrail de saída com regex de reforço (CPF `\d{3}\.?\d{3}\.?\d{3}-?\d{2}`, número de conta) como camada extra determinística, já que o dataset é fictício mas o teste deve ser robusto.

## 4. RAG da política interna

Decisão completa e alternativas descartadas em [ADR 0002](./adr/0002-rag-faiss-embeddings.html).

- Fonte: `docs/KS_POLITICA_INTERNA (2).pdf` (POL-SAC-001).
- Chunking: 1 chunk por seção numerada (2.1 a 2.4 urgência, 3.1 a 3.5 por produto, 4.1 a 4.4 por canal, 5 proteção de dados, 6 indicadores) — ~15 chunks.
- Embeddings: `text-embedding-3-small` (OpenAI, dev) / `amazon.titan-embed-text-v2:0` (Bedrock, prod) — mesmo preço, mesma abstração de client já usada pros agentes.
- Índice: FAISS `IndexFlatIP` (busca exata, vetores normalizados) — não HNSW/IVF, que são pra escala de milhares/milhões de vetores e não fazem sentido pra ~15 chunks (ADR 0002 §2). Índice reconstruído em memória a cada execução, nunca persistido em disco/S3.
- Retrieval: top-3 chunks mais relevantes por reclamação, injetados no prompt do `agente_risco`.
- Saída do `agente_risco` deve incluir campo `clausula_referencia` (ex: `"2.4"`) além do parecer textual.

## 5. Schemas de I/O por agente

### `agente_triagem` (Nível 1)
```json
{
  "categoria": "Cobrança Indevida | Atendimento | Fraude/Segurança | Produto/Serviço | Cancelamento | Outros",
  "produto": "Cartão de Crédito | Conta Corrente | Empréstimo | Investimentos | Seguros | Não Identificado",
  "sentimento": "Positivo | Neutro | Negativo | Crítico",
  "urgencia": "Baixa | Média | Alta | Crítica",
  "resumo": "2-3 linhas, palavras impróprias ofuscadas"
}
```
Regra dura (não depende só do modelo decidir bem): se o texto contiver menção a Banco Central/Procon/Justiça, indício de fraude, ou vulnerabilidade extrema → forçar `urgencia = "Crítica"` por código, independentemente da saída do modelo.

### `agente_risco` (Nível 2/3)
```json
{
  "nivel_risco": "Baixo | Médio | Alto | Crítico",
  "justificativa": "texto",
  "clausula_referencia": "ex: 2.4",
  "acoes_recomendadas": ["ex: notificar compliance em até 2h"]
}
```

### `agente_relatorio` (Nível 2/3)
```json
{
  "dashboard": {"total": 0, "por_categoria": {}, "por_produto": {}, "por_urgencia": {}},
  "criticas": [{"id": "...", "nivel_risco": "...", "justificativa": "...", "clausula_referencia": "..."}],
  "recomendacoes": ["..."]
}
```
Saída final: JSON + HTML navegável com gráfico (ex: Chart.js local ou SVG estático), gerado no diretório de execução (sem S3).

## 6. Grafo (LangGraph)

Grafo processa **1 reclamação por vez**:

```
_start_ → guardrail_entrada
guardrail_entrada --[PASS]--> agente_triagem
guardrail_entrada --[BLOCK]--> resposta_bloqueio --> __end__
agente_triagem --> agente_risco
agente_risco --> guardrail_saida
guardrail_saida --> __end__
```

`agente_relatorio` roda **1 vez, fora do grafo**, depois que todas as reclamações do lote passaram por ele — ele agrega estatísticas do lote inteiro (dashboard, distribuição por categoria/produto/urgência), não faz sentido como nó por-reclamação. Desvio deliberado do diagrama de exemplo do desafio, justificado em `docs/TASKS.md` (seção Nível 2).

Estado do grafo carrega: `texto_original`, saída de cada agente, logs (`timestamp`, `agente`, `tempo_ms`).

## 7. Variáveis de ambiente (`.env.example`)

```
LLM_PROVIDER=openai        # openai (máquina pessoal) | bedrock (validação/demo)

OPENAI_API_KEY=
OPENAI_MODEL_TRIAGEM=gpt-4o-mini
OPENAI_MODEL_RISCO=gpt-4o-mini
OPENAI_MODEL_RELATORIO=gpt-4o-mini

AWS_REGION=
AWS_PROFILE=
BEDROCK_MODEL_ID_TRIAGEM=amazon.nova-micro-v1:0
BEDROCK_MODEL_ID_RISCO=amazon.nova-micro-v1:0      # trocar para anthropic.claude-haiku-4-5 quando ajustar pontualmente
BEDROCK_MODEL_ID_RELATORIO=amazon.nova-micro-v1:0
BEDROCK_GUARDRAIL_ID=
BEDROCK_GUARDRAIL_VERSION=1
```

## 8. Critério de "pronto" (Definition of Done) — Nível 3

- [ ] Roda ponta a ponta local, sem S3, com `LLM_PROVIDER=bedrock` na conta do projeto Vivo/Zup.
- [ ] Guardrail de entrada bloqueia os casos de prompt injection do dataset (validado nos ~10 casos identificados).
- [ ] Guardrail de saída + regex garantem zero CPF/conta nas saídas (testado com casos que citam dados sensíveis no texto).
- [ ] `agente_risco` cita seção da política em 100% dos casos com urgência Alta/Crítica.
- [ ] Relatório final gerado como `.html` (com gráfico) e `.json`.
- [ ] ADR em HTML navegável, com custo comparado por modelo.
- [ ] Logs de cada agente (entrada, saída, tempo) persistidos em arquivo.
- [ ] Resposta pronta para a pergunta obrigatória da banca (ferramentas usadas + contribuição de cada uma).
- [x] Cobertura de testes unitários ≥ 90% (regra permanente, ver §9).

## 9. Regras de qualidade de código

- **Cobertura de testes ≥ 90%, sempre.** Configurada em `pyproject.toml` (`--cov-fail-under=90`) — rodar `pytest` puro já aplica a regra, não é opcional nem precisa lembrar de passar flag. Cobertura alta não é objetivo em si: cada teste deve provar um comportamento real (regra de negócio, caso de borda, correção de bug), não só "tocar a linha" pra inflar número.
- **CI obrigatório**: `.github/workflows/tests.yml` roda a suíte completa (com o gate de 90%) em todo push/PR pra `main`. Se quiser bloquear merge de fato (não só ver o X vermelho), falta ativar "Require status checks" nas configurações de proteção de branch do GitHub — é um clique manual nas configs do repo, não faço isso automaticamente.
- **Regra dura em código > confiar no julgamento do modelo**, sempre que a política interna definir um critério objetivo e verificável (ex: canal Banco Central/Procon → Crítica). O modelo decide o que é ambíguo; o código decide o que a política já decidiu.
- **Sem gambiarra pra bater requisito**: se um agente ainda não existe (ex: `agente_risco` no Nível 1), o código não finge que existe — levanta `NotImplementedError` ou não é chamado, nunca retorna dado falso pra "passar no teste".
- **Estrutura de pastas fixa** (`SPECS.md` §1) — todo código novo entra no pacote/subpasta certa (`agents/`, `llm/`, `rag/`, `guardrails/`), não em `run.py` ou em um arquivo solto na raiz.

## 10. Rastreamento de custo

Objetivo: nunca perder visibilidade de quanto o FinGuard gasta em chamada de LLM, e saber separar isso do custo de *construir* o FinGuard (Claude Code).

- **Toda chamada de LLM é registrada automaticamente** (`src/finguard/cost_tracking.py`), tanto em `OpenAIClient` quanto em `BedrockClient` — não é um passo manual, acontece dentro do `complete()` de cada client.
- Log local, append-only, em `logs/llm_usage.jsonl`: 1 linha JSON por chamada (`timestamp`, `provider`, `agent`, `model`, `tokens_in`, `tokens_out`, `cost_usd`). Nunca grava o texto da reclamação nem a resposta do modelo — só metadado de custo.
- Preço por modelo mantido à mão em `PRICING_USD_PER_MILLION_TOKENS` (mesmo módulo), com os números já pesquisados no ADR 0001 §5. Considerado (e descartado) usar a lib `litellm` para isso — ela tem uma tabela de preço de 100+ modelos mantida pela comunidade, mas é uma dependência pesada pra um problema que se resolve em ~15 linhas com números que já tínhamos. **Modelo sem preço na tabela nunca é tratado como custo zero** — fica marcado como `cost_usd: null` e aparece destacado no relatório, pra nunca esconder um gasto real por tabela desatualizada.
- **Relatório**: `python -m finguard.cost_report` lê o log inteiro, agrega por provider/agente/modelo, e escreve `docs/COST_REPORT.md` (arquivo gerado, não editar à mão). Rodar de novo a qualquer momento pra atualizar.
- **Custo do Claude Code** (ferramenta de desenvolvimento) é rastreado à parte, via [`ccusage`](https://ccusage.com) (`npx ccusage@latest session --json`), que lê os logs locais do Claude Code — não tem como capturar isso de dentro do pipeline Python, é uma ferramenta externa. Snapshot manual salvo em `logs/claude_code_usage.json` (session id + custo + data de verificação), lido pelo relatório e somado ao total combinado, mas sempre com a categoria separada (custo de execução do produto vs. custo de construir o produto) — nunca soma escondido, sempre com nota explicando a diferença.
- Atualizar `logs/claude_code_usage.json` antes da entrega final, rodando `ccusage` de novo (o número sobe conforme a sessão continua).
