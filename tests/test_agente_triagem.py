import json
from unittest.mock import MagicMock

from finguard.agents.triagem import classificar
from finguard.schemas import ReclamacaoInput, Urgencia


class FakeLLMClient:
    """Stub de LLMClient — retorna uma resposta JSON fixa, sem chamar API real."""

    def __init__(self, payload: dict):
        self._payload = payload

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        return json.dumps(self._payload)


def test_exemplo_oficial_do_desafio_nao_forca_critica_por_mencao_condicional():
    """Ameaça futura de escalar pro Banco Central (não confirmada, canal != Banco
    Central) é Alta, conforme o gabarito do próprio PDF do desafio -- não deve
    ser forçada para Crítica só por citar o órgão no texto."""
    texto = (
        "Já é a terceira vez que ligo pedindo o estorno de uma cobrança no meu "
        "cartão que eu não fiz. Ninguém resolve nada. Vou procurar o Banco "
        "Central se não resolverem até sexta."
    )
    reclamacao = ReclamacaoInput(
        id="REC-TEST-001", data_reclamacao="2026-01-15", canal="SAC", texto_reclamacao=texto
    )
    client = FakeLLMClient(
        {
            "categoria": "Cobrança Indevida",
            "produto": "Cartão de Crédito",
            "sentimento": "Crítico",
            "urgencia": "Alta",
            "resumo": "Cliente relata cobrança não reconhecida, ameaça escalar para Banco Central.",
        }
    )

    output = classificar(reclamacao, client)

    assert output.urgencia == Urgencia.ALTA


def test_canal_banco_central_forca_urgencia_critica_mesmo_se_modelo_errar():
    """Caso real do dataset (REC-2026-00146): canal já é Banco Central --
    POL-SAC-001 §4.3 exige Crítica automática, mesmo que o modelo erre."""
    texto = (
        "Impressionante como esse banco consegue a proeza de errar o cálculo de "
        "juros de um empréstimo. Já registrei reclamação no Banco Central."
    )
    reclamacao = ReclamacaoInput(
        id="REC-2026-00146",
        data_reclamacao="2025-10-01",
        canal="Banco Central",
        texto_reclamacao=texto,
        produto="Empréstimo",
    )
    client = FakeLLMClient(
        {
            "categoria": "Cobrança Indevida",
            "produto": "Empréstimo",
            "sentimento": "Crítico",
            "urgencia": "Média",  # modelo "errou" de propósito -- regra dura deve corrigir
            "resumo": "Cliente contesta cálculo de juros do empréstimo.",
        }
    )

    output = classificar(reclamacao, client)

    assert output.urgencia == Urgencia.CRITICA


def test_indicio_de_fraude_no_texto_forca_urgencia_critica():
    reclamacao = ReclamacaoInput(
        id="REC-TEST-002",
        data_reclamacao="2026-01-20",
        canal="SAC",
        texto_reclamacao="Não reconheço essa compra no meu cartão, acho que é fraude.",
    )
    client = FakeLLMClient(
        {
            "categoria": "Fraude/Segurança",
            "produto": "Cartão de Crédito",
            "sentimento": "Crítico",
            "urgencia": "Alta",  # modelo "errou" -- deveria ser Crítica
            "resumo": "Cliente relata compra não reconhecida no cartão.",
        }
    )

    output = classificar(reclamacao, client)

    assert output.urgencia == Urgencia.CRITICA


def test_resumo_ofusca_palavrao():
    reclamacao = ReclamacaoInput(
        id="REC-TEST-003", data_reclamacao="2026-01-20", canal="SAC", texto_reclamacao="qualquer coisa"
    )
    client = FakeLLMClient(
        {
            "categoria": "Atendimento",
            "produto": "Não Identificado",
            "sentimento": "Negativo",
            "urgencia": "Baixa",
            "resumo": "Cliente diz que o atendimento é uma merda.",
        }
    )

    output = classificar(reclamacao, client)

    assert "merda" not in output.resumo.lower()
    assert "m****" in output.resumo
