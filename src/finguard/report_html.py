import html

from finguard.schemas import RelatorioOutput

_CSS = """
body { font-family: -apple-system, Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; color: #1a1a2e; }
h1 { border-bottom: 2px solid #1a1a2e; padding-bottom: .5rem; }
h2 { margin-top: 2rem; }
.bar-row { display: flex; align-items: center; gap: .75rem; margin: .35rem 0; }
.bar-label { width: 180px; font-size: .9rem; text-align: right; }
.bar-track { flex: 1; background: #f0f0f4; border-radius: 4px; height: 22px; position: relative; }
.bar-fill { background: #1a1a2e; height: 100%; border-radius: 4px; }
.bar-count { position: absolute; left: 8px; top: 2px; font-size: .8rem; color: #fff; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .9rem; }
th, td { border: 1px solid #ccc; padding: .5rem .7rem; text-align: left; }
th { background: #1a1a2e; color: #fff; }
.critico { color: #b91c1c; font-weight: 600; }
"""


def _barras(titulo: str, dados: dict[str, int]) -> str:
    if not dados:
        return f"<h2>{html.escape(titulo)}</h2><p>Sem dados.</p>"
    maximo = max(dados.values())
    linhas = []
    for label, count in sorted(dados.items(), key=lambda item: -item[1]):
        largura_pct = (count / maximo) * 100 if maximo else 0
        linhas.append(
            f'<div class="bar-row"><div class="bar-label">{html.escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{largura_pct:.1f}%">'
            f'<span class="bar-count">{count}</span></div></div></div>'
        )
    return f"<h2>{html.escape(titulo)}</h2>" + "\n".join(linhas)


def _tabela_criticas(relatorio: RelatorioOutput) -> str:
    if not relatorio.criticas:
        return "<h2>Reclamações críticas</h2><p>Nenhuma reclamação crítica neste lote.</p>"
    linhas = "\n".join(
        f"<tr><td>{html.escape(c.id)}</td><td class='critico'>{html.escape(c.nivel_risco.value)}</td>"
        f"<td>{html.escape(c.clausula_referencia)}</td><td>{html.escape(c.justificativa)}</td></tr>"
        for c in relatorio.criticas
    )
    return (
        "<h2>Reclamações críticas</h2>"
        "<table><tr><th>ID</th><th>Risco</th><th>Cláusula</th><th>Justificativa</th></tr>"
        f"{linhas}</table>"
    )


def _lista_recomendacoes(relatorio: RelatorioOutput) -> str:
    if not relatorio.recomendacoes:
        return "<h2>Recomendações</h2><p>Nenhuma ação pendente.</p>"
    itens = "\n".join(f"<li>{html.escape(r)}</li>" for r in relatorio.recomendacoes)
    return f"<h2>Recomendações de ação</h2><ul>{itens}</ul>"


def renderizar(relatorio: RelatorioOutput) -> str:
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="UTF-8">
<title>FinGuard — Relatório gerencial</title>
<style>{_CSS}</style></head>
<body>
<h1>FinGuard — Relatório gerencial</h1>
<p>Total de reclamações processadas: <strong>{relatorio.dashboard.total}</strong></p>
{_barras("Por urgência", relatorio.dashboard.por_urgencia)}
{_barras("Por categoria", relatorio.dashboard.por_categoria)}
{_barras("Por produto", relatorio.dashboard.por_produto)}
{_tabela_criticas(relatorio)}
{_lista_recomendacoes(relatorio)}
</body></html>
"""
