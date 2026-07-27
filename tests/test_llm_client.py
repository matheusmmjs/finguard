from unittest.mock import MagicMock, patch

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
