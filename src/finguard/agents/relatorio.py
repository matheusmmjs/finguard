from collections import Counter

from finguard.schemas import (
    DashboardResumo,
    NivelRisco,
    ReclamacaoCritica,
    ReclamacaoProcessada,
    RelatorioOutput,
)


def gerar(resultados: list[ReclamacaoProcessada]) -> RelatorioOutput:
    """Consolida triagem + risco de todas as reclamações processadas.

    Deliberadamente sem chamada de LLM -- é agregação de dado que os outros
    agentes já produziram, não julgamento novo. Fazer isso com uma chamada de
    LLM adicionaria custo, latência e risco de alucinação num relatório que
    tem que ser 100% fiel ao que já foi decidido (SPECS.md §5: regra dura
    quando o critério já está definido, não deixa a cargo do modelo)."""
    dashboard = DashboardResumo(
        total=len(resultados),
        por_categoria=dict(Counter(r.triagem.categoria.value for r in resultados)),
        por_produto=dict(Counter(r.triagem.produto.value for r in resultados)),
        por_urgencia=dict(Counter(r.triagem.urgencia.value for r in resultados)),
    )

    criticas = [
        ReclamacaoCritica(
            id=r.id,
            nivel_risco=r.risco.nivel_risco,
            justificativa=r.risco.justificativa,
            clausula_referencia=r.risco.clausula_referencia,
        )
        for r in resultados
        if r.risco.nivel_risco == NivelRisco.CRITICO
    ]

    recomendacoes: list[str] = []
    for r in resultados:
        if r.risco.nivel_risco == NivelRisco.CRITICO:
            for acao in r.risco.acoes_recomendadas:
                if acao not in recomendacoes:
                    recomendacoes.append(acao)

    return RelatorioOutput(dashboard=dashboard, criticas=criticas, recomendacoes=recomendacoes)
