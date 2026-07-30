import json

from finguard.graph import build_graph, processar_lote, processar_reclamacao
from finguard.schemas import GuardrailResult, ReclamacaoInput


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


class FakeGuardrail:
    def __init__(self, bloqueado: bool = False, motivo: str | None = None):
        self.bloqueado = bloqueado
        self.motivo = motivo
        self.chamadas: list[tuple[str, str]] = []

    def avaliar(self, texto: str, source: str = "INPUT") -> GuardrailResult:
        self.chamadas.append((texto, source))
        return GuardrailResult(bloqueado=self.bloqueado, motivo=self.motivo)


_TRIAGEM_PAYLOAD = {
    "categoria": "Cobrança Indevida",
    "produto": "Cartão de Crédito",
    "sentimento": "Negativo",
    "urgencia": "Média",
    "resumo": "Cliente com dúvida sobre conta 123456-7.",
}
_RISCO_PAYLOAD = {
    "nivel_risco": "Médio",
    "justificativa": "CPF 123.456.789-01 mencionado no relato.",
    "clausula_referencia": "2.2",
    "acoes_recomendadas": ["Registrar protocolo"],
}
_CHUNKS = [{"secao": "2.2", "titulo": "Urgência Média", "texto": "..."}]


def _reclamacao(id_="REC-TEST-1"):
    return ReclamacaoInput(id=id_, data_reclamacao="2026-01-20", canal="SAC", texto_reclamacao="texto qualquer")


def _grafo(bloqueado=False):
    return build_graph(
        FakeLLMClient(_TRIAGEM_PAYLOAD),
        FakeLLMClient(_RISCO_PAYLOAD),
        FakeRetriever(_CHUNKS),
        FakeGuardrail(bloqueado=bloqueado),
    )


def test_grafo_compila_e_roda_ponta_a_ponta_quando_aprovado():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=False))

    assert estado_final["bloqueado"] is False
    assert estado_final["triagem"].urgencia.value == "Média"
    assert estado_final["risco"].nivel_risco.value == "Médio"


def test_grafo_desvia_para_resposta_bloqueio_quando_guardrail_bloqueia():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=True))

    assert estado_final["bloqueado"] is True
    assert estado_final["resposta_bloqueio"] is not None
    assert estado_final["triagem"] is None
    assert estado_final["risco"] is None


def test_resposta_bloqueio_nao_expoe_detalhe_interno():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=True))

    resposta = estado_final["resposta_bloqueio"]
    for termo_interno in ["guardrail", "bedrock", "system prompt", "langgraph"]:
        assert termo_interno not in resposta.lower()


def test_guardrail_saida_redige_cpf_e_conta_das_saidas():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=False))

    assert "123.456.789-01" not in estado_final["risco"].justificativa
    assert "[CPF removido]" in estado_final["risco"].justificativa
    assert "123456-7" not in estado_final["triagem"].resumo
    assert "[número de conta removido]" in estado_final["triagem"].resumo


def test_log_registra_todos_os_nos_quando_aprovado():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=False))

    agentes_logados = [log["agente"] for log in estado_final["logs"]]
    assert agentes_logados == ["guardrail_entrada", "agente_triagem", "agente_risco", "guardrail_saida"]


def test_log_registra_apenas_guardrail_e_bloqueio_quando_bloqueado():
    estado_final = processar_reclamacao(_reclamacao(), _grafo(bloqueado=True))

    agentes_logados = [log["agente"] for log in estado_final["logs"]]
    assert agentes_logados == ["guardrail_entrada", "resposta_bloqueio"]


def test_processar_lote_separa_processadas_de_bloqueadas():
    reclamacoes = [_reclamacao("REC-OK"), _reclamacao("REC-BLOQ")]
    guardrail = FakeGuardrail(bloqueado=False)
    # 1a chamada aprova, 2a bloqueia -- simula 1 reclamação normal + 1 ataque no lote.
    resultados_guardrail = iter([False, True])

    def avaliar_alternado(texto, source="INPUT"):
        return GuardrailResult(bloqueado=next(resultados_guardrail))

    guardrail.avaliar = avaliar_alternado

    processadas, bloqueadas, erros, logs = processar_lote(
        reclamacoes, FakeLLMClient(_TRIAGEM_PAYLOAD), FakeLLMClient(_RISCO_PAYLOAD), FakeRetriever(_CHUNKS), guardrail
    )

    assert [p.id for p in processadas] == ["REC-OK"]
    assert [b["id"] for b in bloqueadas] == ["REC-BLOQ"]
    assert bloqueadas[0]["resposta"]
    assert erros == []
    assert len(logs) == 4 + 2  # REC-OK: 4 nós, REC-BLOQ: 2 nós


def test_processar_lote_registra_erro_de_1_reclamacao_sem_derrubar_as_outras():
    """Regressão real: rodando o dataset completo no Bedrock, uma reclamação
    fez o modelo devolver texto que não é JSON válido -- sem try/except por
    item, isso derrubava o lote inteiro (500 reclamações perdidas por causa
    de 1)."""
    respostas = iter(["isso não é JSON válido", json.dumps(_TRIAGEM_PAYLOAD)])

    class ClienteAlternado:
        def complete(self, system, user, *, temperature=0.0):
            return next(respostas)

    processadas, bloqueadas, erros, logs = processar_lote(
        [_reclamacao("REC-ERRO"), _reclamacao("REC-OK")],
        ClienteAlternado(),
        FakeLLMClient(_RISCO_PAYLOAD),
        FakeRetriever(_CHUNKS),
        FakeGuardrail(bloqueado=False),
    )

    assert [p.id for p in processadas] == ["REC-OK"]
    assert [e["id"] for e in erros] == ["REC-ERRO"]
    assert "erro" in erros[0]
