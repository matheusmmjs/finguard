from typing import Literal, Protocol

AgentName = Literal["triagem", "risco", "relatorio", "rag"]


class LLMClient(Protocol):
    """Interface única — implementações trocáveis por LLM_PROVIDER (SPECS.md §2)."""

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 600) -> str: ...
