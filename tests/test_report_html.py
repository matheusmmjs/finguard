from finguard.report_html import renderizar
from finguard.schemas import DashboardResumo, ReclamacaoCritica, RelatorioOutput


def test_renderiza_totais_e_barras():
    relatorio = RelatorioOutput(
        dashboard=DashboardResumo(total=5, por_categoria={"Atendimento": 3, "Fraude/Segurança": 2}),
    )

    html_out = renderizar(relatorio)

    assert "<html" in html_out
    assert "5" in html_out
    assert "Atendimento" in html_out


def test_renderiza_criticas_e_recomendacoes():
    relatorio = RelatorioOutput(
        dashboard=DashboardResumo(total=1),
        criticas=[
            ReclamacaoCritica(id="REC-1", nivel_risco="Crítico", justificativa="j", clausula_referencia="2.4")
        ],
        recomendacoes=["Notificar compliance"],
    )

    html_out = renderizar(relatorio)

    assert "REC-1" in html_out
    assert "Notificar compliance" in html_out


def test_relatorio_vazio_nao_quebra_e_mostra_mensagens_padrao():
    relatorio = RelatorioOutput(dashboard=DashboardResumo(total=0))

    html_out = renderizar(relatorio)

    assert "Nenhuma reclamação crítica" in html_out
    assert "Nenhuma ação pendente" in html_out
    assert "Sem dados" in html_out


def test_mostra_bloqueadas_pelo_guardrail():
    relatorio = RelatorioOutput(dashboard=DashboardResumo(total=3))
    bloqueadas = [{"id": "REC-ATAQUE-1", "resposta": "..."}, {"id": "REC-ATAQUE-2", "resposta": "..."}]

    html_out = renderizar(relatorio, bloqueadas)

    assert "REC-ATAQUE-1" in html_out
    assert "REC-ATAQUE-2" in html_out
    assert ">2<" in html_out  # stat "Bloqueadas"


def test_sem_bloqueadas_mostra_mensagem_padrao():
    relatorio = RelatorioOutput(dashboard=DashboardResumo(total=1))

    html_out = renderizar(relatorio)

    assert "Nenhuma tentativa de ataque bloqueada" in html_out


def test_escapa_html_na_justificativa_para_evitar_injecao():
    relatorio = RelatorioOutput(
        dashboard=DashboardResumo(total=1),
        criticas=[
            ReclamacaoCritica(
                id="REC-1",
                nivel_risco="Crítico",
                justificativa="<script>alert(1)</script>",
                clausula_referencia="2.4",
            )
        ],
    )

    html_out = renderizar(relatorio)

    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out
