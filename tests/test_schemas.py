import pytest
from pydantic import ValidationError

from finguard.schemas import TriagemOutput


def test_triagem_output_accepts_valid_values():
    out = TriagemOutput(
        categoria="Cobrança Indevida",
        produto="Cartão de Crédito",
        sentimento="Crítico",
        urgencia="Alta",
        resumo="Cliente relata cobrança não reconhecida no cartão de crédito.",
    )
    assert out.urgencia.value == "Alta"


def test_triagem_output_rejects_value_outside_enum():
    with pytest.raises(ValidationError):
        TriagemOutput(
            categoria="Categoria Inventada",
            produto="Cartão de Crédito",
            sentimento="Crítico",
            urgencia="Alta",
            resumo="texto",
        )
