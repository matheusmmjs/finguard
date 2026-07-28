import json

from finguard.llm_json import parse_llm_json


def test_parse_llm_json_aceita_json_puro():
    payload = {"a": 1, "b": "texto"}
    assert parse_llm_json(json.dumps(payload)) == payload


def test_parse_llm_json_aceita_bloco_markdown_multilinha():
    payload = {"categoria": "Atendimento", "urgencia": "Baixa"}
    raw = "```json\n" + json.dumps(payload) + "\n```"
    assert parse_llm_json(raw) == payload


def test_parse_llm_json_aceita_bloco_markdown_em_uma_linha():
    payload = {"categoria": "Atendimento", "urgencia": "Baixa"}
    raw = "```json" + json.dumps(payload) + "```"
    assert parse_llm_json(raw) == payload
