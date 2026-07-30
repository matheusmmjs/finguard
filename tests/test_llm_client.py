import json
from unittest.mock import MagicMock, patch

import pytest

from finguard.llm.bedrock_client import BedrockClient
from finguard.llm.factory import get_llm_client
from finguard.llm.openai_client import OpenAIClient


def _fake_openai_response(text: str | None, tokens_in: int = 10, tokens_out: int = 5):
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.usage = MagicMock(prompt_tokens=tokens_in, completion_tokens=tokens_out)
    return response


def test_openai_client_complete_returns_model_text(tmp_path):
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response("oi, tudo bem?")

        client = OpenAIClient(
            model="gpt-4o-mini", agent="triagem", api_key="test-key", log_path=tmp_path / "usage.jsonl"
        )
        result = client.complete(system="responda em português", user="diga oi")

        assert result == "oi, tudo bem?"
        _, kwargs = instance.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["max_tokens"] == 600


def test_openai_client_max_tokens_customizavel(tmp_path):
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response("ok")

        client = OpenAIClient(
            model="gpt-4o-mini", agent="triagem", api_key="test-key", log_path=tmp_path / "usage.jsonl"
        )
        client.complete(system="sys", user="user", max_tokens=100)

        _, kwargs = instance.chat.completions.create.call_args
        assert kwargs["max_tokens"] == 100


def test_openai_client_registra_custo_no_log(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response(
            "ok", tokens_in=100, tokens_out=50
        )

        client = OpenAIClient(model="gpt-4o-mini", agent="triagem", api_key="test-key", log_path=log_path)
        client.complete(system="sys", user="user")

    linhas = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 1
    registro = json.loads(linhas[0])
    assert registro["provider"] == "openai"
    assert registro["agent"] == "triagem"
    assert registro["tokens_in"] == 100
    assert registro["tokens_out"] == 50
    assert registro["cost_usd"] == pytest.approx(100 / 1_000_000 * 0.15 + 50 / 1_000_000 * 0.60)


def test_factory_resolves_openai_client_with_agent_specific_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL_TRIAGEM", "gpt-4o-mini")

    with patch("finguard.llm.openai_client.OpenAI"):
        client = get_llm_client("triagem")

    assert isinstance(client, OpenAIClient)
    assert client.model == "gpt-4o-mini"
    assert client.agent == "triagem"


def test_openai_client_raises_on_empty_response(tmp_path):
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response(None)

        client = OpenAIClient(
            model="gpt-4o-mini", agent="triagem", api_key="test-key", log_path=tmp_path / "usage.jsonl"
        )
        with pytest.raises(RuntimeError):
            client.complete(system="sys", user="user")


def test_factory_resolves_bedrock_client_with_agent_specific_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID_RISCO", "anthropic.claude-haiku-4-5")

    with patch("finguard.llm.bedrock_client.boto3"):
        client = get_llm_client("risco")

    assert isinstance(client, BedrockClient)
    assert client.model_id == "anthropic.claude-haiku-4-5"
    assert client.agent == "risco"


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "watson")

    with pytest.raises(ValueError):
        get_llm_client("triagem")


def test_bedrock_client_complete_returns_model_text_and_registra_custo(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    with patch("finguard.llm.bedrock_client.boto3") as mock_boto3:
        mock_runtime = mock_boto3.client.return_value
        mock_runtime.converse.return_value = {
            "output": {"message": {"content": [{"text": "resposta do bedrock"}]}},
            "usage": {"inputTokens": 200, "outputTokens": 80},
        }

        client = BedrockClient(
            model_id="amazon.nova-micro-v1:0", agent="triagem", region="us-east-1", log_path=log_path
        )
        result = client.complete(system="sys", user="user", temperature=0.2)

        assert result == "resposta do bedrock"
        _, kwargs = mock_runtime.converse.call_args
        assert kwargs["modelId"] == "amazon.nova-micro-v1:0"
        assert kwargs["inferenceConfig"] == {"temperature": 0.2, "maxTokens": 600}

    registro = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert registro["provider"] == "bedrock"
    assert registro["tokens_in"] == 200
    assert registro["tokens_out"] == 80
