# Checklist de conformidade — regras do desafio

Confere nossa solução contra as "Notas de compromisso" e os "Requisitos não funcionais" do documento oficial (`docs/[TERABYTE] Future Minds 3 — O Desafio (2).pdf`). Isso é premissa do projeto — quebrar qualquer item aqui é motivo de desclassificação, não é detalhe técnico.

## 1. Dados e privacidade

> "Todos os participantes devem utilizar exclusivamente o dataset fornecido pela equipe do Future Minds. É proibido incorporar dados reais de clientes, colaboradores ou qualquer informação oriunda de ambientes corporativos de produção, mesmo para fins de teste ou enriquecimento."

- [x] Única fonte de dado usada é `docs/dataset_finguard_desafio_3 (3).csv`, fornecido pelo desafio.
- [x] Política interna usada no RAG (`docs/KS_POLITICA_INTERNA (2).pdf`) também é documento fornecido pelo desafio, não é política real de produção.
- [x] Nenhum dado real de cliente/colaborador da Zup ou de terceiros entra no sistema, em nenhuma etapa (dev ou demo).

## 2. Ambientes de execução

> "A implementação deve ocorrer exclusivamente nos ambientes designados para o desafio. Fica vedado o uso de ambientes corporativos de produção, homologação ou desenvolvimento institucional, incluindo buckets, endpoints, bancos de dados ou qualquer recurso vinculado a operações reais."

- [x] Máquina pessoal: só usada para desenvolvimento de código e testes de lógica com `OpenAIClient` (conta pessoal, fora de qualquer ambiente Zup) — sem risco de tocar ambiente corporativo.
- [x] **Máquina Zup / conta AWS**: confirmado com o time organizador. Testes de Bedrock rodam em conta AWS própria do usuário (conta pessoal, não a corporativa de produção), conforme a tabela "Diferenças por público" do desafio ("Bedrock: Conta AWS própria (custo estimado)" para Zup). Sem uso de ambiente corporativo real.

## 3. Desprovisionamento de recursos

> "Todos os recursos cloud que gerem custo (...) devem ser desprovisionados imediatamente após o término do evento. A responsabilidade pelo desprovisionamento é da equipe participante, e custos gerados por negligência após o prazo de encerramento serão de responsabilidade do participante ou de sua gestão direta."

- [x] Não criamos SageMaker, instâncias ou buckets S3 (fora de escopo por decisão — nível 4 não entra na entrega).
- [ ] **Ação pendente pós-evento**: confirmar com o time Zup se o Guardrail (ID + version) foi criado só para o desafio ou é recurso compartilhado — se foi criado só para isso, precisa ser removido/desprovisionado por vocês (ou por quem provisionou) logo após 30/07. Anotar isso como item de checklist do dia do evento, não deixar para depois.

## 4. Requisitos não funcionais por nível

| Requisito | Nível | Status | Onde |
|---|---|---|---|
| Executa localmente, sem persistir em S3 | 1–3 | Planejado | `SPECS.md` §1, saída sempre em arquivo local |
| Logs de execução (entrada, saída, tempo por agente) | 2–3 | Planejado | `SPECS.md` §6 (estado do grafo) |
| Fluxo rastreável (identificar em qual agente a reclamação está) | 2–3 | Planejado | Logs por nó do LangGraph |
| Relatório final em arquivo (JSON/Markdown/HTML) | 2–3 | Planejado | `agente_relatorio`, saída `.html` + `.json` |
| Guardrail/tópico é sempre o primeiro nó do grafo | 3 | Planejado | `SPECS.md` §3 e §6 (grafo) |
| Nenhum dado sensível do cliente nas saídas dos agentes ou relatório | 3 | Planejado | Guardrail de saída + regex de reforço, `SPECS.md` §3 |
| Respostas de bloqueio educadas, em português, sem detalhe interno | 3 | Planejado | `SPECS.md` §3 |
| ADR entregue como HTML navegável junto ao repositório | 3 | **Feito** | `docs/adr/0001-arquitetura-e-modelos.html` |

## 5. Pendências que precisam de resposta sua antes de codar

1. ~~Confirmar se Bedrock/Guardrail em mãos é conta designada para o desafio~~ — **resolvido**: conta própria, confirmada com o time.
2. Confirmar responsável por desprovisionar o Guardrail após 30/07, se aplicável (item 3 acima). Ainda em aberto — anotar como item do checklist do dia do evento.
