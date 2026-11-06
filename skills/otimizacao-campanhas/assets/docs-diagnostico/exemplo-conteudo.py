"""Gera os elementos do Doc de comitê / Sprint Growth a partir do dados.json. Copie e adapte por cliente.

Uso:  python3 -I exemplo-conteudo.py dados.json contexto.json --saida elementos.json

Números vêm do dados.json. O que é julgamento ou vem de fora dele (decisão de verba, semana anterior, meta, gargalo, 5W1H)
vem do contexto.json: ver contexto.exemplo.json. Nomes de lead e de vendedor não entram: o Doc costuma ser editável por link.
"""
import argparse, json

ap = argparse.ArgumentParser()
ap.add_argument('dados')
ap.add_argument('contexto')
ap.add_argument('--saida', default='elementos.json')
a = ap.parse_args()
D, X = json.load(open(a.dados)), json.load(open(a.contexto))
T, Q = D['totais'], D['qualidade']
INV_M, INV_G = T['investimento'].get('meta', 0), T['investimento'].get('google', 0)
INV = INV_M + INV_G


def n(x, d=0): return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
def brl(x, d=0): return 'R$ ' + n(x, d)
def pct(p, q, d=1): return n(p / q * 100, d) + '%' if q else '—'
def custo(i, c): return brl(i / c) if c and i else '—'


E = []
def P(*runs, style='NORMAL', bullet=False, italic=False):
    rr = [{'t': r} if isinstance(r, str) else dict(r) for r in runs]
    if italic:
        for r in rr:
            r['i'] = True
    E.append({'k': 'p', 'runs': rr, 'style': style, 'bullet': bullet})
def B(t): return {'t': t, 'b': True}
def T_(rows, widths): E.append({'k': 't', 'rows': [[str(c) for c in r] for r in rows], 'widths': widths})
def H3(t): P(t, style='H3')


def soma(tree, k): return sum(x[k] for x in tree)


def linha(no, *extra):
    return [no['name'], brl(no['invest']), no['leads'], no['mql'], custo(no['invest'], no['mql']), pct(no['mql'], no['leads']), no['sql'], no['venda'], *extra]


def ranking(tree, chave='mql'):
    com = [x for x in tree if x['invest'] > 0 and not x.get('synthetic')]
    return sorted(com, key=lambda x: (x['invest'] / x[chave]) if x[chave] else float('inf'))


CAB = ['Item', 'Invest.', 'Leads', 'MQL', 'Custo/MQL', 'Lead → MQL', 'SQL', 'Vendas']
LARG = [250, 80, 55, 55, 75, 75, 55, 60]
meta, goo = D['META_TREE'], D['GOOGLE_TREE']

P(X['titulo'], style='H2')
P(B('Resumo: '), f"{X['periodo_texto']}: {brl(INV)} investidos (Meta {brl(INV_M)}, Google {brl(INV_G)}), {n(T['leads'])} leads, {n(T['mql'])} MQL, {n(T['sql'])} SQL e {n(T['venda'])} vendas. ", B(X['decisao_verba']))
P(B('Dashboard: '), {'t': X['dashboard_url'], 'link': X['dashboard_url']}, f" {X.get('dashboard_descricao', 'traz a árvore por campanha, público e anúncio.')}")
P(X['metodo'], italic=True)

H3('1. Funil completo')
A = X.get('semana_anterior')
linhas = [['Etapa', 'Semana anterior', 'Atual']] if A else [['Etapa', 'Atual']]
for rot, chave, val in (('Investimento', 'investimento', brl(INV)), ('Leads', 'leads', n(T['leads'])), ('MQL', 'mql', n(T['mql'])), ('SQL', 'sql', n(T['sql'])), ('Vendas', 'venda', n(T['venda']))):
    linhas.append([rot, A.get(chave, '—'), val] if A else [rot, val])
T_(linhas, [160, 120, 120] if A else [160, 120])
M = X.get('meta_mes')
if M:
    fr = M['fracao_do_mes']
    T_([['Ritmo × meta', 'Meta do mês', 'Esperado até hoje', 'Realizado']] +
       [[r, n(M[k]), n(M[k] * fr), n(T[k])] for r, k in (('Leads', 'leads'), ('MQL', 'mql'), ('SQL', 'sql'), ('Vendas', 'venda'))], [140, 110, 130, 100])
T_([['Estado', 'Leads', '% do total'], ['Qualificado', T['mql'], pct(T['mql'], T['leads'])], ['Desqualificado', T['desqualificados'], pct(T['desqualificados'], T['leads'])], ['Em aberto', T['em_aberto'], pct(T['em_aberto'], T['leads'])]], [160, 80, 90])

H3('2. Funil no CRM e gargalo')
if X.get('etapas_atuais'):
    T_([['Etapa atual', 'Leads', 'Mediana de dias na etapa']] + X['etapas_atuais'], [220, 70, 170])
for g in X.get('gargalos', []):
    P(g, bullet=True)

H3('3. Por canal')
T_([['Canal', 'Invest.', 'Leads', 'MQL', 'SQL', 'Vendas', 'CPL', 'Custo/MQL', 'Lead → MQL', 'CAC']] +
   [[c, brl(soma(t, 'invest')), soma(t, 'leads'), soma(t, 'mql'), soma(t, 'sql'), soma(t, 'venda'), custo(soma(t, 'invest'), soma(t, 'leads')), custo(soma(t, 'invest'), soma(t, 'mql')), pct(soma(t, 'mql'), soma(t, 'leads')), custo(soma(t, 'invest'), soma(t, 'venda'))]
    for c, t in (('Meta', meta), ('Google', goo))], [60, 75, 50, 50, 50, 55, 60, 70, 75, 65])

H3('4. Leads de campanha sem UTM')
T_([['Tipo', 'Leads'], ['Sem UTM ou canal', Q.get('sem_utm', 0) + Q.get('canal_desconhecido', 0)], ['Macro não substituída', Q.get('utm_quebrada', 0)], ['Campanha sem match na mídia', Q.get('campanha_sem_match', 0)]], [240, 70])

H3('5. Ranking de campanhas')
P(B('Meta, por campanha'))
T_([CAB] + [linha(x) for x in ranking(meta)], LARG)
conj = [c for x in meta for c in x.get('children', [])]
P(B('Meta, por conjunto'))
T_([CAB] + [linha(x) for x in ranking(conj)[:10]], LARG)
gasto7 = X.get('gasto_7_dias', {})
anuncios = [ad for c in conj for ad in c.get('children', [])]
P(B('Meta, por anúncio'))
T_([CAB + ['Gasto últimos 7 dias']] + [linha(x, gasto7.get(x['name'], '—')) for x in ranking(anuncios)[:10]], LARG + [95])
P(B('Google, por campanha'))
T_([CAB] + [linha(x) for x in ranking(goo)], LARG)
P(B('Google, por palavra-chave'))
T_([CAB] + [linha(x) for x in ranking(D['GOOGLE_KEYWORDS'])[:10]], LARG)
P('Custo por MQL não é tudo: compare até onde cada item chega no funil antes de escalar.', bullet=True)

H3('6. Onde investir mais, menos e o que desativar')
for rot in ('Investir mais', 'Manter sem escalar', 'Investir menos ou pausar'):
    P(B(rot))
    T_([['Item', 'Nível', 'Números', 'Ação']] + (X['decisoes'].get(rot) or [['—', '—', '—', '—']]), [190, 70, 170, 190])
P(B('Anúncios para desativar'))
T_([['Anúncio', 'Campanha', 'Gasto últimos 7 dias', 'Motivo']] + (X.get('desativar') or [['—', '—', '—', '—']]), [170, 170, 110, 170])
P(B('Pra onde vai a verba: '), X.get('para_onde_vai', ''))

H3('7. UTMs e contas')
for u in X.get('utms_contas', []):
    P(u, bullet=True)

H3('Próximos passos')
for foco, resto in X.get('proximos_passos', []):
    P(B(foco + ': '), resto, bullet=True)

H3('Planos de ação (5W1H)')
T_([['O quê', 'Por quê', 'Como', 'Quem', 'Quando', 'Onde/métrica']] + (X.get('planos') or [['—'] * 6]), [120, 130, 140, 70, 70, 100])
E.append({'k': 'rule'})
json.dump(E, open(a.saida, 'w'), ensure_ascii=False, indent=1)
print(len(E), 'elementos em', a.saida)
