import json

from finguard.llm.base import LLMClient
from finguard.schemas import Categoria, Produto, ReclamacaoInput, Sentimento, TriagemOutput, Urgencia
from finguard.text_utils import exige_urgencia_critica, ofuscar_palavroes

_SYSTEM_PROMPT = f"""\
Você é o agente de triagem do FinGuard, sistema de análise de reclamações de uma \
instituição financeira. Classifique a reclamação do cliente e responda SOMENTE com \
um objeto JSON, sem texto antes ou depois, no formato:

{{
  "categoria": "<uma de: {', '.join(c.value for c in Categoria)}>",
  "produto": "<um de: {', '.join(p.value for p in Produto)}>",
  "sentimento": "<um de: {', '.join(s.value for s in Sentimento)}>",
  "urgencia": "<uma de: {', '.join(u.value for u in Urgencia)}>",
  "resumo": "<2-3 linhas em linguagem padronizada, neutra>"
}}

Regras de urgência (política interna POL-SAC-001):
- Crítica: indício de fraude, menção a Banco Central/Procon/Justiça, vulnerabilidade \
extrema do cliente.
- Alta: valor significativo (acima de R$ 500), múltiplas tentativas sem resolução, \
ameaça de escalar para órgão regulador.
- Média: impacto financeiro moderado, problema recorrente, falha de atendimento.
- Baixa: dúvida operacional, insatisfação leve sem impacto financeiro.
"""


def _parse_llm_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def classificar(reclamacao: ReclamacaoInput, client: LLMClient) -> TriagemOutput:
    raw = client.complete(system=_SYSTEM_PROMPT, user=reclamacao.texto_reclamacao)
    data = _parse_llm_json(raw)
    output = TriagemOutput(**data)

    # Regra dura: nunca depende só do modelo ter decidido bem (SPECS.md §5).
    if exige_urgencia_critica(reclamacao.texto_reclamacao, canal=reclamacao.canal):
        output.urgencia = Urgencia.CRITICA

    output.resumo = ofuscar_palavroes(output.resumo)
    return output
