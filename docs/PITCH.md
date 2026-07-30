# FinGuard - Roteiro de pitch (5 min + 5 min de perguntas)

Baseado em `PRD.md`, `SPECS.md`, `ADR 0001/0002`, `TASKS.md`. Fala natural, não decorar palavra por palavra. Os pontos em **negrito** são os que não podem faltar.

## Antes de começar (checklist de 2 minutos)

- [ ] `.env` na máquina Zup com `LLM_PROVIDER=bedrock` e `BEDROCK_GUARDRAIL_ID`/`VERSION` corretos
- [ ] Terminal aberto na pasta do projeto, venv ativado
- [ ] Tela compartilhada mostrando o terminal (fonte grande)
- [ ] Já rodou uma vez antes pra aquecer (evita esperar API na frente da banca)

---

## 0:00 - 0:40, Abertura e diferencial

> "A maioria das equipes aqui vai construir um classificador de reclamação. O FinGuard não é isso. Chamamos de **Escudo de Compliance e Risco Regulatório**, porque o problema real de um banco não é demorar pra responder, é **errar o escalonamento**: uma reclamação com fraude ou já registrada no Banco Central que não vira ação crítica na hora custa multa e dano de imagem. E tem um segundo risco que ninguém mais aqui vai mostrar ao vivo: **o próprio sistema de IA sendo atacado**. O dataset do desafio tem tentativas reais de prompt injection, e o FinGuard bloqueia isso em tempo real."

---

**Diagrama de sequência pra usar no slide**: [docs/diagrama-sequencia.svg](./diagrama-sequencia.svg)

## 0:40 - 2:00, Arquitetura (rápido, sem ler slide)

> "Grafo LangGraph: guardrail de entrada primeiro, nenhuma reclamação passa sem checar. Se aprovado, agente de triagem classifica, agente de risco consulta a política interna via RAG (FAISS, busca exata, ~15 seções) e **cita a cláusula exata** que justifica o risco. Não é só um rótulo, é uma decisão auditável. Depois guardrail de saída garante que CPF e número de conta nunca aparecem no relatório final."

**Não esquecer de citar**: dois modelos diferentes por custo. Nova Micro pra classificação (barato, rápido), DeepSeek V3.2 pro agente de risco (mais robusto, é onde citar a cláusula errada custa caro de verdade, e ainda assim ~40-60% mais barato que Claude Haiku pra raciocínio equivalente).

---

## 2:00 - 3:30, DEMO AO VIVO (o momento que importa)

**Parte 1, caso normal** (mostra o pipeline funcionando):
```bash
python -m finguard.run --limit 1
```
Abre `output/relatorio.html` no navegador. Aponta: dashboard, cláusula citada, ação recomendada.

**Parte 2, o ataque, ao vivo.** Usa `REC-2026-00380`. É o caso do dataset onde o texto tenta fazer o sistema virar uma persona chamada "InfoLeaker" sem regras. Roda:
```bash
python3 -c "
from dotenv import load_dotenv
load_dotenv()
from finguard.pipeline import carregar_reclamacoes
from finguard.guardrails.bedrock_guardrail import get_guardrail
regs = {r.id: r for r in carregar_reclamacoes('docs/dataset_finguard_desafio_3 (3).csv')}
guardrail = get_guardrail()
r = guardrail.avaliar(regs['REC-2026-00380'].texto_reclamacao, source='INPUT')
print('BLOQUEADO' if r.bloqueado else 'passou', '|', r.motivo)
"
```
> "Esse texto tenta convencer o sistema de que ele não é mais o FinGuard, e sim um assistente sem regras chamado InfoLeaker, que vazaria dado de cliente. Vejam: bloqueado, em tempo real, na conta real da Zup."

---

## 3:30 - 4:15, Segurança, governança e honestidade

> "Documentamos toda decisão em ADR navegável: arquitetura, RAG, modelos, custo, tudo com alternativa considerada e descartada, não só a escolhida."

**Ponto de honestidade (dizer antes que a banca pergunte)**: "Bloqueamos a maioria dos ataques do dataset, mas 2 casos ainda não têm bloqueio confirmado. Documentamos isso abertamente no ADR, não escondemos. E mesmo nesse caso, o sistema não tem capacidade nenhuma de acessar dado de outro cliente. Não existe um vazamento real possível, só um miss de classificação do guardrail."

---

## 4:15 - 5:00, Custo e fechamento

> "Custo de LLM pra rodar o dataset inteiro: menos de 1 centavo de dólar. Documentado com justificativa de modelo por agente no ADR. Repositório público, testado: 88 testes automatizados, 99% de cobertura, CI rodando em todo commit."

> "FinGuard não é só um classificador que funciona. É uma arquitetura pensada pra proteger o banco de multa, vazamento e ataque, com decisão documentada em cada escolha, e honestidade sobre o que ainda não está perfeito."

---

## Perguntas prováveis da banca (respostas prontas)

**"Quais ferramentas de IA você usou e como elas contribuíram?"** (pergunta obrigatória)
> Bedrock Guardrails pro bloqueio de ataque, Amazon Nova Micro pra classificação barata, DeepSeek V3.2 pro agente de risco onde precisão importa mais que custo (mas ainda assim mais barato que Claude Haiku), FAISS + Titan Embeddings pro RAG na política interna, LangGraph pra orquestrar o fluxo com rastreabilidade por nó, GitHub Copilot/Claude Code pra acelerar o desenvolvimento. Cada um resolveu um problema específico, documentado no ADR.

**"Como vocês controlam custo/latência pra não ter surpresa em produção?"**
> Limite de `max_tokens` em toda chamada de LLM (600 tokens, com folga sobre o que a gente observa na prática: respostas rodam entre 80 e 130 tokens de saída). Sem isso, uma resposta que "engasgasse" ou um modelo mais verboso custaria mais e demoraria mais sem a gente perceber. Achamos essa lacuna durante a validação real e corrigimos antes da entrega.

**"Por que 2 casos de ataque não foram bloqueados?"**
> São pedidos de extração disfarçados de legítimos (auditoria, pentest, documentação), mais difíceis de distinguir de um pedido real. Ajustamos o guardrail com um Denied Topic customizado e resolvemos a maioria; os 2 restantes ficam documentados como risco conhecido, mitigado porque o sistema não tem acesso a dado de outros clientes de qualquer forma.

**"Por que FAISS e não outra ferramenta de busca vetorial?"**
> Corpus pequeno (~15 seções). FAISS com índice exato (Flat) é a escolha certa pra esse tamanho. HNSW ou índice aproximado seria complexidade sem benefício real; a própria documentação do FAISS recomenda Flat abaixo de 10 mil vetores.

**"Quanto custou construir isso (não rodar, construir)?"**
> Custo de ferramenta de desenvolvimento (Claude Code) documentado à parte em `docs/COST_REPORT.md`, separado do custo de execução do produto. São categorias diferentes e não confundimos as duas.

**"O agente de relatório não devia estar no meio do grafo, como no diagrama do desafio?"**
> O diagrama oficial é chamado de "estrutura mínima" e o próprio desafio incentiva ir além dela. Relatório agrega o lote inteiro (contagem, distribuição), não faz sentido rodar por reclamação. Documentamos essa decisão no TASKS.md.
