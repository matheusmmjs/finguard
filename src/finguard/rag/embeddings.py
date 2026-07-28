import json
import os
from pathlib import Path
from typing import Protocol

import boto3
from openai import OpenAI

from finguard.cost_tracking import DEFAULT_LOG_PATH, registrar_uso


class EmbeddingClient(Protocol):
    def embed(self, textos: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingClient:
    """Único provider disponível na máquina pessoal (sem acesso a Bedrock aqui)."""

    def __init__(self, model: str, api_key: str | None = None, log_path: Path | str = DEFAULT_LOG_PATH) -> None:
        self.model = model
        self.log_path = log_path
        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    def embed(self, textos: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model, input=textos)

        if response.usage is not None:
            registrar_uso(
                provider="openai",
                agent="rag",
                model=self.model,
                tokens_in=response.usage.prompt_tokens,
                tokens_out=0,
                log_path=self.log_path,
            )

        return [item.embedding for item in response.data]


class BedrockEmbeddingClient:
    """Usado na conta do projeto Vivo/Zup (ver COMPLIANCE.md §2). Não testado na
    máquina pessoal -- validar na tarefa 3.5 do backlog. Titan Embeddings não
    tem API de lote na versão usada aqui -- 1 chamada por texto."""

    def __init__(
        self, model_id: str, region: str | None = None, log_path: Path | str = DEFAULT_LOG_PATH
    ) -> None:
        self.model_id = model_id
        self.log_path = log_path
        self._client = boto3.client("bedrock-runtime", region_name=region or os.environ.get("AWS_REGION"))

    def embed(self, textos: list[str]) -> list[list[float]]:
        vetores = []
        tokens_total = 0
        for texto in textos:
            response = self._client.invoke_model(
                modelId=self.model_id, body=json.dumps({"inputText": texto})
            )
            payload = json.loads(response["body"].read())
            vetores.append(payload["embedding"])
            tokens_total += payload.get("inputTextTokenCount", 0)

        registrar_uso(
            provider="bedrock",
            agent="rag",
            model=self.model_id,
            tokens_in=tokens_total,
            tokens_out=0,
            log_path=self.log_path,
        )
        return vetores


def get_embedding_client() -> EmbeddingClient:
    provider = os.environ.get("LLM_PROVIDER", "openai")

    if provider == "openai":
        return OpenAIEmbeddingClient(model=os.environ["OPENAI_EMBEDDING_MODEL"])

    if provider == "bedrock":
        return BedrockEmbeddingClient(model_id=os.environ["BEDROCK_EMBEDDING_MODEL_ID"])

    raise ValueError(f"LLM_PROVIDER desconhecido: {provider!r} (use 'openai' ou 'bedrock')")
