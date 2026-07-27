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
- [~] **Máquina Zup / conta AWS**: **risco residual real, não "sem risco".** O acesso é a conta AWS de **desenvolvimento** do projeto Vivo (cliente Zup do usuário) — usada só pra teste, não produção. Importante: a regra 2 não proíbe só "produção" — o texto lista nomeadamente três categorias vedadas: **"produção, homologação ou desenvolvimento institucional"**. Uma conta de desenvolvimento de projeto institucional é literalmente o terceiro item dessa lista, não uma exceção a ela. "É só ambiente de dev, não é prod" não resolve a leitura literal da regra.
  - O que reduz o risco na prática, mas não elimina: acesso já testado e funcional (Guardrail ID + version 1 criado), uso restrito à janela do desafio (sem testes extensivos pra limitar custo/exposição), sistema só chama endpoint de inferência e Guardrail — nunca toca bucket, banco ou recurso real do projeto Vivo.
  - O que sustenta o participante mesmo assim: a tabela oficial do desafio diz que pra trilha Zup o Bedrock é "conta AWS própria (custo estimado)" — sem fornecer alternativa sandbox central — e o usuário confirmou com o time Zup que usar conta de projeto (mesmo institucional) é a prática esperada e comum entre os participantes dessa trilha.
  - **Recomendação que não mudou**: pela leitura literal da regra 2, o ideal é confirmar por escrito (e-mail/Slack) com quem organiza o Future Minds que "conta de desenvolvimento de projeto Zup" está dentro do aceitável — não deixar essa interpretação só entre você e o time interno da Zup, já que quem valida a regra do desafio é a organização do desafio, não o empregador.

## 3. Desprovisionamento de recursos

> "Todos os recursos cloud que gerem custo (...) devem ser desprovisionados imediatamente após o término do evento. A responsabilidade pelo desprovisionamento é da equipe participante, e custos gerados por negligência após o prazo de encerramento serão de responsabilidade do participante ou de sua gestão direta."

- [x] Não criamos SageMaker, instâncias ou buckets S3 (fora de escopo por decisão — nível 4 não entra na entrega).
- [x] Guardrail (ID + version) foi criado pelo próprio usuário, na conta pessoal, exclusivamente para o desafio — não é recurso compartilhado nem pré-existente.
- [ ] **Ação obrigatória pós-evento, dono: você.** Deletar o Guardrail (e qualquer outro recurso Bedrock criado pra isso) na sua conta AWS pessoal logo após a apresentação de 30/07 — mesmo dia, não deixar pra depois. Custo gerado por esquecimento é responsabilidade sua conforme a regra. Sugestão: colocar isso como último item do checklist do dia do evento, junto com "printar/gerar o relatório final antes de desligar tudo".

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
