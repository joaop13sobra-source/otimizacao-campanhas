"""Injeta o dados.json no motor (assets/reference-otimizacao-campanhas.html) e grava o dashboard.

Uso:  python3 -I gerar_html.py dados.json --saida deploy/index.html [--template caminho.html]
Narrativa: o bloco "notas" do config (achados, leitura) entra no HTML como escrito. Números de qualidade são automáticos.
"""
import argparse, datetime, html, json, re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / 'assets' / 'reference-otimizacao-campanhas.html'
CHAVES = ('META_TREE', 'GOOGLE_TREE', 'GOOGLE_KEYWORDS', 'LOSS_REASONS', 'QUALIFIED_LOST_REASONS')


def br(iso):
    return datetime.date.fromisoformat(iso).strftime('%d/%m/%Y')


def int_br(n):
    return f'{n:,}'.replace(',', '.')


def nota_qualidade(q, etapas):
    partes = []
    fora = q.get('sem_utm', 0) + q.get('canal_desconhecido', 0)
    if fora:
        partes.append(f"{int_br(fora)} leads sem UTM ou sem canal identificado ficam fora das árvores ({int_br(q.get('mql_fora_da_arvore', 0))} deles qualificados)")
    if q.get('campanha_sem_match'):
        partes.append(f"{int_br(q['campanha_sem_match'])} com campanha que não aparece na mídia do período (nó sintético, investimento R$ 0)")
    if q.get('utm_quebrada'):
        partes.append(f"{int_br(q['utm_quebrada'])} com UTM quebrada, macro não substituída (nó sintético)")
    if q.get('organico'):
        partes.append(f"{int_br(q['organico'])} orgânicos, fora da análise de mídia")
    if q.get('teste'):
        partes.append(f"{int_br(q['teste'])} leads de teste removidos")
    if q.get('campanha_excluida'):
        partes.append(f"{int_br(q['campanha_excluida'])} de campanhas excluídas da análise por decisão desta rodada")
    return ('; '.join(partes) + '.') if partes else 'Todos os leads pagos casaram com campanha da mídia.'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dados')
    ap.add_argument('--saida', default='index.html')
    ap.add_argument('--template', default=str(TEMPLATE))
    a = ap.parse_args()
    d = json.load(open(a.dados))
    h = open(a.template, encoding='utf-8').read()
    # </ não pode fechar o <script>: nome de campanha vem de fora
    js = lambda x: json.dumps(x, ensure_ascii=False).replace('</', '<\\/')
    for k in CHAVES:
        h, n = re.subn(rf'^const {k} = .*$', lambda _m, k=k: f'const {k} = {js(d[k])};', h, count=1, flags=re.M)
        assert n == 1, k
    M, Q, E = d['meta'], d['qualidade'], d['meta']['etapas']
    notas = M.get('notas') or {}
    aviso_hist = ('<strong>Limitação:</strong> a fonte não tem histórico de etapas. A qualificação usa só a etapa atual, então a taxa pode '
                  'estar subestimada: quem qualificou e depois foi perdido aparece como desqualificado.<br/><br/>') if Q.get('sem_historico') else ''
    # tabela mês a mês só quando o período cruza mais de um mês
    extras = notas.get('secoes_extras_geral', '')
    if len(d.get('por_mes', [])) > 1:
        linhas = ''.join(f"<tr><td>{m['mes']}</td><td class='num'>{m.get('leads', 0)}</td><td class='num'>{m.get('mql', 0)}</td><td class='num'>{m.get('sql', 0)}</td>"
                         f"<td class='num'>{m.get('venda', 0)}</td><td class='num'>{m.get('lost', 0)}</td></tr>" for m in d['por_mes'])
        extras += ('<section><div class="section-head"><h2>Mês a mês <span class="platform-badge">lead pelo mês de entrada</span></h2></div>'
                   '<div class="table-scroll"><table><thead><tr><th>Mês</th><th class="num">Leads</th><th class="num">MQL</th><th class="num">SQL</th><th class="num">Venda</th><th class="num">Desqualificados</th></tr></thead>'
                   f'<tbody>{linhas}</tbody></table></div></section>')
    vendas = ' + '.join(E.get('venda') or [])
    mapa = {
        'CLIENTE': html.escape(M['cliente']), 'PERIODO': f"{br(M['periodo']['inicio'])} a {br(M['periodo']['fim'])}",
        'PERIODO_INICIO': br(M['periodo']['inicio']), 'PERIODO_FIM': br(M['periodo']['fim']), 'CRM': html.escape(M['crm']),
        'ETAPA_MQL': html.escape(E['mql']), 'ETAPA_SQL': html.escape(E.get('sql') or '—'), 'ETAPA_VENDA': html.escape(vendas),
        'ROTULO_SQL': html.escape(E.get('rotulo_sql') or 'SQL'), 'ROTULO_VENDA': html.escape(E.get('rotulo_venda') or 'Venda'),
        'SELO': html.escape(notas.get('selo') or 'Dado real'), 'DATA_GERACAO': datetime.date.today().strftime('%d/%m/%Y'),
        'SECOES_EXTRAS_GERAL': extras, 'NOTA_GERAL': notas.get('geral', ''), 'NOTA_MQL': notas.get('qualificacao', ''),
        'NOTA_QUALIFICADOS_PERDIDOS': notas.get('qualificados_perdidos', ''), 'NOTA_DESQUALIFICACAO': notas.get('desqualificacao', ''),
        'NOTA_QUALIDADE': aviso_hist + '<strong>Qualidade de dado:</strong> ' + nota_qualidade(Q, E),
        'NOTA_QUALIDADE_MOTIVO': f"<strong>Qualidade de dado:</strong> {int_br(Q.get('perdidos_sem_motivo', 0))} leads perdidos sem motivo preenchido no CRM.",
    }
    # uma passada só: nome de campanha com {{...}} já injetado no JSON não pode ser confundido com placeholder
    h = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: mapa[m.group(1)] if m.group(1) in mapa else m.group(0), h)
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    open(a.saida, 'w', encoding='utf-8').write(h)
    print('gravado', a.saida, len(h))


if __name__ == '__main__':
    main()
