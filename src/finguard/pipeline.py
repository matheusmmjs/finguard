import csv
import json
import sys
from pathlib import Path

from finguard.agents.triagem import classificar
from finguard.llm.factory import get_llm_client
from finguard.schemas import ReclamacaoInput


def carregar_reclamacoes(csv_path: str) -> list[ReclamacaoInput]:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return [ReclamacaoInput(**row) for row in csv.DictReader(f)]


def processar_triagem(csv_path: str, output_dir: str, limit: int | None = None) -> Path:
    """Tarefa 1.5 do backlog. Processa o dataset e salva um JSON com o
    resultado da triagem de cada reclamação. Erro em uma linha não derruba
    o processamento das demais -- fica registrado no próprio resultado."""
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
