import os
from pathlib import Path

import boto3

from finguard.cost_tracking import DEFAULT_LOG_PATH, registrar_uso
from finguard.llm.base import AgentName


class BedrockClient:
    """Usado na conta do projeto Vivo/Zup para validação e demo (ver COMPLIANCE.md §2).

    Não testado na máquina pessoal — sem acesso a Bedrock aqui. Validar na
    tarefa 3.5 do backlog (docs/TASKS.md), na máquina/conta com Bedrock.
    """

    def __init__(
        self,
        model_id: str,
        agent: AgentName,
        region: str | None = None,
        log_path: Path | str = DEFAULT_LOG_PATH,
    ) -> None:
        self.model_id = model_id
        self.agent = agent
        self.log_path = log_path
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region or os.environ.get("AWS_REGION"),
        )

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"temperature": temperature},
        )

        usage = response.get("usage")
        if usage is not None:
            registrar_uso(
                provider="bedrock",
                agent=self.agent,
                model=self.model_id,
                tokens_in=usage["inputTokens"],
                tokens_out=usage["outputTokens"],
                log_path=self.log_path,
            )

        return response["output"]["message"]["content"][0]["text"]
