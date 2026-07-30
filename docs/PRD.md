# FinGuard — Escudo de Compliance e Risco Regulatório

PRD do desafio Future Minds 3 (Zup), trilha Zup. Entrega: 30/07/2026. Alvo: Nível 3.

## Status de implementação (atualizado 28/07)

**Níveis 1, 2 e 3 implementados e validados com chamada real**, tanto em desenvolvimento (OpenAI) quanto na conta Bedrock do projeto (Vivo/Zup). Pipeline completo — guardrail de entrada → triagem → risco (RAG com citação de cláusula) → guardrail de saída → relatório — funciona ponta a ponta via `python -m finguard.run`.

**Honesto sobre o que não está 100%**: o guardrail de entrada bloqueia a maioria dos ~10 casos de prompt injection do dataset, mas 2 ainda não têm bloqueio confirmado (ver `docs/TASKS.md`, tarefa 3.1, e ADR 0001 §7 pra a história completa de como chegamos até aqui). Mitigação estrutural: os agentes não têm nenhuma capacidade de acessar dado de cliente além da reclamação que estão processando — mesmo um guardrail incompleto não resulta em vazamento real. Documentar isso na apresentação é mais forte que esconder.

## 1. Problema

Instituições financeiras recebem milhares de reclamações por dia, em múltiplos canais (SAC, Ouvidoria, Redes Sociais, Banco Central, Procon), em texto livre, sem padronização. Hoje a triagem é manual, lenta e inconsistente. Reclamações com indício de fraude ou violação regulatória precisam ser escaladas para compliance — e um erro de escalonamento custa multa regulatória, dano de imagem ou vazamento de dado (LGPD).

## 2. Diferencial escolhido

A maioria das soluções vai construir um classificador genérico (categoria/produto/sentimento). O FinGuard foca no que gera **maior risco financeiro e de imagem**: proteger a instituição contra multa regulatória e vazamento de dado, não só rotear reclamação comum.

Três pilares:

1. **Defesa ativa** — Bedrock Guardrails como primeiro nó do grafo, bloqueando jailbreak, extração de system prompt, roubo de identidade e conteúdo que não é reclamação válida. Validado com casos reais presentes no dataset fornecido (~10+ tentativas de prompt injection identificadas em `dataset_finguard_desafio_3.csv`, canais Redes Sociais / Banco Central).
2. **Escalonamento automático correto** — qualquer indício de fraude, menção a Banco Central/Procon/Justiça ou vulnerabilidade extrema do cliente é classificado como urgência Crítica automaticamente, replicando a regra da política interna (POL-SAC-001, seção 2.4).
3. **Decisão auditável** — o parecer do Agente de Risco cita a seção exata da política interna (RAG) que justificou o veredito, em vez de devolver só um rótulo. Isso é o que um time de compliance/regulador exige na prática.

## 3. Usuário e cenário de uso

- Usuário: analista/gestor de SAC ou compliance de instituição financeira.
- Cenário: reclamação chega em texto livre → sistema classifica, aplica regras da política interna, gera parecer de risco com justificativa citada, e produz relatório gerencial acionável.
- Demo ao vivo (pitch banca): (1) reclamação comum sendo processada ponta a ponta; (2) tentativa de prompt injection do dataset sendo bloqueada pelo guardrail de entrada, em tempo real.

## 4. Escopo por nível (ver desafio oficial em `docs/[TERABYTE] Future Minds 3 — O Desafio (2).pdf`)

### Nível 1 — Classificador
Input: texto livre de reclamação. Output JSON: categoria, produto, sentimento, urgência, resumo (2-3 linhas, palavras impróprias ofuscadas). Urgência Crítica forçada por regra quando houver fraude/Bacen/Procon/vulnerabilidade, mesmo que o modelo hesite.

### Nível 2 — Orquestrador (LangGraph)
Grafo com no mínimo 3 etapas especializadas: `agente_triagem` → `agente_risco` → `agente_relatorio`. Logs de entrada/saída/tempo por agente. Relatório final em arquivo (JSON/Markdown/HTML) com dashboard resumido, lista de críticas e recomendações de ação.

### Nível 3 — Escudo de Compliance (entrega alvo)
Tudo do Nível 2, mais:
- Guardrail de entrada (Bedrock, ID + version já provisionados) como primeiro nó obrigatório do grafo — bloqueia prompt injection, extração de system prompt, ameaças, conteúdo que não é reclamação válida.
- Guardrail de saída — garante que CPF, número de conta e outros dados sensíveis nunca aparecem nas saídas dos agentes nem no relatório final.
- Resposta de bloqueio educada, em português, sem expor detalhe interno do sistema.
- ADR (Architectural Decision Record) em HTML navegável: contexto, alternativas consideradas (mínimo 2), decisão, trade-offs, análise de custo por modelo, recomendações de segurança.
- Justificativa de custo: por que cada modelo foi escolhido, comparação de custo por token, uso de modelo leve para triagem vs. modelo robusto para risco.
- Agente de risco cita a seção da política interna (RAG) que fundamentou o parecer.

Fora de escopo por decisão: Nível 4 (SageMaker/clustering não supervisionado) — não entra na entrega, é bônus sem penalidade se não feito.

## 5. Dataset

`dataset_finguard_desafio_3.csv` — ~500 reclamações fictícias. Campos: `id`, `data_reclamacao`, `canal`, `texto_reclamacao`, `produto` (pode estar vazio), `status`. Contém casos limpos, casos ambíguos, e casos de ataque (prompt injection) misturados nos canais Redes Sociais e Banco Central — usar esses últimos como suíte de teste do guardrail de entrada.

## 6. Requisitos não funcionais

- Execução local, sem persistência em nuvem (sem AWS S3).
- Nenhum dado sensível do cliente nas saídas dos agentes ou relatório.
- Guardrail de entrada é sempre o primeiro nó — nenhuma reclamação processada sem passar por ele.
- Respostas de bloqueio em português, tom educado, sem detalhe interno.
- Logs rastreáveis por agente (entrada, saída, tempo de resposta).
- ADR entregue como HTML navegável junto ao repositório.

## 7. Critérios de avaliação (peso oficial da banca)

| Critério | Peso |
|---|---|
| Funcionalidade (demo ao vivo) | 30% |
| Uso de ferramentas de IA | 20% |
| Arquitetura e design | 20% |
| Segurança e governança | 15% |
| Apresentação e justificativa | 15% |

Pergunta obrigatória da banca: "Quais ferramentas de IA você utilizou e como elas contribuíram para a sua solução?"

## 8. Riscos e mitigação

- **Risco**: prompt engineering do guardrail falhar ao vivo. **Mitigação**: testar os ~10 casos de injection do dataset antes do evento, na máquina com Bedrock, com folga antes de 30/07.
- **Risco**: RAG citar seção errada da política. **Mitigação**: RAG formal simples (1 chunk por seção, ~15 chunks), retrieval top-3, testado com casos por produto/canal antes da entrega.
- **Risco**: divergência de comportamento entre modelo de dev (OpenAI, máquina pessoal) e modelo de produção (Claude via Bedrock, máquina Zup). **Mitigação**: bateria de testes completa na máquina Zup antes do evento, recalibrar prompts se necessário.
