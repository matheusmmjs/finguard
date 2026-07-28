# FinGuard — Escudo de Compliance e Risco Regulatório

[![tests](https://github.com/matheusmmjs/finguard/actions/workflows/tests.yml/badge.svg)](https://github.com/matheusmmjs/finguard/actions/workflows/tests.yml)

Desafio Future Minds 3 (Zup) — assistente inteligente de análise de reclamações de clientes. Diferencial: não é mais um roteador genérico de reclamação — o foco é blindar a instituição contra multa regulatória e vazamento de dado, os riscos financeiros e de imagem mais caros do cenário. Bloqueia ataques de prompt injection ao vivo, aplica a política interna com citação de cláusula, garante conformidade LGPD.

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Problema de negócio, diferencial escolhido, escopo por nível |
| [docs/SPECS.md](docs/SPECS.md) | Arquitetura técnica, schemas, regras de qualidade, rastreamento de custo |
| [docs/adr/0001-arquitetura-e-modelos.html](docs/adr/0001-arquitetura-e-modelos.html) | Decisão de arquitetura + seleção de modelos de LLM + custo |
| [docs/adr/0002-rag-faiss-embeddings.html](docs/adr/0002-rag-faiss-embeddings.html) | Decisão de RAG: FAISS + embeddings |
| [docs/COMPLIANCE.md](docs/COMPLIANCE.md) | Checklist de conformidade com as regras do desafio |
| [docs/TASKS.md](docs/TASKS.md) | Backlog, Definition of Ready, critério de aceite por tarefa |
| [docs/COST_REPORT.md](docs/COST_REPORT.md) | Custo real de LLM + Claude Code (gerado automaticamente) |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # preencher OPENAI_API_KEY (dev) ou credenciais Bedrock (validação/demo)
```

## Rodar

```bash
python -m finguard.run --limit 5   # testa em poucas linhas, sem gastar tokens à toa
python -m finguard.run             # processa o dataset completo
```

## Testar

```bash
pytest                       # roda a suíte com gate de cobertura ≥ 90% (pyproject.toml)
python -m finguard.cost_report   # regenera docs/COST_REPORT.md a partir dos logs
```

## Estado atual

Níveis 1 e 2 completos e validados com chamada real (`python -m finguard.run`). Nível 3 (guardrails): código pronto e testado com mock, mas **validação real do bloqueio de ataque ainda pendente** — guardrail é Bedrock-obrigatório e esta máquina não tem acesso; `LLM_PROVIDER=openai` usa um `PassthroughGuardrail` que nunca bloqueia (só serve pra testar o resto do pipeline localmente). Falta rodar a bateria real na conta Zup/Vivo (`docs/TASKS.md`, tarefa 3.5) antes de considerar o Nível 3 fechado.
