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
  requirements.txt
  README.md
```

## 2. Client de LLM abstraído

Interface única, implementação trocável por env var `LLM_PROVIDER=openai|bedrock`.

```python
class LLMClient(Protocol):
    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str: ...
```

- `OpenAIClient`: usa chave pessoal (`OPENAI_API_KEY`). **Único provider disponível na máquina pessoal** (sem acesso a Bedrock aqui) — todo agente, em todo teste local, roda em modelo OpenAI, independente de qual modelo Bedrock está mapeado pra ele em produção.
- `BedrockClient`: usa boto3 (`bedrock-runtime`), credenciais da conta AWS pessoal usada para os testes (conta própria do usuário, separada da corporativa — ver `COMPLIANCE.md` §2). Único client usado na validação real e na demo final.

Cada agente resolve seu próprio modelo por variável de ambiente (ver §7), não é um único `MODEL_ID` global — assim dá pra trocar o modelo de um agente sem mexer nos outros.

**Fase atual (baseline): todos os agentes em Nova Micro no lado Bedrock.** Ajuste por agente vem depois, pontualmente — o candidato já identificado é subir `agente_risco` para Claude Haiku 4.5 (ver ADR 0001, §5) assim que o baseline em Nova Micro estiver funcionando ponta a ponta.

Mesma assinatura nos dois — resto do código (grafo, agentes, parsing) não muda ao trocar.

## 3. Guardrails (Bedrock)

- Guardrail ID e version já provisionados (fornecidos pelo usuário).
- **Nó de entrada** (`guardrail_entrada`, primeiro nó do grafo): chama `bedrock-runtime.apply_guardrail` sobre o texto bruto da reclamação, antes de qualquer outro processamento.
  - Bloqueia: prompt injection / jailbreak, tentativa de extração de system prompt/config interna, exposição de histórico, exfiltração de dados, conteúdo que não é reclamação válida, ameaças a pessoas/instituições.
  - Se `action == BLOCKED`: vai para `resposta_bloqueio` (mensagem educada, fixa, em português, sem detalhe interno) e termina (`__end__`).
  - Se `action == NONE`: segue para `agente_triagem`.
- **Nó de saída** (`guardrail_saida`, antes do `__end__` principal): valida a saída do `agente_relatorio` — nenhum CPF, número de conta ou dado sensível; tom profissional e neutro. Combinar guardrail de saída com regex de reforço (CPF `\d{3}\.?\d{3}\.?\d{3}-?\d{2}`, número de conta) como camada extra determinística, já que o dataset é fictício mas o teste deve ser robusto.

## 4. RAG da política interna

- Fonte: `docs/KS_POLITICA_INTERNA (2).pdf` (POL-SAC-001).
- Chunking: 1 chunk por seção numerada (2.1 a 2.4 urgência, 3.1 a 3.5 por produto, 4.1 a 4.4 por canal, 5 proteção de dados, 6 indicadores) — ~15 chunks.
- Embeddings: Bedrock Embeddings (prod) / embedding equivalente do provedor de dev.
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

```
_start_ → guardrail_entrada
guardrail_entrada --[PASS]--> agente_triagem
guardrail_entrada --[BLOCK]--> resposta_bloqueio --> __end__
agente_triagem --> agente_risco
agente_risco --> agente_relatorio
agente_relatorio --> guardrail_saida
guardrail_saida --> __end__
```

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

- [ ] Roda ponta a ponta local, sem S3, com `LLM_PROVIDER=bedrock` na máquina Zup.
- [ ] Guardrail de entrada bloqueia os casos de prompt injection do dataset (validado nos ~10 casos identificados).
- [ ] Guardrail de saída + regex garantem zero CPF/conta nas saídas (testado com casos que citam dados sensíveis no texto).
- [ ] `agente_risco` cita seção da política em 100% dos casos com urgência Alta/Crítica.
- [ ] Relatório final gerado como `.html` (com gráfico) e `.json`.
- [ ] ADR em HTML navegável, com custo comparado por modelo.
- [ ] Logs de cada agente (entrada, saída, tempo) persistidos em arquivo.
- [ ] Resposta pronta para a pergunta obrigatória da banca (ferramentas usadas + contribuição de cada uma).
