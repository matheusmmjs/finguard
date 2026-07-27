import pytest
from unittest.mock import MagicMock, patch

from finguard.llm.bedrock_client import BedrockClient
from finguard.llm.factory import get_llm_client
from finguard.llm.openai_client import OpenAIClient


def _fake_openai_response(text: str):
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def test_openai_client_complete_returns_model_text():
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response("oi, tudo bem?")

        client = OpenAIClient(model="gpt-4o-mini", api_key="test-key")
        result = client.complete(system="responda em português", user="diga oi")

        assert result == "oi, tudo bem?"
        _, kwargs = instance.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o-mini"


def test_factory_resolves_openai_client_with_agent_specific_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL_TRIAGEM", "gpt-4o-mini")

    with patch("finguard.llm.openai_client.OpenAI"):
        client = get_llm_client("triagem")

    assert isinstance(client, OpenAIClient)
    assert client.model == "gpt-4o-mini"


def test_openai_client_raises_on_empty_response():
    with patch("finguard.llm.openai_client.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _fake_openai_response(None)

        client = OpenAIClient(model="gpt-4o-mini", api_key="test-key")
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


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "watson")

    with pytest.raises(ValueError):
        get_llm_client("triagem")


def test_bedrock_client_complete_returns_model_text():
    with patch("finguard.llm.bedrock_client.boto3") as mock_boto3:
        mock_runtime = mock_boto3.client.return_value
        mock_runtime.converse.return_value = {
            "output": {"message": {"content": [{"text": "resposta do bedrock"}]}}
        }

        client = BedrockClient(model_id="amazon.nova-micro-v1:0", region="us-east-1")
        result = client.complete(system="sys", user="user", temperature=0.2)

        assert result == "resposta do bedrock"
        _, kwargs = mock_runtime.converse.call_args
        assert kwargs["modelId"] == "amazon.nova-micro-v1:0"
        assert kwargs["inferenceConfig"] == {"temperature": 0.2}
