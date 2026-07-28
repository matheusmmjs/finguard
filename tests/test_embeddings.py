import json
from unittest.mock import MagicMock, patch

import pytest

from finguard.rag.embeddings import BedrockEmbeddingClient, OpenAIEmbeddingClient, get_embedding_client


def test_openai_embedding_client_retorna_vetores_e_registra_custo(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    with patch("finguard.rag.embeddings.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        item1, item2 = MagicMock(embedding=[0.1, 0.2]), MagicMock(embedding=[0.3, 0.4])
        response = MagicMock(data=[item1, item2], usage=MagicMock(prompt_tokens=42))
        instance.embeddings.create.return_value = response

        client = OpenAIEmbeddingClient(model="text-embedding-3-small", api_key="test-key", log_path=log_path)
        vetores = client.embed(["texto a", "texto b"])

    assert vetores == [[0.1, 0.2], [0.3, 0.4]]
    registro = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert registro["provider"] == "openai"
    assert registro["agent"] == "rag"
    assert registro["tokens_in"] == 42
    assert registro["tokens_out"] == 0


def test_bedrock_embedding_client_faz_1_chamada_por_texto_e_soma_tokens(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    with patch("finguard.rag.embeddings.boto3") as mock_boto3:
        mock_runtime = mock_boto3.client.return_value

        def _fake_invoke(modelId, body):
            texto = json.loads(body)["inputText"]
            payload = {"embedding": [len(texto) * 1.0], "inputTextTokenCount": len(texto.split())}
            fake_body = MagicMock()
            fake_body.read.return_value = json.dumps(payload).encode("utf-8")
            return {"body": fake_body}

        mock_runtime.invoke_model.side_effect = _fake_invoke

        client = BedrockEmbeddingClient(
            model_id="amazon.titan-embed-text-v2:0", region="us-east-1", log_path=log_path
        )
        vetores = client.embed(["um dois", "um dois tres"])

    assert vetores == [[7.0], [12.0]]
    assert mock_runtime.invoke_model.call_count == 2
    registro = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert registro["tokens_in"] == 2 + 3


def test_get_embedding_client_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    with patch("finguard.rag.embeddings.OpenAI"):
        client = get_embedding_client()

    assert isinstance(client, OpenAIEmbeddingClient)
    assert client.model == "text-embedding-3-small"


def test_get_embedding_client_bedrock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

    with patch("finguard.rag.embeddings.boto3"):
        client = get_embedding_client()

    assert isinstance(client, BedrockEmbeddingClient)
    assert client.model_id == "amazon.titan-embed-text-v2:0"


def test_get_embedding_client_provider_desconhecido(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "watson")
    with pytest.raises(ValueError):
        get_embedding_client()
