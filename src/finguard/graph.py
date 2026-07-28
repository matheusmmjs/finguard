import operator
import time
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from finguard.agents.risco import avaliar
from finguard.agents.triagem import classificar
from finguard.guardrails.bedrock_guardrail import MENSAGEM_BLOQUEIO, BedrockGuardrail
from finguard.llm.base import LLMClient
from finguard.rag.retriever import PolicyRetriever
from finguard.schemas import ReclamacaoInput, ReclamacaoProcessada, RiscoOutput, TriagemOutput
from finguard.text_utils import redigir_dados_sensiveis


class GraphState(TypedDict):
    reclamacao: ReclamacaoInput
    triagem: TriagemOutput | None
    risco: RiscoOutput | None
    bloqueado: bool
    resposta_bloqueio: str | None
    logs: Annotated[list[dict], operator.add]


def _log(agente: str, inicio: float) -> dict:
    return {
        "agente": agente,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tempo_ms": int((time.monotonic() - inicio) * 1000),
    }


def build_graph(
    client_triagem: LLMClient,
    client_risco: LLMClient,
    retriever: PolicyRetriever,
    guardrail: BedrockGuardrail,
):
    """Grafo por reclamação (SPECS.md §6):
    start -> guardrail_entrada -> [PASS] agente_triagem -> agente_risco -> guardrail_saida -> end
                                -> [BLOCK] resposta_bloqueio -> end
    """

    def node_guardrail_entrada(state: GraphState) -> dict:
        inicio = time.monotonic()
        resultado = guardrail.avaliar(state["reclamacao"].texto_reclamacao, source="INPUT")
        return {"bloqueado": resultado.bloqueado, "logs": [_log("guardrail_entrada", inicio)]}

    def node_resposta_bloqueio(state: GraphState) -> dict:
        inicio = time.monotonic()
        return {"resposta_bloqueio": MENSAGEM_BLOQUEIO, "logs": [_log("resposta_bloqueio", inicio)]}

    def node_triagem(state: GraphState) -> dict:
        inicio = time.monotonic()
        triagem = classificar(state["reclamacao"], client_triagem)
        return {"triagem": triagem, "logs": [_log("agente_triagem", inicio)]}

    def node_risco(state: GraphState) -> dict:
        inicio = time.monotonic()
        risco = avaliar(state["reclamacao"], state["triagem"], client_risco, retriever)
        return {"risco": risco, "logs": [_log("agente_risco", inicio)]}

    def node_guardrail_saida(state: GraphState) -> dict:
        inicio = time.monotonic()
        triagem = state["triagem"].model_copy(update={"resumo": redigir_dados_sensiveis(state["triagem"].resumo)})
        risco = state["risco"].model_copy(
            update={"justificativa": redigir_dados_sensiveis(state["risco"].justificativa)}
        )
        return {"triagem": triagem, "risco": risco, "logs": [_log("guardrail_saida", inicio)]}

    def _rota_guardrail_entrada(state: GraphState) -> Literal["agente_triagem", "resposta_bloqueio"]:
        return "resposta_bloqueio" if state["bloqueado"] else "agente_triagem"

    grafo = StateGraph(GraphState)
    grafo.add_node("guardrail_entrada", node_guardrail_entrada)
    grafo.add_node("resposta_bloqueio", node_resposta_bloqueio)
    grafo.add_node("agente_triagem", node_triagem)
    grafo.add_node("agente_risco", node_risco)
    grafo.add_node("guardrail_saida", node_guardrail_saida)

    grafo.add_edge(START, "guardrail_entrada")
    grafo.add_conditional_edges(
        "guardrail_entrada",
        _rota_guardrail_entrada,
        {"agente_triagem": "agente_triagem", "resposta_bloqueio": "resposta_bloqueio"},
    )
    grafo.add_edge("resposta_bloqueio", END)
    grafo.add_edge("agente_triagem", "agente_risco")
    grafo.add_edge("agente_risco", "guardrail_saida")
    grafo.add_edge("guardrail_saida", END)
    return grafo.compile()


def processar_reclamacao(reclamacao: ReclamacaoInput, grafo) -> GraphState:
    return grafo.invoke(
        {
            "reclamacao": reclamacao,
            "triagem": None,
            "risco": None,
            "bloqueado": False,
            "resposta_bloqueio": None,
            "logs": [],
        }
    )


def processar_lote(
    reclamacoes: list[ReclamacaoInput],
    client_triagem: LLMClient,
    client_risco: LLMClient,
    retriever: PolicyRetriever,
    guardrail: BedrockGuardrail,
) -> tuple[list[ReclamacaoProcessada], list[dict], list[dict]]:
    """Retorna (processadas, bloqueadas, logs). `bloqueadas` guarda o id e a
    resposta educada de toda reclamação que o guardrail de entrada barrou --
    não entra no relatório gerencial, mas não pode desaparecer sem rastro."""
    grafo = build_graph(client_triagem, client_risco, retriever, guardrail)
    processadas = []
    bloqueadas = []
    logs_completos = []

    for reclamacao in reclamacoes:
        estado_final = processar_reclamacao(reclamacao, grafo)
        for entrada_log in estado_final["logs"]:
            logs_completos.append({"reclamacao_id": reclamacao.id, **entrada_log})

        if estado_final["bloqueado"]:
            bloqueadas.append({"id": reclamacao.id, "resposta": estado_final["resposta_bloqueio"]})
        else:
            processadas.append(
                ReclamacaoProcessada(id=reclamacao.id, triagem=estado_final["triagem"], risco=estado_final["risco"])
            )

    return processadas, bloqueadas, logs_completos
