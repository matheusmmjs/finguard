import os
from pathlib import Path

from openai import OpenAI

from finguard.cost_tracking import DEFAULT_LOG_PATH, registrar_uso
from finguard.llm.base import AgentName


class OpenAIClient:
    """Único provider disponível na máquina pessoal (sem acesso a Bedrock aqui)."""

    def __init__(
        self,
        model: str,
        agent: AgentName,
        api_key: str | None = None,
        log_path: Path | str = DEFAULT_LOG_PATH,
    ) -> None:
        self.model = model
        self.agent = agent
        self.log_path = log_path
        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        if response.usage is not None:
            registrar_uso(
                provider="openai",
                agent=self.agent,
                model=self.model,
                tokens_in=response.usage.prompt_tokens,
                tokens_out=response.usage.completion_tokens,
                log_path=self.log_path,
            )

        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("OpenAI retornou resposta vazia")
        return content
