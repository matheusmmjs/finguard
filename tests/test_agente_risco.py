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


def test_clausula_referencia_sempre_corresponde_ao_nivel_de_risco():
    """Achado real (REC-2026-00146): mesmo com a regra anterior (preferir
    seção de urgência/canal sobre produto quando disponível no retrieval),
    um caso Crítico citou seção 2.3 (Alta) em vez de 2.4 (Crítica) -- porque
    a citação ainda dependia do que o RAG recuperou pro texto daquela
    reclamação específica, não do nivel_risco de fato atribuído. Agora é
    mapeamento direto e fixo, não fica sujeito a isso."""
    casos = [
        ("Baixo", "2.1"),
        ("Médio", "2.2"),
        ("Alto", "2.3"),
        ("Crítico", "2.4"),
    ]
    for nivel_risco_modelo, secao_esperada in casos:
        client = FakeLLMClient(
            {
                "nivel_risco": nivel_risco_modelo,
                "justificativa": "texto",
                "clausula_referencia": "3.3",  # o que o modelo disser aqui é ignorado
                "acoes_recomendadas": [],
            }
        )
        retriever = FakeRetriever([{"secao": "3.3", "titulo": "Empréstimo", "texto": "..."}])

        output = avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

        assert output.clausula_referencia == secao_esperada


def test_urgencia_critica_na_triagem_forca_nivel_risco_e_clausula_2_4():
    client = FakeLLMClient(
        {
            "nivel_risco": "Baixo",  # modelo "errou" -- regra dura deve corrigir os dois campos
            "justificativa": "texto",
            "clausula_referencia": "2.1",
            "acoes_recomendadas": [],
        }
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)
    triagem_critica = _TRIAGEM_PADRAO.model_copy(update={"urgencia": Urgencia.CRITICA})

    output = avaliar(_RECLAMACAO_PADRAO, triagem_critica, client, retriever)

    assert output.nivel_risco == NivelRisco.CRITICO
    assert output.clausula_referencia == "2.4"


def test_prompt_usuario_inclui_texto_da_reclamacao_e_contexto_da_politica():
    client = FakeLLMClient(
        {"nivel_risco": "Baixo", "justificativa": "texto", "clausula_referencia": "2.2", "acoes_recomendadas": []}
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)

    avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

    assert "Cobrança indevida no cartão" in client.ultimo_prompt_usuario
    assert "2.2" in client.ultimo_prompt_usuario
    assert retriever.ultima_busca == _RECLAMACAO_PADRAO.texto_reclamacao


def test_nivel_risco_nao_forcado_quando_triagem_nao_e_critica():
    """Regra dura só força Crítico quando triagem.urgencia é Crítica -- fora
    isso, o julgamento do modelo pro nivel_risco é respeitado (só a cláusula
    é sempre travada pelo mapeamento)."""
    client = FakeLLMClient(
        {"nivel_risco": "Alto", "justificativa": "texto", "clausula_referencia": "2.2", "acoes_recomendadas": []}
    )
    retriever = FakeRetriever(_CONTEXTO_PADRAO)

    output = avaliar(_RECLAMACAO_PADRAO, _TRIAGEM_PADRAO, client, retriever)

    assert output.nivel_risco == NivelRisco.ALTO
    assert output.clausula_referencia == "2.3"
