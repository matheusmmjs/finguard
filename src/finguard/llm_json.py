import json


def parse_llm_json(raw: str) -> dict:
    """Extrai JSON da resposta de um LLM, tolerando bloco de código markdown
    (```json ... ```) que alguns modelos adicionam mesmo quando instruídos a
    não fazer isso."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
