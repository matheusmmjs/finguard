import html
import time

from finguard.schemas import RelatorioOutput

_CSS = """
:root { --ink: #1c1c1e; --muted: #6b6b70; --line: #e4e4e7; --accent: #9a3412; --bg-soft: #fafafa; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; max-width: 720px; margin: 3rem auto; padding: 0 1.5rem; color: var(--ink); line-height: 1.5; }
.kicker { font-size: .72rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
h1 { font-size: 1.7rem; font-weight: 600; margin: .3rem 0 1.5rem; letter-spacing: -.01em; }
h2 { font-size: .78rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 2.75rem 0 1rem; }
.stats { display: flex; gap: 2.5rem; padding-bottom: 1.75rem; border-bottom: 1px solid var(--line); }
.stat-value { font-size: 1.9rem; font-weight: 600; }
.stat-label { font-size: .8rem; color: var(--muted); }
.bar-row { display: grid; grid-template-columns: 150px 1fr 2.2rem; align-items: center; gap: .9rem; margin: .55rem 0; font-size: .88rem; }
.bar-label { text-align: right; color: var(--ink); }
.bar-track { background: var(--bg-soft); height: 6px; border-radius: 3px; }
.bar-fill { background: var(--ink); height: 100%; border-radius: 3px; }
.bar-count { text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem 1.25rem; margin-bottom: .75rem; }
.card-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: .5rem; }
.card-id { font-size: .82rem; color: var(--muted); font-variant-numeric: tabular-nums; }
.card-risco { font-size: .72rem; font-weight: 600; letter-spacing: .05em; text-transform: uppercase; color: var(--accent); }
.card-clausula { font-size: .78rem; color: var(--muted); margin-bottom: .4rem; }
.card p { margin: 0; font-size: .92rem; }
.empty { color: var(--muted); font-size: .9rem; font-style: italic; }
ul.acoes { margin: 0; padding-left: 1.1rem; }
ul.acoes li { margin: .4rem 0; font-size: .92rem; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: .78rem; color: var(--muted); }
"""


def _barras(titulo: str, dados: dict[str, int]) -> str:
    if not dados:
        return f'<h2>{html.escape(titulo)}</h2><p class="empty">Sem dados.</p>'
    maximo = max(dados.values())
    linhas = []
    for label, count in sorted(dados.items(), key=lambda item: -item[1]):
        largura_pct = (count / maximo) * 100 if maximo else 0
        linhas.append(
            f'<div class="bar-row"><div class="bar-label">{html.escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{largura_pct:.1f}%"></div></div>'
            f'<div class="bar-count">{count}</div></div>'
        )
    return f"<h2>{html.escape(titulo)}</h2>" + "\n".join(linhas)


def _cards_criticas(relatorio: RelatorioOutput) -> str:
    if not relatorio.criticas:
        return '<h2>Reclamações críticas</h2><p class="empty">Nenhuma reclamação crítica neste lote.</p>'
    cards = "\n".join(
        f'<div class="card"><div class="card-head">'
        f'<span class="card-id">{html.escape(c.id)}</span>'
        f'<span class="card-risco">{html.escape(c.nivel_risco.value)}</span></div>'
        f'<div class="card-clausula">Política, seção {html.escape(c.clausula_referencia)}</div>'
        f"<p>{html.escape(c.justificativa)}</p></div>"
        for c in relatorio.criticas
    )
    return f"<h2>Reclamações críticas</h2>{cards}"


def _lista_recomendacoes(relatorio: RelatorioOutput) -> str:
    if not relatorio.recomendacoes:
        return '<h2>Recomendações</h2><p class="empty">Nenhuma ação pendente.</p>'
    itens = "\n".join(f"<li>{html.escape(r)}</li>" for r in relatorio.recomendacoes)
    return f'<h2>Recomendações de ação</h2><ul class="acoes">{itens}</ul>'


def renderizar(relatorio: RelatorioOutput) -> str:
    gerado_em = time.strftime("%d/%m/%Y às %H:%M", time.localtime())
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="UTF-8">
<title>FinGuard — Relatório gerencial</title>
<style>{_CSS}</style></head>
<body>
<div class="kicker">FinGuard</div>
<h1>Relatório gerencial</h1>
<div class="stats">
  <div><div class="stat-value">{relatorio.dashboard.total}</div><div class="stat-label">Processadas</div></div>
  <div><div class="stat-value">{len(relatorio.criticas)}</div><div class="stat-label">Críticas</div></div>
</div>
{_barras("Por urgência", relatorio.dashboard.por_urgencia)}
{_barras("Por categoria", relatorio.dashboard.por_categoria)}
{_barras("Por produto", relatorio.dashboard.por_produto)}
{_cards_criticas(relatorio)}
{_lista_recomendacoes(relatorio)}
<footer>Gerado em {gerado_em}</footer>
</body></html>
"""
