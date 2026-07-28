import json
import time
from pathlib import Path

from finguard.cost_tracking import DEFAULT_LOG_PATH

CLAUDE_CODE_LOG_PATH = Path("logs/claude_code_usage.json")
REPORT_PATH = Path("docs/COST_REPORT.md")


def carregar_registros(log_path: Path | str = DEFAULT_LOG_PATH) -> list[dict]:
    path = Path(log_path)
    if not path.exists():
        return []
    linhas = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(linha) for linha in linhas if linha]


def agregar_por_provider_agente_modelo(registros: list[dict]) -> list[dict]:
    """Agrupa e soma. Custo desconhecido (cost_usd=None) nunca vira 0 --
    fica contado à parte em 'chamadas_sem_preco'."""
    grupos: dict[tuple[str, str, str], dict] = {}
    for r in registros:
        chave = (r["provider"], r["agent"], r["model"])
        grupo = grupos.setdefault(
            chave,
            {
                "provider": r["provider"],
                "agent": r["agent"],
                "model": r["model"],
                "chamadas": 0,
                "chamadas_sem_preco": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
            },
        )
        grupo["chamadas"] += 1
        grupo["tokens_in"] += r["tokens_in"]
        grupo["tokens_out"] += r["tokens_out"]
        if r["cost_usd"] is None:
            grupo["chamadas_sem_preco"] += 1
        else:
            grupo["cost_usd"] += r["cost_usd"]
    return sorted(grupos.values(), key=lambda g: (g["provider"], g["agent"], g["model"]))


def carregar_custo_claude_code(path: Path | str = CLAUDE_CODE_LOG_PATH) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def gerar_relatorio_markdown(
    grupos: list[dict], claude_code: dict | None, gerado_em: str | None = None
) -> str:
    gerado_em = gerado_em or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    total_llm = sum(g["cost_usd"] for g in grupos)
    total_sem_preco = sum(g["chamadas_sem_preco"] for g in grupos)

    linhas = [
        "# FinGuard — Relatório de custo",
        "",
        f"Gerado automaticamente em {gerado_em} por `python -m finguard.cost_report`. "
        "Não editar à mão — a fonte é `logs/llm_usage.jsonl` (LLM) e "
        "`logs/claude_code_usage.json` (Claude Code, atualizado via `ccusage`).",
        "",
        "## Custo de chamadas de LLM (OpenAI dev + Bedrock prod)",
        "",
    ]

    if not grupos:
        linhas.append("Nenhuma chamada registrada ainda.")
    else:
        linhas.append("| Provider | Agente | Modelo | Chamadas | Tokens in | Tokens out | Custo USD |")
        linhas.append("|---|---|---|---|---|---|---|")
        for g in grupos:
            custo_fmt = f"${g['cost_usd']:.4f}"
            if g["chamadas_sem_preco"]:
                custo_fmt += f" (+{g['chamadas_sem_preco']} sem preço na tabela)"
            linhas.append(
                f"| {g['provider']} | {g['agent']} | {g['model']} | {g['chamadas']} | "
                f"{g['tokens_in']:,} | {g['tokens_out']:,} | {custo_fmt} |"
            )
        linhas.append("")
        linhas.append(f"**Total LLM API: ${total_llm:.4f}**")
        if total_sem_preco:
            linhas.append(
                f"⚠️ {total_sem_preco} chamada(s) com modelo fora da tabela de preços "
                "(`src/finguard/cost_tracking.py`) — custo real é maior que o total acima. "
                "Atualizar a tabela antes de confiar neste número."
            )

    linhas += ["", "## Custo do Claude Code (ferramenta de desenvolvimento, categoria separada)", ""]
    if claude_code is None:
        linhas.append(
            "Nenhum snapshot registrado ainda. Gerar com: "
            "`npx ccusage@latest session --id <SESSION_ID> --json` e salvar o resultado "
            "resumido em `logs/claude_code_usage.json`."
        )
    else:
        linhas.append(f"- Sessão: `{claude_code['session_id']}`")
        linhas.append(f"- Custo: **${claude_code['cost_usd']:.2f}**")
        linhas.append(f"- Verificado em: {claude_code['checked_at']}")
        linhas.append(f"- Nota: {claude_code.get('note', '')}")

    linhas += ["", "## Total combinado", ""]
    if claude_code is not None:
        total_geral = total_llm + claude_code["cost_usd"]
        linhas.append(
            f"LLM API (${total_llm:.4f}) + Claude Code (${claude_code['cost_usd']:.2f}) = "
            f"**${total_geral:.2f}**"
        )
        linhas.append(
            "Categorias diferentes: LLM API é custo de execução do FinGuard (o que o desafio "
            "avalia); Claude Code é custo de desenvolvimento (ferramenta usada pra construir). "
            "Somado aqui só pra ter visão total de investimento, não é custo operacional do produto."
        )
    else:
        linhas.append(f"LLM API: ${total_llm:.4f} (Claude Code ainda não registrado, ver seção acima).")

    return "\n".join(linhas) + "\n"


def main() -> None:
    # Passa os nomes do módulo explicitamente (não usa os defaults dos
    # parâmetros) para que testes consigam trocar os caminhos via monkeypatch.
    registros = carregar_registros(DEFAULT_LOG_PATH)
    grupos = agregar_por_provider_agente_modelo(registros)
    claude_code = carregar_custo_claude_code(CLAUDE_CODE_LOG_PATH)
    relatorio = gerar_relatorio_markdown(grupos, claude_code)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(relatorio, encoding="utf-8")
    print(relatorio)


if __name__ == "__main__":
    main()
