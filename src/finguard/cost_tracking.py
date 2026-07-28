import json
import time
from pathlib import Path

# USD por 1 milhão de tokens (input, output). Fonte: pesquisa registrada em
# docs/adr/0001-arquitetura-e-modelos.html §5 e docs/COST_REPORT.md.
# Preço desconhecido nunca é tratado como zero -- ver record_usage().
PRICING_USD_PER_MILLION_TOKENS = {
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),
        "text-embedding-3-small": (0.02, 0.0),
    },
    "bedrock": {
        "amazon.nova-micro-v1:0": (0.035, 0.14),
        "amazon.nova-lite-v1:0": (0.06, 0.24),
        "amazon.nova-pro-v1:0": (0.80, 3.20),
        "anthropic.claude-haiku-4-5": (1.00, 5.00),
        "amazon.titan-embed-text-v2:0": (0.02, 0.0),
    },
}

DEFAULT_LOG_PATH = Path("logs/llm_usage.jsonl")


def calcular_custo_usd(provider: str, model: str, tokens_in: int, tokens_out: int) -> float | None:
    """Retorna None (não zero!) se o modelo não está na tabela -- um custo
    desconhecido nunca deve ser contado como grátis."""
    preco = PRICING_USD_PER_MILLION_TOKENS.get(provider, {}).get(model)
    if preco is None:
        return None
    preco_in, preco_out = preco
    return (tokens_in / 1_000_000) * preco_in + (tokens_out / 1_000_000) * preco_out


def registrar_uso(
    provider: str,
    agent: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    log_path: Path | str = DEFAULT_LOG_PATH,
) -> dict:
    """Registra 1 chamada de LLM em log local (JSONL, append-only). Nunca
    persiste o texto da reclamação -- só metadados de custo (ver
    docs/COMPLIANCE.md sobre não reter dado além do escopo)."""
    custo = calcular_custo_usd(provider, model, tokens_in, tokens_out)
    registro = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": provider,
        "agent": agent,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": custo,
    }

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    return registro
