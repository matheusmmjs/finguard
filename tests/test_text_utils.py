from finguard.text_utils import exige_urgencia_critica, ofuscar_palavroes, redigir_dados_sensiveis


def test_exige_urgencia_critica_por_canal():
    assert exige_urgencia_critica("qualquer texto", canal="Banco Central") is True
    assert exige_urgencia_critica("qualquer texto", canal="Procon") is True
    assert exige_urgencia_critica("qualquer texto", canal="SAC") is False


def test_exige_urgencia_critica_por_fraude_no_texto():
    assert exige_urgencia_critica("não reconheço essa compra", canal="SAC") is True
    assert exige_urgencia_critica("acho que é fraude no meu cartão", canal="SAC") is True
    assert exige_urgencia_critica("estou insatisfeito com a tarifa", canal="SAC") is False


def test_ofuscar_palavroes_mascara_e_preserva_resto_do_texto():
    resultado = ofuscar_palavroes("o atendimento foi uma porcaria e uma merda")
    assert "merda" not in resultado
    assert "atendimento" in resultado


def test_redigir_cpf():
    assert redigir_dados_sensiveis("meu CPF é 123.456.789-01") == "meu CPF é [CPF removido]"
    assert redigir_dados_sensiveis("cpf 12345678901 aqui") == "cpf [CPF removido] aqui"


def test_redigir_numero_de_conta():
    assert redigir_dados_sensiveis("conta 123456-7 encerrada") == "conta [número de conta removido] encerrada"


def test_redigir_nao_mexe_em_texto_sem_dado_sensivel():
    texto = "cliente reclama de cobrança indevida no cartão de crédito"
    assert redigir_dados_sensiveis(texto) == texto
