import json

from finguard import pipeline
from finguard.schemas import GuardrailResult


class FakeLLMClient:
    def __init__(self, responses):
        self._responses = iter(responses)

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        return next(self._responses)


class FakeEmbeddingClient:
    def embed(self, textos: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in textos]


class FakeGuardrail:
    def __init__(self, bloqueado: bool = False):
        self.bloqueado = bloqueado

    def avaliar(self, texto: str, source: str = "INPUT") -> GuardrailResult:
        return GuardrailResult(bloqueado=self.bloqueado)


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


_RISCO_JSON = json.dumps(
    {"nivel_risco": "Baixo", "justificativa": "j", "clausula_referencia": "2.1", "acoes_recomendadas": []}
)


def test_processar_completo_gera_relatorio_json_html_logs_e_bloqueadas(tmp_path, monkeypatch):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(_CSV_CONTENT, encoding="utf-8-sig")
    out_dir = tmp_path / "out"

    client_triagem = FakeLLMClient([_VALID_JSON, _VALID_JSON])
    client_risco = FakeLLMClient([_RISCO_JSON, _RISCO_JSON])
    monkeypatch.setattr(
        pipeline, "get_llm_client", lambda agent: client_triagem if agent == "triagem" else client_risco
    )
    monkeypatch.setattr(pipeline, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(pipeline, "get_guardrail", lambda: FakeGuardrail(bloqueado=False))

    resultado_path = pipeline.processar_completo(str(csv_path), str(out_dir))

    assert resultado_path == out_dir / "relatorio.html"
    relatorio = json.loads((out_dir / "relatorio.json").read_text(encoding="utf-8"))
    assert relatorio["dashboard"]["total"] == 2
    assert "<html" in (out_dir / "relatorio.html").read_text(encoding="utf-8")
    logs = json.loads((out_dir / "logs_execucao.json").read_text(encoding="utf-8"))
    assert len(logs) == 2 * 4  # 2 reclamações x 4 nós (entrada, triagem, risco, saída)
    bloqueadas = json.loads((out_dir / "bloqueadas.json").read_text(encoding="utf-8"))
    assert bloqueadas == []


def test_processar_completo_separa_bloqueadas_do_relatorio(tmp_path, monkeypatch):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(_CSV_CONTENT, encoding="utf-8-sig")
    out_dir = tmp_path / "out"

    monkeypatch.setattr(pipeline, "get_llm_client", lambda agent: FakeLLMClient([]))
    monkeypatch.setattr(pipeline, "get_embedding_client", lambda: FakeEmbeddingClient())
    monkeypatch.setattr(pipeline, "get_guardrail", lambda: FakeGuardrail(bloqueado=True))

    pipeline.processar_completo(str(csv_path), str(out_dir))

    relatorio = json.loads((out_dir / "relatorio.json").read_text(encoding="utf-8"))
    assert relatorio["dashboard"]["total"] == 0
    bloqueadas = json.loads((out_dir / "bloqueadas.json").read_text(encoding="utf-8"))
    assert len(bloqueadas) == 2
    assert all(b["resposta"] for b in bloqueadas)
