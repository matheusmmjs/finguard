"""Chunks da política interna (POL-SAC-001), 1 por seção numerada.

Transcrito à mão a partir de docs/KS_POLITICA_INTERNA (2).pdf, em vez de
parsing automático do PDF. Decisão deliberada: o documento é fixo (fornecido
uma única vez pelo desafio, não muda durante o evento), e parsing automático
de layout de PDF é frágil (quebra de linha, ordem de coluna) para um ganho
que não existe aqui -- se a política mudasse com frequência, valeria a pena
automatizar. RAG continua sendo RAG (embedding + busca vetorial) independente
de como o texto-fonte entrou em memória (ver ADR 0002).
"""

POLICY_CHUNKS = [
    {
        "secao": "2.1",
        "titulo": "Urgência Baixa",
        "texto": (
            "Urgência Baixa: dúvidas operacionais, solicitações de informação, insatisfações leves "
            "sem impacto financeiro. Prazo de resposta: até 5 dias úteis. Ações: registrar protocolo "
            "e enviar confirmação de recebimento ao cliente em até 24h, encaminhar para a fila padrão "
            "da área responsável pelo produto. Não requer acompanhamento gerencial."
        ),
    },
    {
        "secao": "2.2",
        "titulo": "Urgência Média",
        "texto": (
            "Urgência Média: reclamações com impacto financeiro moderado, problemas recorrentes, "
            "falhas de atendimento. Prazo de resposta: até 3 dias úteis. Ações: registrar protocolo e "
            "enviar confirmação ao cliente em até 12h, analista sênior avalia em até 24h, se envolver "
            "valor financeiro solicitar análise preliminar de estorno à área de Operações, enviar "
            "posicionamento intermediário ao cliente caso o prazo exceda 48h."
        ),
    },
    {
        "secao": "2.3",
        "titulo": "Urgência Alta",
        "texto": (
            "Urgência Alta: reclamações com valores significativos (acima de R$ 500), múltiplas "
            "tentativas sem resolução, ameaça de escalação para órgãos reguladores (o cliente diz que "
            "vai procurar Banco Central/Procon/Justiça, mas ainda não fez isso). Prazo de resposta: até "
            "24 horas. Ações: contato ativo com o cliente em até 4h, designar analista dedicado, "
            "notificar coordenador da área responsável, iniciar processo de estorno ou compensação "
            "temporária se aplicável, registrar no painel de acompanhamento gerencial."
        ),
    },
    {
        "secao": "2.4",
        "titulo": "Urgência Crítica",
        "texto": (
            "Urgência Crítica: indícios de fraude, violação regulatória, reclamação JÁ registrada/"
            "formalizada em Banco Central, Procon ou Justiça (não apenas ameaça de fazer isso), risco à "
            "segurança do cliente, vulnerabilidade emocional ou financeira extrema. Prazo de resposta: "
            "até 4 horas. Ações: contato ativo imediato com o cliente em até 2h, escalar para gerente de "
            "área e equipe de Compliance, se suspeita de fraude acionar Prevenção a Fraudes e bloquear "
            "transações suspeitas, se menção a Banco Central/Procon registrar no sistema de ouvidoria e "
            "notificar jurídico, se vulnerabilidade do cliente acionar protocolo de atendimento sensível "
            "(tom empático, sem cobrança de prazos), relatório de incidente em até 24h."
        ),
    },
    {
        "secao": "3.1",
        "titulo": "Procedimento — Cartão de Crédito",
        "texto": (
            "Cartão de Crédito: cobrança indevida -- contestação de fatura em até 24h, estorno "
            "provisório em até 48h se valor > R$ 200. Fraude -- bloquear cartão imediatamente, emitir "
            "segunda via, investigação em até 12h. Cancelamento -- processar em até 24h, estornar "
            "anuidades proporcionais automaticamente. Responsável: Gerência de Cartões."
        ),
    },
    {
        "secao": "3.2",
        "titulo": "Procedimento — Conta Corrente",
        "texto": (
            "Conta Corrente: tarifas indevidas -- revisar extrato dos últimos 90 dias, estorno "
            "automático se comprovado. Problemas de acesso/app -- encaminhar para TI com prioridade se "
            "afetar transações. Encerramento -- processar em até 5 dias úteis, confirmar saldo zerado. "
            "Responsável: Gerência de Contas."
        ),
    },
    {
        "secao": "3.3",
        "titulo": "Procedimento — Empréstimo",
        "texto": (
            "Empréstimo: divergência de taxas -- recalcular parcelas em até 48h, notificar cliente com "
            "comparativo. Cobranças após quitação -- suspender em até 24h, emitir carta de quitação. "
            "Renegociação -- oferecer ao menos 2 alternativas. Responsável: Gerência de Crédito."
        ),
    },
    {
        "secao": "3.4",
        "titulo": "Procedimento — Investimentos",
        "texto": (
            "Investimentos: taxas não informadas -- revisar contrato e comunicações, estornar se "
            "ausência de informação comprovada. Rentabilidade divergente -- relatório comparativo "
            "detalhado em até 72h. Resgate bloqueado -- desbloquear ou justificar formalmente em até "
            "24h. Responsável: Gerência de Investimentos."
        ),
    },
    {
        "secao": "3.5",
        "titulo": "Procedimento — Seguros",
        "texto": (
            "Seguros: reajuste sem aviso -- verificar cláusula contratual, estornar diferença se aviso "
            "prévio insuficiente. Negativa de sinistro -- reanálise obrigatória por perito diferente do "
            "original em até 5 dias. Cancelamento -- processar em até 48h com devolução proporcional do "
            "prêmio. Responsável: Gerência de Seguros."
        ),
    },
    {
        "secao": "4.1",
        "titulo": "Canal — SAC",
        "texto": (
            "SAC (Serviço de Atendimento ao Consumidor): canal de primeira instância. Prazo legal: 5 "
            "dias úteis. Registro obrigatório com protocolo numérico fornecido ao cliente."
        ),
    },
    {
        "secao": "4.2",
        "titulo": "Canal — Ouvidoria",
        "texto": (
            "Ouvidoria: canal de segunda instância (cliente já tentou SAC). Tratamento diferenciado: "
            "analista sênior dedicado. Prazo legal: 10 dias úteis (prorrogável por mais 10 com "
            "justificativa). Toda reclamação de ouvidoria gera relatório mensal para diretoria."
        ),
    },
    {
        "secao": "4.3",
        "titulo": "Canal — Banco Central / Procon",
        "texto": (
            "Banco Central / Procon: URGÊNCIA AUTOMATICAMENTE CRÍTICA quando a reclamação chega por "
            "esse canal, independente do conteúdo do texto. Prazo conforme determinação do órgão "
            "(geralmente 10 dias úteis). Resposta deve ser revisada pelo jurídico antes do envio. "
            "Notificar diretoria de Compliance em até 2h após recebimento."
        ),
    },
    {
        "secao": "4.4",
        "titulo": "Canal — Redes Sociais",
        "texto": (
            "Redes Sociais: resposta pública em até 2h (mesmo que só confirmação de recebimento). "
            "Migrar atendimento para canal privado (DM/inbox) imediatamente. Monitorar repercussão -- "
            "se viralizar, acionar equipe de Comunicação. Risco reputacional -- notificar gerência de "
            "Marketing."
        ),
    },
    {
        "secao": "5",
        "titulo": "Proteção de dados e conformidade",
        "texto": (
            "Nenhuma informação pessoal do cliente (CPF, número de conta, dados de cartão) pode ser "
            "incluída em relatórios gerenciais ou compartilhada fora da área responsável. Toda "
            "comunicação com o cliente deve seguir diretrizes LGPD. Gravações e registros armazenados "
            "por no mínimo 5 anos. Acesso aos dados da reclamação restrito à equipe designada para o "
            "caso."
        ),
    },
    {
        "secao": "6",
        "titulo": "Indicadores e acompanhamento",
        "texto": (
            "SLA de primeira resposta monitorado diariamente por urgência. Taxa de resolução no "
            "primeiro contato: meta mínima de 40%. NPS pós-atendimento enviado após resolução. "
            "Reclamações reincidentes: alerta automático se mesmo cliente reclamar 3+ vezes em 90 dias. "
            "Relatório semanal consolidado para diretoria."
        ),
    },
]
