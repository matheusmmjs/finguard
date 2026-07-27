import os

from openai import OpenAI


class OpenAIClient:
    """Único provider disponível na máquina pessoal (sem acesso a Bedrock aqui)."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
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
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("OpenAI retornou resposta vazia")
        return content
