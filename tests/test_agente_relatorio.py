from finguard.agents.relatorio import gerar
from finguard.schemas import ReclamacaoProcessada, RiscoOutput, TriagemOutput


def _processada(id_, categoria, produto, urgencia, nivel_risco, acoes=None):
    return ReclamacaoProcessada(
        id=id_,
        triagem=TriagemOutput(
            categoria=categoria, produto=produto, sentimento="Negativo", urgencia=urgencia, resumo="r"
        ),
        risco=RiscoOutput(
            nivel_risco=nivel_risco, justificativa="j", clausula_referencia="2.4", acoes_recomendadas=acoes or []
        ),
    )


def test_dashboard_soma_por_categoria_produto_urgencia():
    resultados = [
        _processada("R1", "Cobrança Indevida", "Cartão de Crédito", "Alta", "Alto"),
        _processada("R2", "Cobrança Indevida", "Conta Corrente", "Média", "Médio"),
        _processada("R3", "Atendimento", "Cartão de Crédito", "Baixa", "Baixo"),
    ]

    relatorio = gerar(resultados)

    assert relatorio.dashboard.total == 3
    assert relatorio.dashboard.por_categoria == {"Cobrança Indevida": 2, "Atendimento": 1}
    assert relatorio.dashboard.por_produto == {"Cartão de Crédito": 2, "Conta Corrente": 1}
    assert relatorio.dashboard.por_urgencia == {"Alta": 1, "Média": 1, "Baixa": 1}


def test_criticas_inclui_so_nivel_risco_critico():
    resultados = [
        _processada("R1", "Fraude/Segurança", "Cartão de Crédito", "Crítica", "Crítico"),
        _processada("R2", "Cobrança Indevida", "Conta Corrente", "Alta", "Alto"),
    ]

    relatorio = gerar(resultados)

    assert len(relatorio.criticas) == 1
    assert relatorio.criticas[0].id == "R1"


def test_recomendacoes_agrega_e_deduplica_acoes_das_criticas():
    resultados = [
        _processada(
            "R1", "Fraude/Segurança", "Cartão de Crédito", "Crítica", "Crítico",
            acoes=["Bloquear cartão", "Notificar compliance"],
        ),
        _processada(
            "R2", "Fraude/Segurança", "Cartão de Crédito", "Crítica", "Crítico", acoes=["Notificar compliance"]
        ),
        _processada(
            "R3", "Cobrança Indevida", "Conta Corrente", "Baixa", "Baixo",
            acoes=["Ação de caso não-crítico, não deve aparecer"],
        ),
    ]

    relatorio = gerar(resultados)

    assert relatorio.recomendacoes == ["Bloquear cartão", "Notificar compliance"]


def test_lista_vazia_gera_relatorio_vazio_sem_erro():
    relatorio = gerar([])

    assert relatorio.dashboard.total == 0
    assert relatorio.criticas == []
    assert relatorio.recomendacoes == []
