from enum import StrEnum

from pydantic import BaseModel, Field


class Categoria(StrEnum):
    COBRANCA_INDEVIDA = "Cobrança Indevida"
    ATENDIMENTO = "Atendimento"
    FRAUDE_SEGURANCA = "Fraude/Segurança"
    PRODUTO_SERVICO = "Produto/Serviço"
    CANCELAMENTO = "Cancelamento"
    OUTROS = "Outros"


class Produto(StrEnum):
    CARTAO_CREDITO = "Cartão de Crédito"
    CONTA_CORRENTE = "Conta Corrente"
    EMPRESTIMO = "Empréstimo"
    INVESTIMENTOS = "Investimentos"
    SEGUROS = "Seguros"
    NAO_IDENTIFICADO = "Não Identificado"


class Sentimento(StrEnum):
    POSITIVO = "Positivo"
    NEUTRO = "Neutro"
    NEGATIVO = "Negativo"
    CRITICO = "Crítico"


class Urgencia(StrEnum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"


class NivelRisco(StrEnum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"
    CRITICO = "Crítico"


class ReclamacaoInput(BaseModel):
    """Uma linha do dataset fornecido pelo desafio."""

    id: str
    data_reclamacao: str
    canal: str
    texto_reclamacao: str
    produto: str | None = None
    status: str | None = None


class TriagemOutput(BaseModel):
    """Saída do agente_triagem — Nível 1 (SPECS.md §5)."""

    categoria: Categoria
    produto: Produto
    sentimento: Sentimento
    urgencia: Urgencia
    resumo: str = Field(..., description="2-3 linhas, palavras impróprias ofuscadas")


class RiscoOutput(BaseModel):
    """Saída do agente_risco — Nível 2/3 (SPECS.md §5)."""

    nivel_risco: NivelRisco
    justificativa: str
    clausula_referencia: str = Field(..., description='Seção da política interna, ex: "2.4"')
    acoes_recomendadas: list[str] = Field(default_factory=list)


class DashboardResumo(BaseModel):
    total: int = 0
    por_categoria: dict[str, int] = Field(default_factory=dict)
    por_produto: dict[str, int] = Field(default_factory=dict)
    por_urgencia: dict[str, int] = Field(default_factory=dict)


class ReclamacaoCritica(BaseModel):
    id: str
    nivel_risco: NivelRisco
    justificativa: str
    clausula_referencia: str


class RelatorioOutput(BaseModel):
    """Saída do agente_relatorio — Nível 2/3 (SPECS.md §5)."""

    dashboard: DashboardResumo
    criticas: list[ReclamacaoCritica] = Field(default_factory=list)
    recomendacoes: list[str] = Field(default_factory=list)
