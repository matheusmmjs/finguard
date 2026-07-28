# FinGuard — Relatório de custo

Gerado automaticamente em 2026-07-28T00:12:45Z por `python -m finguard.cost_report`. Não editar à mão — a fonte é `logs/llm_usage.jsonl` (LLM) e `logs/claude_code_usage.json` (Claude Code, atualizado via `ccusage`).

## Custo de chamadas de LLM (OpenAI dev + Bedrock prod)

| Provider | Agente | Modelo | Chamadas | Tokens in | Tokens out | Custo USD |
|---|---|---|---|---|---|---|
| openai | triagem | gpt-4o-mini | 1 | 612 | 93 | $0.0001 |

**Total LLM API: $0.0001**

## Custo do Claude Code (ferramenta de desenvolvimento, categoria separada)

- Sessão: `c06d317f-47d2-4d22-882e-ef35d2ebd381`
- Custo: **$8.30**
- Verificado em: 2026-07-28T00:20:00Z
- Nota: Sessão de desenvolvimento do FinGuard no Claude Code, via `npx ccusage@latest session --json` filtrando pelo period/session id acima. Inclui tokens de cache (leitura/escrita), não só tokens novos. Atualizar rodando o mesmo comando de novo antes da entrega final -- número sobe conforme a sessão continua.

## Total combinado

LLM API ($0.0001) + Claude Code ($8.30) = **$8.30**
Categorias diferentes: LLM API é custo de execução do FinGuard (o que o desafio avalia); Claude Code é custo de desenvolvimento (ferramenta usada pra construir). Somado aqui só pra ter visão total de investimento, não é custo operacional do produto.
