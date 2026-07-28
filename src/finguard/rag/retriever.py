import faiss
import numpy as np

from finguard.rag.embeddings import EmbeddingClient
from finguard.rag.policy_chunks import POLICY_CHUNKS


class PolicyRetriever:
    """RAG sobre a política interna. Índice FAISS `IndexFlatIP` (busca exata,
    não aproximada) sobre vetores normalizados -- decisão justificada em
    ADR 0002: ~15 chunks não justifica HNSW/IVF. Índice em memória, nunca
    persistido em disco/S3."""

    def __init__(self, embedding_client: EmbeddingClient, chunks: list[dict] = POLICY_CHUNKS) -> None:
        self.chunks = chunks
        self._embedding_client = embedding_client

        vetores = np.array(embedding_client.embed([c["texto"] for c in chunks]), dtype="float32")
        faiss.normalize_L2(vetores)
        self.index = faiss.IndexFlatIP(vetores.shape[1])
        self.index.add(vetores)

    def buscar(self, texto_reclamacao: str, top_k: int = 3) -> list[dict]:
        vetor = np.array(self._embedding_client.embed([texto_reclamacao]), dtype="float32")
        faiss.normalize_L2(vetor)
        _, indices = self.index.search(vetor, top_k)
        return [self.chunks[i] for i in indices[0] if i != -1]
