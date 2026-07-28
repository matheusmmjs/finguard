import os

from finguard.llm.base import AgentName, LLMClient

_ENV_KEY_SUFFIX = {"triagem": "TRIAGEM", "risco": "RISCO", "relatorio": "RELATORIO"}


def get_llm_client(agent: AgentName) -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    suffix = _ENV_KEY_SUFFIX[agent]

    if provider == "openai":
        from finguard.llm.openai_client import OpenAIClient

        model = os.environ[f"OPENAI_MODEL_{suffix}"]
        return OpenAIClient(model=model, agent=agent)

    if provider == "bedrock":
        from finguard.llm.bedrock_client import BedrockClient

        model_id = os.environ[f"BEDROCK_MODEL_ID_{suffix}"]
        return BedrockClient(model_id=model_id, agent=agent)

    raise ValueError(f"LLM_PROVIDER desconhecido: {provider!r} (use 'openai' ou 'bedrock')")
