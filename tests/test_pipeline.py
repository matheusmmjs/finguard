import json

from finguard import pipeline


class FakeLLMClient:
    def __init__(self, responses):
        self._responses = iter(responses)

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        return next(self._responses)


_VALID_JSON = json.dumps(
    {
        "categoria": "Atendimento",
        "produto": "Conta Corrente",
        "sentimento": "Negativo",
        "urgencia": "Baixa",
        "resumo": "Cliente reclama de atendimento demorado.",
    }
)

_CSV_CONTENT = (
    "id,data_reclamacao,canal,texto_reclamacao,produto,status\n"
    'REC-1,2026-01-01,SAC,"Demorou muito pra me atender.",Conta Corrente,Aberta\n'
    'REC-2,2026-01-02,SAC,"Fui mal atendido de novo.",Conta Corrente,Aberta\n'
)


def test_processar_triagem_gera_json_para_cada_linha(tmp_path, monkeypatch):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(_CSV_CONTENT, encoding="utf-8-sig")

    fake_client = FakeLLMClient([_VALID_JSON, _VALID_JSON])
    monkeypatch.setattr(pipeline, "get_llm_client", lambda agent: fake_client)

    out_path = pipeline.processar_triagem(str(csv_path), str(tmp_path / "out"))

    resultados = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(resultados) == 2
    assert {r["id"] for r in resultados} == {"REC-1", "REC-2"}
    assert all("erro" not in r for r in resultados)


def test_processar_triagem_nao_derruba_lote_com_erro_em_1_linha(tmp_path, monkeypatch):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(_CSV_CONTENT, encoding="utf-8-sig")

    fake_client = FakeLLMClient(["isso não é json válido", _VALID_JSON])
    monkeypatch.setattr(pipeline, "get_llm_client", lambda agent: fake_client)

    out_path = pipeline.processar_triagem(str(csv_path), str(tmp_path / "out"))

    resultados = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(resultados) == 2
    assert "erro" in resultados[0]
    assert "erro" not in resultados[1]


def test_limit_processa_so_as_n_primeiras_linhas(tmp_path, monkeypatch):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(_CSV_CONTENT, encoding="utf-8-sig")

    fake_client = FakeLLMClient([_VALID_JSON])
    monkeypatch.setattr(pipeline, "get_llm_client", lambda agent: fake_client)

    out_path = pipeline.processar_triagem(str(csv_path), str(tmp_path / "out"), limit=1)

    resultados = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(resultados) == 1
