import os
from typing import Literal

import boto3

from finguard.schemas import GuardrailResult

# Mensagem fixa de bloqueio -- nunca ecoa a instrução recebida nem expõe
# detalhe interno do sistema (requisito não funcional do Nível 3).
MENSAGEM_BLOQUEIO = (
    "Não conseguimos processar essa solicitação. Se você tem uma reclamação sobre "
    "um produto ou serviço, reformule descrevendo o problema e teremos prazer em ajudar."
)


class BedrockGuardrail:
    """Guardrail de proteção do FinGuard (Nível 3, obrigatório usar Bedrock
    Guardrails). Não testado nesta máquina -- sem acesso a Bedrock aqui.
    Validar na tarefa 3.5 do backlog, na conta do projeto Vivo/Zup."""

    def __init__(self, guardrail_id: str, guardrail_version: str, region: str | None = None) -> None:
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self._client = boto3.client("bedrock-runtime", region_name=region or os.environ.get("AWS_REGION"))

    def avaliar(self, texto: str, source: Literal["INPUT", "OUTPUT"] = "INPUT") -> GuardrailResult:
        response = self._client.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source=source,
            content=[{"text": {"text": texto}}],
        )
        bloqueado = response.get("action") == "GUARDRAIL_INTERVENED"
        return GuardrailResult(bloqueado=bloqueado, motivo=response.get("actionReason") if bloqueado else None)


def get_guardrail() -> BedrockGuardrail:
    return BedrockGuardrail(
        guardrail_id=os.environ["BEDROCK_GUARDRAIL_ID"],
        guardrail_version=os.environ["BEDROCK_GUARDRAIL_VERSION"],
    )
