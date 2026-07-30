from finguard.llm.base import LLMClient
from finguard.llm_json import parse_llm_json
from finguard.rag.retriever import PolicyRetriever
from finguard.schemas import NivelRisco, ReclamacaoInput, RiscoOutput, TriagemOutput, Urgencia

# A seção de urgência (2.1-2.4) DEFINE cada nível de risco -- não é uma escolha
# entre "seções relevantes", é uma correspondência exata e fixa da política.
# Determinístico, não fica sujeito ao que o RAG recuperou pra essa reclamação
# específica (SPECS.md §5: regra dura > julgamento do modelo/retrieval).
_NIVEL_RISCO_PARA_CLAUSULA = {
    NivelRisco.BAIXO: "2.1",
    NivelRisco.MEDIO: "2.2",
    NivelRisco.ALTO: "2.3",
    NivelRisco.CRITICO: "2.4",
}

_SYSTEM_PROMPT = f"""\
Você é o agente de risco e conformidade do FinGuard. Recebe uma reclamação já \
classificada e trechos relevantes da política interna (POL-SAC-001), e decide o \
nível de risco regulatório/reputacional, sempre fundamentando na política fornecida.

Responda SOMENTE com um objeto JSON, sem texto antes ou depois:

{{
  "nivel_risco": "<um de: {', '.join(n.value for n in NivelRisco)}>",
  "justificativa": "<2-3 linhas explicando o porquê, citando o conteúdo da política>",
  "clausula_referencia": "<número da seção da política mais relevante, ex: '2.4'>",
  "acoes_recomendadas": ["<ação concreta 1>", "<ação concreta 2, se aplicável>"]
}}

Use exclusivamente as seções da política fornecidas no contexto -- não invente \
número de seção que não esteja lá. Se houver uma seção de PRODUTO (3.1 a 3.5) no \
contexto, use o procedimento dela para compor "acoes_recomendadas" com passos \
concretos (ex: prazo, quem aciona).
"""


def _montar_prompt_usuario(reclamacao: ReclamacaoInput, triagem: TriagemOutput, contexto: list[dict]) -> str:
    secoes = "\n\n".join(f"[{c['secao']}] {c['titulo']}: {c['texto']}" for c in contexto)
    return (
        f"Reclamação (canal: {reclamacao.canal}):\n{reclamacao.texto_reclamacao}\n\n"
        f"Classificação já feita: categoria={triagem.categoria.value}, "
        f"produto={triagem.produto.value}, urgencia={triagem.urgencia.value}\n\n"
        f"Trechos relevantes da política interna:\n{secoes}"
    )


def avaliar(
    reclamacao: ReclamacaoInput,
    triagem: TriagemOutput,
    client: LLMClient,
    retriever: PolicyRetriever,
) -> RiscoOutput:
    contexto = retriever.buscar(reclamacao.texto_reclamacao, top_k=3)
    prompt_usuario = _montar_prompt_usuario(reclamacao, triagem, contexto)

    raw = client.complete(system=_SYSTEM_PROMPT, user=prompt_usuario)
    data = parse_llm_json(raw)
    output = RiscoOutput(**data)

    # Urgência Crítica na triagem sempre implica risco Crítico -- consistência
    # de negócio, não fica a critério do modelo divergir disso.
    if triagem.urgencia == Urgencia.CRITICA:
        output.nivel_risco = NivelRisco.CRITICO

    # clausula_referencia sempre reflete a seção de urgência que DEFINE o
    # nivel_risco final -- nunca fica a critério do RAG/modelo escolher outra
    # seção (produto, canal) pra isso. Justificativa/ações continuam livres
    # pra citar contexto adicional (ex: procedimento de produto), só a
    # cláusula principal é travada.
    output.clausula_referencia = _NIVEL_RISCO_PARA_CLAUSULA[output.nivel_risco]

    return output
