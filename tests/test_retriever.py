from finguard.rag.retriever import PolicyRetriever

_VOCABULARIO = ["cartão", "banco central", "fraude", "seguro"]

_CHUNKS_TESTE = [
    {"secao": "3.1", "titulo": "Cartão", "texto": "Procedimento sobre cartão de crédito e anuidade."},
    {"secao": "4.3", "titulo": "Banco Central", "texto": "Reclamação via banco central é sempre crítica."},
    {"secao": "3.5", "titulo": "Seguro", "texto": "Procedimento sobre seguro e apólice."},
]


class FakeEmbeddingClient:
    """Bag-of-words determinístico sobre um vocabulário pequeno -- suficiente
    pra provar que o retrieval escolhe o chunk certo, sem chamar API real."""

    def __init__(self, vocabulario: list[str] = _VOCABULARIO):
        self.vocabulario = vocabulario
        self.chamadas = 0

    def embed(self, textos: list[str]) -> list[list[float]]:
        self.chamadas += 1
        return [[1.0 if palavra in texto.lower() else 0.0 for palavra in self.vocabulario] for texto in textos]


def test_retriever_indexa_todos_os_chunks_na_construcao():
    client = FakeEmbeddingClient()
    retriever = PolicyRetriever(client, chunks=_CHUNKS_TESTE)

    assert retriever.index.ntotal == len(_CHUNKS_TESTE)
    assert client.chamadas == 1


def test_buscar_retorna_chunk_mais_relevante_primeiro():
    client = FakeEmbeddingClient()
    retriever = PolicyRetriever(client, chunks=_CHUNKS_TESTE)

    resultados = retriever.buscar("tive um problema com o cartão de crédito", top_k=1)

    assert resultados[0]["secao"] == "3.1"


def test_buscar_reconhece_mencao_a_banco_central():
    client = FakeEmbeddingClient()
    retriever = PolicyRetriever(client, chunks=_CHUNKS_TESTE)

    resultados = retriever.buscar("já registrei no banco central", top_k=1)

    assert resultados[0]["secao"] == "4.3"


def test_buscar_respeita_top_k():
    client = FakeEmbeddingClient()
    retriever = PolicyRetriever(client, chunks=_CHUNKS_TESTE)

    resultados = retriever.buscar("cartão", top_k=2)

    assert len(resultados) == 2
