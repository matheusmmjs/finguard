import json

from finguard import cost_report
from finguard.cost_report import (
    agregar_por_provider_agente_modelo,
    carregar_custo_claude_code,
    carregar_registros,
    gerar_relatorio_markdown,
)


def test_carregar_registros_arquivo_inexistente_retorna_lista_vazia(tmp_path):
    assert carregar_registros(tmp_path / "nao-existe.jsonl") == []


def test_carregar_registros_le_jsonl(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    log_path.write_text(
        json.dumps({"provider": "openai", "agent": "triagem", "model": "gpt-4o-mini", "tokens_in": 1, "tokens_out": 1, "cost_usd": 0.001})
        + "\n",
        encoding="utf-8",
    )
    registros = carregar_registros(log_path)
    assert len(registros) == 1
    assert registros[0]["provider"] == "openai"


def test_agregar_soma_por_grupo_e_marca_sem_preco():
    registros = [
        {"provider": "openai", "agent": "triagem", "model": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50, "cost_usd": 0.01},
        {"provider": "openai", "agent": "triagem", "model": "gpt-4o-mini", "tokens_in": 200, "tokens_out": 60, "cost_usd": 0.02},
        {"provider": "bedrock", "agent": "risco", "model": "modelo-fantasma", "tokens_in": 10, "tokens_out": 5, "cost_usd": None},
    ]

    grupos = agregar_por_provider_agente_modelo(registros)

    assert len(grupos) == 2
    triagem = next(g for g in grupos if g["agent"] == "triagem")
    assert triagem["chamadas"] == 2
    assert triagem["tokens_in"] == 300
    assert triagem["cost_usd"] == 0.03
    assert triagem["chamadas_sem_preco"] == 0

    risco = next(g for g in grupos if g["agent"] == "risco")
    assert risco["chamadas_sem_preco"] == 1
    assert risco["cost_usd"] == 0.0


def test_carregar_custo_claude_code_arquivo_inexistente(tmp_path):
    assert carregar_custo_claude_code(tmp_path / "nao-existe.json") is None


def test_carregar_custo_claude_code_le_arquivo(tmp_path):
    path = tmp_path / "cc.json"
    path.write_text(json.dumps({"session_id": "abc", "cost_usd": 1.23, "checked_at": "hoje"}), encoding="utf-8")

    dados = carregar_custo_claude_code(path)

    assert dados["cost_usd"] == 1.23


def test_relatorio_sem_registros_nem_claude_code():
    texto = gerar_relatorio_markdown([], None, gerado_em="2026-07-28T00:00:00Z")
    assert "Nenhuma chamada registrada ainda" in texto
    assert "Nenhum snapshot registrado ainda" in texto


def test_relatorio_com_registros_e_claude_code_soma_total():
    grupos = [
        {
            "provider": "openai",
            "agent": "triagem",
            "model": "gpt-4o-mini",
            "chamadas": 5,
            "chamadas_sem_preco": 0,
            "tokens_in": 1000,
            "tokens_out": 500,
            "cost_usd": 0.045,
        }
    ]
    claude_code = {"session_id": "c06d317f-47d2-4d22-882e-ef35d2ebd381", "cost_usd": 8.30, "checked_at": "2026-07-28"}

    texto = gerar_relatorio_markdown(grupos, claude_code, gerado_em="2026-07-28T00:00:00Z")

    assert "gpt-4o-mini" in texto
    assert "$8.30" in texto
    assert "Total combinado" in texto


def test_relatorio_flagra_chamadas_sem_preco():
    grupos = [
        {
            "provider": "bedrock",
            "agent": "risco",
            "model": "modelo-fantasma",
            "chamadas": 1,
            "chamadas_sem_preco": 1,
            "tokens_in": 10,
            "tokens_out": 5,
            "cost_usd": 0.0,
        }
    ]
    texto = gerar_relatorio_markdown(grupos, None, gerado_em="2026-07-28T00:00:00Z")
    assert "fora da tabela de preços" in texto


def test_main_le_logs_e_escreve_relatorio(tmp_path, monkeypatch, capsys):
    usage_log = tmp_path / "usage.jsonl"
    usage_log.write_text(
        json.dumps({"provider": "openai", "agent": "triagem", "model": "gpt-4o-mini", "tokens_in": 10, "tokens_out": 5, "cost_usd": 0.001})
        + "\n",
        encoding="utf-8",
    )
    claude_code_log = tmp_path / "cc.json"
    claude_code_log.write_text(json.dumps({"session_id": "abc", "cost_usd": 1.0, "checked_at": "hoje"}), encoding="utf-8")
    report_path = tmp_path / "COST_REPORT.md"

    monkeypatch.setattr(cost_report, "DEFAULT_LOG_PATH", usage_log)
    monkeypatch.setattr(cost_report, "CLAUDE_CODE_LOG_PATH", claude_code_log)
    monkeypatch.setattr(cost_report, "REPORT_PATH", report_path)

    cost_report.main()

    assert report_path.exists()
    assert "gpt-4o-mini" in report_path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" in capsys.readouterr().out
