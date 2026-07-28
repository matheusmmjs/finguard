from finguard.rag.policy_chunks import POLICY_CHUNKS


def test_todos_os_chunks_tem_campos_obrigatorios():
    for chunk in POLICY_CHUNKS:
        assert chunk["secao"]
        assert chunk["titulo"]
        assert chunk["texto"]


def test_secoes_sao_unicas():
    secoes = [c["secao"] for c in POLICY_CHUNKS]
    assert len(secoes) == len(set(secoes))


def test_secoes_de_urgencia_presentes():
    secoes = {c["secao"] for c in POLICY_CHUNKS}
    assert {"2.1", "2.2", "2.3", "2.4"} <= secoes


def test_secao_4_3_marca_urgencia_automatica():
    chunk = next(c for c in POLICY_CHUNKS if c["secao"] == "4.3")
    assert "AUTOMATICAMENTE CRÍTICA" in chunk["texto"]
