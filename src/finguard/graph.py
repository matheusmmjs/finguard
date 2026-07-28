import operator
import time
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from finguard.agents.risco import avaliar
from finguard.agents.triagem import classificar
from finguard.llm.base import LLMClient
from finguard.rag.retriever import PolicyRetriever
from finguard.schemas import ReclamacaoInput, ReclamacaoProcessada, RiscoOutput, TriagemOutput


class GraphState(TypedDict):
    reclamacao: ReclamacaoInput
    triagem: TriagemOutput | None
    risco: RiscoOutput | None
    logs: Annotated[list[dict], operator.add]


def _log(agente: str, inicio: float) -> dict:
    return {
        "agente": agente,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tempo_ms": int((time.monotonic() - inicio) * 1000),
    }


def build_graph(client_triagem: LLMClient, client_risco: LLMClient, retriever: PolicyRetriever):
    """Grafo por reclamação: start -> agente_triagem -> agente_risco -> end.
    Guardrails (Nível 3) e agente_relatorio (roda 1x fora do grafo, ver
    SPECS.md §6) ainda não entram aqui -- backlog tarefa 2.1/8."""

    def node_triagem(state: GraphState) -> dict:
        inicio = time.monotonic()
        triagem = classificar(state["reclamacao"], client_triagem)
        return {"triagem": triagem, "logs": [_log("agente_triagem", inicio)]}

    def node_risco(state: GraphState) -> dict:
        inicio = time.monotonic()
        risco = avaliar(state["reclamacao"], state["triagem"], client_risco, retriever)
        return {"risco": risco, "logs": [_log("agente_risco", inicio)]}

    grafo = StateGraph(GraphState)
    grafo.add_node("agente_triagem", node_triagem)
    grafo.add_node("agente_risco", node_risco)
    grafo.add_edge(START, "agente_triagem")
    grafo.add_edge("agente_triagem", "agente_risco")
    grafo.add_edge("agente_risco", END)
    return grafo.compile()


def processar_reclamacao(reclamacao: ReclamacaoInput, grafo) -> GraphState:
    return grafo.invoke({"reclamacao": reclamacao, "triagem": None, "risco": None, "logs": []})


def processar_lote(
    reclamacoes: list[ReclamacaoInput],
    client_triagem: LLMClient,
    client_risco: LLMClient,
    retriever: PolicyRetriever,
) -> tuple[list[ReclamacaoProcessada], list[dict]]:
    grafo = build_graph(client_triagem, client_risco, retriever)
    processadas = []
    logs_completos = []
    for reclamacao in reclamacoes:
        estado_final = processar_reclamacao(reclamacao, grafo)
        processadas.append(
            ReclamacaoProcessada(id=reclamacao.id, triagem=estado_final["triagem"], risco=estado_final["risco"])
        )
        for entrada_log in estado_final["logs"]:
            logs_completos.append({"reclamacao_id": reclamacao.id, **entrada_log})
    return processadas, logs_completos
