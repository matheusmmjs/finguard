import json

from finguard.agents.risco import avaliar
from finguard.schemas import NivelRisco, ReclamacaoInput, TriagemOutput, Urgencia


class FakeLLMClient:
    def __init__(self, payload: dict):
        self._payload = payload
        self.ultimo_prompt_usuario = None

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        self.ultimo_prompt_usuario = user
        return json.dumps(self._payload)


class FakeRetriever:
    def __init__(self, chunks: list[dict]):
        self._chunks = chunks
        self.ultima_busca = None

    def buscar(self, texto: str, top_k: int = 3) -> list[dict]:
        self.ultima_busca = texto
        return self._chunks[:top_k]


_CONTEXTO_PADRAO = [
    {"secao": "2.2", "titulo": "Urgência Média", "texto": "..."},
    {"secao": "3.1", "titulo": "Cartão de Crédito", "texto": "..."},
]

_RECLAMACAO_PADRAO = ReclamacaoInput(
    id="REC-TEST-100", data_reclamacao="2026-01-20", canal="SAC", texto_reclamacao="Cobrança indevida no cartão."
)

_TRIAGEM_PADRAO = TriagemOutput(
    categoria="Cobrança Indevida", produto="Cartão de Crédito", sentimento="Negativo", urgencia="Média",
    resumo="resumo",
)


def test_respeita_clausula_quando_esta_no_contexto_recuperado():
    client = FakeLLMClient(
        {
            "nivel_risco": "Médio",
            "justificativa": "Impacto financeiro moderado.",
            "clausula_referencia": "2.2",
            "acoes_recomendadas": ["Registrar protocolo"],
        }
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)

    output = avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

    assert output.clausula_referencia == "2.2"
    assert output.nivel_risco == NivelRisco.MEDIO


def test_corrige_clausula_alucinada_para_o_topo_do_retrieval():
    """Modelo cita uma seção que não veio do RAG -- não pode ser confiado,
    tem que ser substituído pela seção mais relevante de verdade."""
    client = FakeLLMClient(
        {
            "nivel_risco": "Médio",
            "justificativa": "texto",
            "clausula_referencia": "9.9",  # não existe, não veio do retrieval
            "acoes_recomendadas": [],
        }
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)

    output = avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

    assert output.clausula_referencia == "2.2"


def test_urgencia_critica_na_triagem_forca_nivel_risco_critico():
    client = FakeLLMClient(
        {
            "nivel_risco": "Baixo",  # modelo "errou" -- regra dura deve corrigir
            "justificativa": "texto",
            "clausula_referencia": "2.4",
            "acoes_recomendadas": [],
        }
    )
    retriever = FakeRetriever([{"secao": "2.4", "titulo": "Urgência Crítica", "texto": "..."}])
    triagem_critica = _TRIAGEM_PADRAO.model_copy(update={"urgencia": Urgencia.CRITICA})

    output = avaliar(_RECLAMACAO_PADRAO, triagem_critica, client, retriever)

    assert output.nivel_risco == NivelRisco.CRITICO


def test_prompt_usuario_inclui_texto_da_reclamacao_e_contexto_da_politica():
    client = FakeLLMClient(
        {"nivel_risco": "Baixo", "justificativa": "texto", "clausula_referencia": "2.2", "acoes_recomendadas": []}
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)

    avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

    assert "Cobrança indevida no cartão" in client.ultimo_prompt_usuario
    assert "2.2" in client.ultimo_prompt_usuario
    assert retriever.ultima_busca == _RECLAMACAO_PADRAO.texto_reclamacao


def test_cinco_niveis_de_urgencia_retornam_risco_coerente():
    casos = [
        ("Baixa", "Baixo", "2.1"),
        ("Média", "Médio", "2.2"),
        ("Alta", "Alto", "2.3"),
        ("Crítica", "Crítico", "2.4"),
    ]
    for urgencia, nivel_risco_esperado, secao in casos:
        client = FakeLLMClient(
            {
                "nivel_risco": nivel_risco_esperado,
                "justificativa": "texto",
                "clausula_referencia": secao,
                "acoes_recomendadas": [],
            }
        )
        retriever = FakeRetriever([{"secao": secao, "titulo": "t", "texto": "..."}])
        triagem = _TRIAGEM_PADRAO.model_copy(update={"urgencia": Urgencia(urgencia)})

        output = avaliar(_RECLAMACAO_PADRAO, triagem, client, retriever)

        assert output.nivel_risco.value == nivel_risco_esperado
        assert output.clausula_referencia == secao

    # caso ambíguo: triagem não-crítica mas modelo aponta risco Alto -- regra
    # dura não mexe (só força Crítico quando triagem é Crítica), fica o
    # julgamento do modelo.
    client = FakeLLMClient(
        {"nivel_risco": "Alto", "justificativa": "texto", "clausula_referencia": "2.2", "acoes_recomendadas": []}
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)
    output = avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)
    assert output.nivel_risco == NivelRisco.ALTO
