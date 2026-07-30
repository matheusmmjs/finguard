import csv
import json
import sys
from pathlib import Path

from finguard.agents.relatorio import gerar
from finguard.agents.triagem import classificar
from finguard.graph import processar_lote
from finguard.guardrails.bedrock_guardrail import get_guardrail
from finguard.llm.factory import get_llm_client
from finguard.rag.embeddings import get_embedding_client
from finguard.rag.retriever import PolicyRetriever
from finguard.report_html import renderizar
from finguard.schemas import ReclamacaoInput


def carregar_reclamacoes(csv_path: str) -> list[ReclamacaoInput]:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return [ReclamacaoInput(**row) for row in csv.DictReader(f)]


def processar_triagem(csv_path: str, output_dir: str, limit: int | None = None) -> Path:
    """Tarefa 1.5 do backlog (Nível 1, só classificação). Superada pelo fluxo
    completo em `processar_completo` -- mantida porque ainda é útil pra
    depurar o agente_triagem isoladamente, sem RAG/risco/guardrail no meio."""
    reclamacoes = carregar_reclamacoes(csv_path)
    if limit is not None:
        reclamacoes = reclamacoes[:limit]

    client = get_llm_client("triagem")
    resultados = []
    for i, reclamacao in enumerate(reclamacoes, start=1):
        try:
            saida = classificar(reclamacao, client)
            resultados.append({"id": reclamacao.id, **saida.model_dump()})
        except Exception as exc:  # nosec - erro de 1 linha não pode derrubar o lote
            resultados.append({"id": reclamacao.id, "erro": str(exc)})
        print(f"[{i}/{len(reclamacoes)}] {reclamacao.id}", file=sys.stderr)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "triagem_resultados.json"
    out_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    erros = sum(1 for r in resultados if "erro" in r)
    print(f"Concluído: {len(resultados)} processadas, {erros} com erro. Saída: {out_path}", file=sys.stderr)
    return out_path


def processar_completo(csv_path: str, output_dir: str, limit: int | None = None) -> Path:
    """Fluxo completo (Nível 2 + 3): guardrail de entrada -> triagem -> risco
    -> guardrail de saída, por reclamação, depois agente_relatorio 1x sobre o
    lote inteiro (ver SPECS.md §6 pro porquê do relatório ficar fora do grafo)."""
    reclamacoes = carregar_reclamacoes(csv_path)
    if limit is not None:
        reclamacoes = reclamacoes[:limit]

    client_triagem = get_llm_client("triagem")
    client_risco = get_llm_client("risco")
    retriever = PolicyRetriever(get_embedding_client())
    guardrail = get_guardrail()

    processadas, bloqueadas, erros, logs = processar_lote(
        reclamacoes, client_triagem, client_risco, retriever, guardrail
    )
    relatorio = gerar(processadas)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "relatorio.json").write_text(relatorio.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "relatorio.html").write_text(renderizar(relatorio, bloqueadas), encoding="utf-8")
    (out_dir / "logs_execucao.json").write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "bloqueadas.json").write_text(json.dumps(bloqueadas, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "erros.json").write_text(json.dumps(erros, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Concluído: {len(reclamacoes)} reclamações, {len(processadas)} processadas, "
        f"{len(bloqueadas)} bloqueadas pelo guardrail de entrada, {len(erros)} com erro, "
        f"{len(relatorio.criticas)} críticas. Saída: {out_dir}/",
        file=sys.stderr,
    )
    return out_dir / "relatorio.html"
