import json

from finguard.graph import build_graph, processar_lote, processar_reclamacao
from finguard.schemas import ReclamacaoInput


class FakeLLMClient:
    def __init__(self, payload: dict):
        self._payload = payload

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        return json.dumps(self._payload)


class FakeRetriever:
    def __init__(self, chunks: list[dict]):
        self._chunks = chunks

    def buscar(self, texto: str, top_k: int = 3) -> list[dict]:
        return self._chunks[:top_k]


_TRIAGEM_PAYLOAD = {
    "categoria": "Cobrança Indevida",
    "produto": "Cartão de Crédito",
    "sentimento": "Negativo",
    "urgencia": "Média",
    "resumo": "resumo",
}
_RISCO_PAYLOAD = {
    "nivel_risco": "Médio",
    "justificativa": "j",
    "clausula_referencia": "2.2",
    "acoes_recomendadas": ["Registrar protocolo"],
}
_CHUNKS = [{"secao": "2.2", "titulo": "Urgência Média", "texto": "..."}]


def _reclamacao(id_="REC-TEST-1"):
    return ReclamacaoInput(id=id_, data_reclamacao="2026-01-20", canal="SAC", texto_reclamacao="texto qualquer")


def test_grafo_compila_e_roda_ponta_a_ponta_para_1_reclamacao():
    grafo = build_graph(FakeLLMClient(_TRIAGEM_PAYLOAD), FakeLLMClient(_RISCO_PAYLOAD), FakeRetriever(_CHUNKS))

    estado_final = processar_reclamacao(_reclamacao(), grafo)

    assert estado_final["triagem"].urgencia.value == "Média"
    assert estado_final["risco"].nivel_risco.value == "Médio"


def test_grafo_registra_log_por_agente_com_timestamp_e_duracao():
    grafo = build_graph(FakeLLMClient(_TRIAGEM_PAYLOAD), FakeLLMClient(_RISCO_PAYLOAD), FakeRetriever(_CHUNKS))

    estado_final = processar_reclamacao(_reclamacao(), grafo)

    agentes_logados = [log["agente"] for log in estado_final["logs"]]
    assert agentes_logados == ["agente_triagem", "agente_risco"]
    for log in estado_final["logs"]:
        assert "timestamp" in log
        assert isinstance(log["tempo_ms"], int)


def test_processar_lote_retorna_1_resultado_por_reclamacao_e_logs_com_id():
    reclamacoes = [_reclamacao("REC-1"), _reclamacao("REC-2")]

    processadas, logs = processar_lote(
        reclamacoes,
        FakeLLMClient(_TRIAGEM_PAYLOAD),
        FakeLLMClient(_RISCO_PAYLOAD),
        FakeRetriever(_CHUNKS),
    )

    assert [p.id for p in processadas] == ["REC-1", "REC-2"]
    assert len(logs) == 4  # 2 reclamações x 2 agentes
    assert all("reclamacao_id" in log for log in logs)
    assert {log["reclamacao_id"] for log in logs} == {"REC-1", "REC-2"}
