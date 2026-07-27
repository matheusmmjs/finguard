import os

import boto3


class BedrockClient:
    """Usado na conta do projeto Vivo/Zup para validação e demo (ver COMPLIANCE.md §2).

    Não testado na máquina pessoal — sem acesso a Bedrock aqui. Validar na
    tarefa 3.5 do backlog (docs/TASKS.md), na máquina/conta com Bedrock.
    """

    def __init__(self, model_id: str, region: str | None = None) -> None:
        self.model_id = model_id
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
        return response["output"]["message"]["content"][0]["text"]
