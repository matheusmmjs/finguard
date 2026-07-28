# FinGuard — Relatório de custo

Gerado automaticamente em 2026-07-28T01:28:54Z por `python -m finguard.cost_report`. Não editar à mão — a fonte é `logs/llm_usage.jsonl` (LLM) e `logs/claude_code_usage.json` (Claude Code, atualizado via `ccusage`).

## Custo de chamadas de LLM (OpenAI dev + Bedrock prod)

| Provider | Agente | Modelo | Chamadas | Tokens in | Tokens out | Custo USD |
|---|---|---|---|---|---|---|
| openai | rag | text-embedding-3-small | 24 | 9,731 | 0 | $0.0002 |
| openai | risco | gpt-4o-mini | 15 | 10,490 | 1,907 | $0.0027 |
| openai | triagem | gpt-4o-mini | 16 | 10,121 | 1,443 | $0.0024 |

**Total LLM API: $0.0053**

## Custo do Claude Code (ferramenta de desenvolvimento, categoria separada)

- Sessão: `c06d317f-47d2-4d22-882e-ef35d2ebd381`
- Custo: **$27.84**
- Verificado em: 2026-07-28T01:28:37Z
- Nota: Sessão de desenvolvimento do FinGuard no Claude Code, via `npx ccusage@latest session --json` filtrando pelo period/session id acima. Inclui tokens de cache (leitura/escrita), não só tokens novos. Atualizar rodando o mesmo comando de novo antes da entrega final -- número sobe conforme a sessão continua. Subiu de $8.30 (checkpoint anterior) pra $27.84 depois de construir Nível 2 completo + Nível 3 (guardrails) nesta mesma sessão.

## Total combinado

LLM API ($0.0053) + Claude Code ($27.84) = **$27.85**
Categorias diferentes: LLM API é custo de execução do FinGuard (o que o desafio avalia); Claude Code é custo de desenvolvimento (ferramenta usada pra construir). Somado aqui só pra ter visão total de investimento, não é custo operacional do produto.
