import json

import pytest

from finguard.cost_tracking import calcular_custo_usd, registrar_uso


def test_calcular_custo_usd_modelo_conhecido():
    custo = calcular_custo_usd("openai", "gpt-4o-mini", tokens_in=1_000_000, tokens_out=1_000_000)
    assert custo == pytest.approx(0.15 + 0.60)


def test_calcular_custo_usd_deepseek_v3_2():
    custo = calcular_custo_usd("bedrock", "deepseek.v3-2", tokens_in=1_000_000, tokens_out=1_000_000)
    assert custo == pytest.approx(0.62 + 1.85)


def test_calcular_custo_usd_modelo_desconhecido_retorna_none_nao_zero():
    """Custo desconhecido nunca pode ser contado como grátis -- ver docstring
    de calcular_custo_usd."""
    custo = calcular_custo_usd("openai", "modelo-que-nao-existe", tokens_in=1000, tokens_out=1000)
    assert custo is None


def test_registrar_uso_grava_linha_jsonl(tmp_path):
    log_path = tmp_path / "usage.jsonl"

    registro = registrar_uso(
        provider="bedrock",
        agent="risco",
        model="amazon.nova-micro-v1:0",
        tokens_in=500,
        tokens_out=200,
        log_path=log_path,
    )

    linhas = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 1
    salvo = json.loads(linhas[0])
    assert salvo == registro
    assert salvo["cost_usd"] is not None


def test_registrar_uso_faz_append_sem_sobrescrever(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    registrar_uso(provider="openai", agent="triagem", model="gpt-4o-mini", tokens_in=1, tokens_out=1, log_path=log_path)
    registrar_uso(provider="openai", agent="triagem", model="gpt-4o-mini", tokens_in=2, tokens_out=2, log_path=log_path)

    linhas = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 2


def test_registrar_uso_com_modelo_desconhecido_nao_derruba_e_marca_none(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    registro = registrar_uso(
        provider="openai", agent="triagem", model="modelo-fantasma", tokens_in=10, tokens_out=10, log_path=log_path
    )
    assert registro["cost_usd"] is None
