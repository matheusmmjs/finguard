import re

# Indício de fraude é Crítica sempre (POL-SAC-001 §2.4), independente de canal.
# Cuidado: NÃO incluir "banco central"/"procon"/"justiça" como palavra-chave de
# texto livre aqui -- o próprio exemplo oficial do desafio menciona "Banco
# Central" como ameaça condicional futura ("vou procurar... se não resolverem")
# e o gabarito espera urgência Alta, não Crítica. Canal já confirmado como
# Banco Central/Procon é sinal estrutural correto (ver CANAIS_URGENCIA_CRITICA
# abaixo), texto livre mencionando o órgão não é.
_FRAUDE_PATTERNS = [
    r"\bfraude\b",
    r"\bn[ãa]o reconhe[çc]o\b",
    r"\bn[ãa]o fiz essa compra\b",
    r"\bn[ãa]o autorizei\b",
]
_FRAUDE_RE = re.compile("|".join(_FRAUDE_PATTERNS), re.IGNORECASE)

# POL-SAC-001 §4.3: reclamação chegando por esses canais é Crítica automática,
# independente do conteúdo do texto.
CANAIS_URGENCIA_CRITICA = {"Banco Central", "Procon"}

# Lista pequena e deliberadamente conservadora — evita falso positivo em
# palavras comuns. Ampliar conforme necessário durante os testes do dataset.
_PALAVROES = [
    "merda",
    "porra",
    "caralho",
    "puta",
    "foda",
    "idiota",
    "imbecil",
]
_PALAVRAO_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in _PALAVROES) + r")\w*\b",
    re.IGNORECASE,
)


def exige_urgencia_critica(texto: str, canal: str | None = None) -> bool:
    """Regra dura, não depende do julgamento do modelo (SPECS.md §5)."""
    if canal in CANAIS_URGENCIA_CRITICA:
        return True
    return bool(_FRAUDE_RE.search(texto))


def ofuscar_palavroes(texto: str) -> str:
    def _mask(match: re.Match[str]) -> str:
        word = match.group(0)
        return word[0] + "*" * (len(word) - 1)

    return _PALAVRAO_RE.sub(_mask, texto)


# Guardrail de saída (Nível 3, SPECS.md §3): camada determinística de reforço
# além do julgamento do modelo -- nunca depende só do LLM não vazar dado.
_CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
# Heurística conservadora pra número de conta bancária (padrão agência/conta-dígito
# comum no Brasil, ex: "12345-6"). Não é infalível -- pode dar falso positivo em
# outro tipo de código numérico; é camada extra, não a única defesa (o guardrail
# de entrada/saída do Bedrock é a defesa principal, isso é reforço determinístico).
_CONTA_RE = re.compile(r"\b\d{4,8}-\d{1}\b")


def redigir_dados_sensiveis(texto: str) -> str:
    texto = _CPF_RE.sub("[CPF removido]", texto)
    texto = _CONTA_RE.sub("[número de conta removido]", texto)
    return texto
