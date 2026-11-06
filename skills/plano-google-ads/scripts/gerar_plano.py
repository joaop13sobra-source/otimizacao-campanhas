#!/usr/bin/env python3
"""Monta a página HTML do plano de Google Ads (tema branco + vermelho, IBM Plex).

    python3 -I gerar_plano.py --dados dados.json --plano plano.json [--semrush semrush.json] --saida index.html

dados.json  = tudo que é calculado (analise.py).      plano.json = narrativa e decisões (escritas por quem analisa).
Textos do plano aceitam {{caminho.no.dados|formato}} (formatos: brl, brl0, pct, pct0, frac, frac0, n0, n1, raw; frac = fração 0,24 -> 24,0%), por exemplo
"CPL de {{kpis.cpl|brl}}" ou "{{campanhas[nome=Core].cpl|brl}}". Assim o texto nunca desencontra do número.
Esquema completo: references/formato-plano-json.md.
"""
import argparse
import html
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gads import brl as _brl, norm

E = html.escape


# --------------------------------------------------------------------------- formatação
def n0(x):
    return f'{x:,.0f}'.replace(',', '.') if x is not None and x == x else '-'


def n1(x):
    return f'{x:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if x is not None and x == x else '-'


def pc(x, d=1):
    return (f'{x:.{d}f}'.replace('.', ',') + '%') if x is not None and x == x else '-'


def brl(x, d=2):
    return _brl(x, d) if x is not None and x == x else '-'


def fmt(v, f):
    if v is None:
        return '-'
    return {'brl': lambda: brl(v), 'brl0': lambda: brl(v, 0), 'pct': lambda: pc(v), 'pct0': lambda: pc(v, 0),
            'n0': lambda: n0(v), 'n1': lambda: n1(v), 'frac': lambda: pc(v * 100), 'frac0': lambda: pc(v * 100, 0), 'raw': lambda: str(v)}.get(f, lambda: str(v))()


# --------------------------------------------------------------------------- {{caminho|formato}}
def resolver(dados, caminho):
    atual = dados
    for parte in re.split(r'\.(?![^\[]*\])', caminho):
        m = re.match(r'^([^\[]+)(?:\[([^=\]]+)=([^\]]+)\])?$', parte)
        if not m:
            return None
        nome, k, v = m.groups()
        atual = atual.get(nome) if isinstance(atual, dict) else None
        if atual is None:
            return None
        if k:
            achado = [x for x in atual if str(x.get(k)).lower().startswith(v.lower())]
            atual = achado[0] if achado else None
            if atual is None:
                return None
    return atual


class Tpl:
    def __init__(self, dados):
        self.d = dados
        self.faltando = []

    def __call__(self, texto):
        if not isinstance(texto, str):
            return texto

        def troca(m):
            caminho, _, f = m.group(1).partition('|')
            v = resolver(self.d, caminho.strip())
            if v is None:
                self.faltando.append(m.group(1))
                return '[[?' + m.group(1) + ']]'
            return fmt(v, f.strip() or 'raw')
        return re.sub(r'\{\{([^}]+)\}\}', troca, texto)


# --------------------------------------------------------------------------- html básico
CSS = '''
:root{color-scheme:light;--bg:#ffffff;--card:#ffffff;--soft:#f7f5f5;--fg:#141414;--fg2:#5a5a5a;--mut:#8a8585;--line:#e1dcdc;--axis:#c9c2c2;--red:#e50914;--redh:#c40712;--dark:#280001;--cream:#ffebc8;--good:#1e8a4c;--goodbg:#e4f4ea;--warn:#b06400;--warnbg:#fff1d6;--bad:#c40712;--badbg:#ffe9e7}
*{box-sizing:border-box}html{background:#fff}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
.bar{height:6px;background:var(--red)}
.top,.nav .in,main{max-width:1180px;margin:0 auto;padding-left:16px;padding-right:16px}.top{padding-top:22px;padding-bottom:16px}
.back{display:inline-block;margin-bottom:12px;font-size:12.5px;color:var(--fg2);text-decoration:none;font-weight:500}.back:hover{color:var(--red)}
.brand{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.brand .cl{height:46px;width:auto}.brand .co{height:22px;width:auto}
h1{font-size:25px;margin:0 0 6px;letter-spacing:-.015em;font-weight:700}.sub{color:var(--fg2);margin:0;font-size:13px}
.nav{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line)}.nav .in{display:flex;gap:2px;overflow-x:auto;padding-top:6px;padding-bottom:6px}
.nav a{padding:6px 10px;border-radius:6px;color:var(--fg2);text-decoration:none;white-space:nowrap;font-size:13px;font-weight:500}.nav a:hover{background:var(--soft);color:var(--red)}
main{padding-bottom:80px}section{scroll-margin-top:52px;padding-top:32px}
h2{font-size:20px;margin:0 0 2px;font-weight:700;display:flex;align-items:center;gap:9px}h2::before{content:"";width:5px;height:19px;background:var(--red);border-radius:2px;flex:none}
.lead{color:var(--fg2);margin:0 0 14px;font-size:13px}h3{font-size:15px;margin:0 0 8px;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:14px}.kpi{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi.hi{background:#fff;border-top:4px solid var(--red)}.kpi.hi .v{color:var(--red)}
.kpi .l{font-size:12.5px;color:var(--fg2)}.kpi .v{font-size:25px;font-weight:700;margin:2px 0 4px;letter-spacing:-.015em}.kpi .s{font-size:12px;color:var(--fg2)}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th{font-size:11.5px;font-weight:600;color:var(--fg2);text-align:right;padding:7px 8px;border-bottom:2px solid var(--fg);white-space:nowrap;vertical-align:bottom;background:var(--soft)}
td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;vertical-align:top}th.l,th:first-child,td.l{text-align:left}td.l{white-space:normal}
td.seg{min-width:200px;max-width:340px}td small{display:block;color:var(--mut);font-size:11.5px;line-height:1.35;margin-top:1px}td.txt{min-width:260px;max-width:460px;color:var(--fg2)}
tr.tot td{font-weight:700;border-top:2px solid var(--fg);border-bottom:none;background:var(--soft)}table.mini{font-size:12.5px}
td.kws{white-space:normal;text-align:left;min-width:360px}tr.grp td{text-align:left;background:var(--soft);font-weight:700;color:var(--red);border-bottom:1px solid var(--axis);padding-top:9px}
.st{display:inline-block;padding:1px 9px;border-radius:999px;font-size:11.5px;font-weight:600;white-space:nowrap}.st.ok{background:var(--goodbg);color:var(--good)}.st.warn{background:var(--warnbg);color:var(--warn)}.st.bad{background:var(--badbg);color:var(--bad)}
ul{margin:6px 0 0;padding-left:20px}li{margin:4px 0}ol{margin:0;padding-left:20px}.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px;margin-bottom:14px}.cols .card{margin:0}
.call{border-left:4px solid var(--red);background:var(--soft);border-radius:0 10px 10px 0;padding:12px 16px;margin:0 0 14px}
.call.warn{border-left-color:var(--warn);background:var(--warnbg)}.call.bad{border-left-color:var(--dark);background:var(--badbg)}.call b.k{color:var(--fg)}
.tag{display:inline-block;background:var(--soft);border:1px solid var(--line);color:var(--fg2);border-radius:6px;padding:1px 7px;font-size:12px;margin:2px 3px 2px 0;white-space:nowrap}
.tag.new{background:var(--goodbg);border-color:#b9dfc7;color:var(--good)}.tag b{color:var(--fg);font-weight:600;margin-left:3px}.tag.new b{color:var(--good)}
.note{color:var(--mut);font-size:12px;margin-top:8px}
.tl{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.tl .card{margin:0;border-top:4px solid var(--red)}.tl .d{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--red);font-weight:500;margin-bottom:4px}
footer{max-width:1180px;margin:0 auto;padding:0 16px 40px;color:var(--mut);font-size:12px}
@media (max-width:640px){.top{padding-top:16px}h1{font-size:21px}.brand .cl{height:38px}}
'''


def td(v, cls=''):
    return f'<td{" class=" + cls if cls else ""}>{v}</td>'


def row(cells, cls=''):
    return f'<tr{" class=" + cls if cls else ""}>' + ''.join(cells) + '</tr>'


def tab(head, rows, cls='', left=()):
    h = ''.join(f'<th{" class=l" if (i == 0 or i in left) else ""}>{E(x)}</th>' for i, x in enumerate(head))
    return f'<div class="wrap"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def call(tipo, titulo, texto):
    cls = {'warn': ' warn', 'bad': ' bad'}.get(tipo, '')
    return f'<div class="call{cls}"><b class="k">{titulo}</b> {texto}</div>'


def bullets(itens):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in itens) + '</ul>' if itens else ''


# --------------------------------------------------------------------------- seções
class Pagina:
    def __init__(self, dados, plano, semrush):
        self.d, self.p, self.sem = dados, plano, semrush or []
        self.T = Tpl(dados)
        self.k = dados['kpis']
        self.ref = dados.get('referencia')
        self.v = dados.get('vendas')
        self.termos_ativos = dados.get('termos_ativos', {})
        self.nomes_kw = set(dados.get('palavras_nomes', []))
        self.sem_idx = {norm(r['kw']): r for r in self.sem}
        self.secoes = []   # (id, rótulo)
        grupos_sem = []
        for g in plano.get('novas_palavras', {}).get('grupos', []):
            vols = [int(self.sem_idx[norm(k)]['vol'] or 0) for k in g.get('palavras', []) if norm(k) in self.sem_idx]
            grupos_sem.append(dict(titulo=g['titulo'], soma=sum(vols), n=len(g.get('palavras', []))))
        self.d['semrush'] = dict(grupo=grupos_sem)

    # util
    def t(self, x):
        return self.T(x)

    def camp(self, nome):
        for c in self.d['campanhas']:
            if c['nome'] == nome:
                return c
        return None

    def venda_palavra(self, nome):
        if not self.v:
            return None
        for s in self.v['segmentos']['palavra']:
            if s['nome'] == norm(nome):
                return s
        return None

    # ---------------------------------------------------------------- resumo
    def resumo(self):
        P = self.p.get('resumo', {})
        k, ref = self.k, self.ref
        kp = [('Custo (' + self.d['meta']['periodo'] + ')', brl(k['custo']), f"{len([c for c in self.d['campanhas'] if (c.get('custo') or 0) > 0])} campanhas"),
              ('Conversões', n1(k['conversoes']), self.p.get('conversao_rotulo', 'ação de conversão')),
              ('CPL', brl(k['cpl']), f"{ref['rotulo']}: {brl(ref['custo'] / ref['conversoes'])}" + (f" ({ref['fonte']})" if ref.get('fonte') else '') if ref else ''),
              ('CPC', brl(k['cpc']), f"{ref['rotulo']}: {brl(ref['custo'] / ref['cliques'])}" if ref else ''),
              ('Conversão por clique', pc(k['cvr']), f"{ref['rotulo']}: {pc(ref['conversoes'] / ref['cliques'] * 100)}" if ref else '')]
        kh = ''.join(f'<div class="kpi{" hi" if i == 2 else ""}"><div class="l">{a}</div><div class="v">{b}</div><div class="s">{c}</div></div>' for i, (a, b, c) in enumerate(kp))
        out = [f'<section id="resumo"><h2>Resumo</h2><p class="lead">{self.t(P.get("lead", "O que dá para afirmar com os dados do período e o que ainda depende de verificação."))}</p><div class="kpis">{kh}</div>']
        dc = self.d.get('decomposicao')
        if dc and not P.get('sem_callout_decomposicao'):
            sobe = 'subiu' if dc['var_cpl_pct'] > 0 else 'caiu'
            out.append(call('', f"O CPL {sobe} {abs(dc['var_cpl_pct']):.0f}% ({brl(dc['cpl_ref'])} em {ref['rotulo'].lower()} para {brl(k['cpl'])}).",
                            f"Cerca de {dc['parte_cpc_pct']}% da variação vem do CPC ({brl(dc['cpc_ref'])} para {brl(k['cpc'])}) e {dc['parte_conversao_pct']}% da conversão por clique ({pc(dc['cvr_ref'])} para {pc(k['cvr'])})."))
        for c in P.get('callouts', []):
            out.append(call(c.get('tipo', ''), self.t(c.get('titulo', '')), self.t(c.get('texto', ''))))
        if not P.get('ocultar_alertas_auto'):
            auto = [a for a in self.d.get('alertas', []) if not any(a['texto'][:30] in c.get('texto', '') for c in P.get('callouts', []))]
            for a in [a for a in auto if a['tipo'] == 'bad']:
                out.append(call('bad', 'Alerta automático.', E(a['texto'])))
            resto = [a for a in auto if a['tipo'] in ('warn', 'info')]
            if resto:
                out.append(call('warn', 'Alertas automáticos da conta.', bullets([E(a['texto']) for a in resto])))
        if P.get('alavancas'):
            rows = [row([td(self.t(a['nome']), 'l'), td(self.t(a['evidencia']), 'l txt'), td(self.t(a['efeito']), 'l'), td(self.t(a['confianca']), 'l')]) for a in P['alavancas']]
            out.append('<h3 style="margin-top:18px">Alavancas, em ordem de impacto potencial</h3>' + tab(['Alavanca', 'Evidência nos dados', 'Efeito possível no CPL', 'Confiança'], rows, left=(1, 2, 3)))
            if P.get('nota_alavancas'):
                out.append(f'<p class="note">{self.t(P["nota_alavancas"])}</p>')
        out.append('</section>')
        self.secoes.append(('resumo', 'Resumo'))
        return ''.join(out)

    # ---------------------------------------------------------------- diagnóstico
    def diagnostico(self):
        P = self.p.get('diagnostico', {})
        cs = [c for c in self.d['campanhas'] if (c.get('custo') or 0) > 0]
        tem_ip = any(c.get('parcela') == c.get('parcela') and c.get('parcela') is not None for c in cs)
        head = ['Campanha', 'Orçamento/dia', 'Custo', '% da verba', 'Cliques', 'CPC', 'Conv.', 'Conv./clique', 'CPL'] + (['Parcela de impr.', 'Perdida p/ orçamento', 'Perdida p/ classif.'] if tem_ip else [])
        rows = []
        for c in cs:
            r = [td(E(self.p.get('rotulos_campanha', {}).get(c['nome'], c['nome'])), 'l'), td(brl(c.get('orcamento'), 0)), td(brl(c['custo'])), td(pc(c['custo'] / self.k['custo'] * 100)),
                 td(n0(c['cliques'])), td(brl(c['cpc'])), td(n1(c['conv'])), td(pc(c['cvr'])), td(brl(c['cpl']))]
            if tem_ip:
                r += [td(pc(c.get('parcela'))), td(pc(c.get('perd_orc'))), td(pc(c.get('perd_class')))]
            rows.append(row(r))
        rows.append(row([td('Total', 'l'), td(brl(sum((c.get('orcamento') or 0) for c in cs), 0)), td(brl(self.k['custo'])), td('100%'), td(n0(self.k['cliques'])), td(brl(self.k['cpc'])),
                         td(n1(self.k['conversoes'])), td(pc(self.k['cvr'])), td(brl(self.k['cpl']))] + ([td('')] * 3 if tem_ip else []), 'tot'))
        out = [f'<section id="diag"><h2>Diagnóstico por campanha</h2><p class="lead">{self.t(P.get("lead", "Relatório de campanhas do Google Ads. CPL = CPC ÷ conversão por clique."))}</p><div class="card">{tab(head, rows)}']
        out.append(bullets([self.t(b) for b in P.get('bullets', [])]))
        if P.get('nota'):
            out.append(f'<p class="note">{self.t(P["nota"])}</p>')
        out.append('</div>')
        if self.v:
            out.append(self.lead_venda(P))
        out.append('</section>')
        self.secoes.append(('diag', 'Diagnóstico'))
        return ''.join(out)

    def lead_venda(self, P):
        v = self.v
        seg = v['segmentos']
        cpl = {c['nome']: c['cpl'] for c in self.d['campanhas']}
        rows, tl, tv, tg = [], 0, 0, 0
        for s in seg['campanha']:
            rows.append(row([td(E(s['nome']), 'l'), td(brl(s['gasto'], 0)), td(n0(s['leads'])), td(n0(s['vendas'])), td(pc(s['taxa'] * 100)), td(brl(cpl.get(s['nome']))), td(f"<b>{brl(s['custo_venda'], 0)}</b>")]))
            tl += s['leads']; tv += s['vendas']; tg += s['gasto'] or 0
        rows.append(row([td('Total', 'l'), td(brl(tg, 0)), td(n0(tl)), td(n0(tv)), td(pc(tv / tl * 100 if tl else None)), td(brl(self.k['cpl'])), td(f"<b>{brl(tg / tv if tv else None, 0)}</b>")], 'tot'))
        t1 = tab(['Campanha', 'Gasto estimado na janela', 'Leads (sem repetidos)', 'Vendas', 'Vendas/lead', 'CPL (Ads)', 'Custo por venda est.'], rows)
        ag = [row([td(E(a['grupo']), 'l'), td(E(a['anuncio'])), td(n0(a['leads'])), td(n0(a['vendas'])), td(pc(a['taxa'] * 100))]) for a in seg['anuncio_por_grupo']]
        t2 = tab(['Grupo', 'Anúncio', 'Leads', 'Vendas', 'Vendas/lead'], ag, 'mini')
        st = [row([td(E(s['nome']), 'l'), td(n0(s['leads'])), td(n0(s['vendas'])), td(pc(s['taxa'] * 100))]) for s in seg.get('status_planilha', [])]
        t3 = tab(['Status na planilha', 'Leads', 'Vendas', 'Vendas/lead'], st, 'mini')
        c = v['crm']
        auto = [f"Cruzamento por telefone, ignorando a data: <b>{n0(c['vendas_achadas'])} das {n0(c['vendas'])} vendas</b> ({pc((c['taxa_cruzamento'] or 0) * 100, 0)}) casaram com a planilha de leads. A tabela usa os leads de {v['janela']['inicio'][8:]}/{v['janela']['inicio'][5:7]} a {v['janela']['fim'][8:]}/{v['janela']['fim'][5:7]}, sem repetidos por telefone ({n0(v['leads']['unicos'])} telefones); {n0(v['leads']['sem_registro_crm'])} não aparecem no relatório do CRM."]
        itens = auto + [self.t(b) for b in P.get('vendas_bullets', [])]
        return (f'<div class="card"><h3>{E(self.p.get("titulo_lead_venda", "Do lead à venda (planilha de leads cruzada com o CRM por telefone)"))}</h3>{t1}'
                f'<div class="cols" style="margin-top:12px"><div>{t2}</div><div>{t3}</div></div>{bullets(itens)}'
                f'<p class="note">Método: venda = telefone no relatório do CRM com o estado "venda" do config. Gasto por campanha na janela é estimado quando o export do Ads cobre mais dias (fração {v.get("fracao_gasto", 1):.3f}). '
                f'A planilha costuma guardar a palavra-chave (utm_term), não a pesquisa do usuário. Taxas com poucas vendas são indicativas.</p></div>')

    # ---------------------------------------------------------------- termos
    def termos(self):
        if not self.d.get('temas'):
            return ''
        P = self.p.get('termos', {})
        tm = self.d['termos']
        rows = []
        desc = P.get('exemplos_tema', {})
        for r in self.d['temas']:
            rows.append(row([td(f'{E(r["tema"])}<small>{E(desc.get(r["tema"], ""))}</small>', 'l seg'), td(n0(r['termos'])), td(n0(r['cliques'])), td(brl(r['custo'])), td(pc(r['pct'])),
                             td(brl(r['cpc'])), td(pc(r['cvr'])), td(n1(r['conv'])), td(f"<b>{brl(r['cpl'])}</b>")]))
        tc = sum(r['custo'] for r in self.d['temas']); tcl = sum(r['cliques'] for r in self.d['temas']); tcv = sum(r['conv'] for r in self.d['temas'])
        rows.append(row([td('Total dos termos visíveis', 'l'), td(n0(sum(r['termos'] for r in self.d['temas']))), td(n0(tcl)), td(brl(tc)), td('100%'), td(brl(tc / tcl if tcl else None)),
                         td(pc(tcv / tcl * 100 if tcl else None)), td(n1(tcv)), td(f"<b>{brl(tc / tcv if tcv else None)}</b>")], 'tot'))
        out = [f'<section id="termos"><h2>Termos de pesquisa</h2><p class="lead">Classificados por intenção. Cobrem {brl(tm["visivel"], 0)} dos {brl(tm["total"], 0)} gastos: {brl(tm["total"] - tm["visivel"], 0)} ({pc(100 - tm["pct_visivel"], 0)}) estão em termos que o Google oculta por baixo volume.</p>',
               '<div class="card">' + tab(['Tema da busca', 'Termos', 'Cliques', 'Custo', '% custo', 'CPC', 'Conv./clique', 'Conv.', 'CPL'], rows) + bullets([self.t(b) for b in P.get('bullets', [])]) + '</div>']
        if self.d.get('locais'):
            mapa = P.get('mapa_cidades', {})
            seg = {s['nome']: s for s in (self.v['segmentos']['cidade'] if self.v else [])}
            tem_v = bool(self.v and mapa)
            head = ['Cidade citada no termo', 'Custo', 'Conv.', 'CPL'] + (['Leads na planilha', 'Vendas (% dos leads)', 'Custo por venda est.'] if tem_v else []) + (['Observação do CRM'] if P.get('obs_cidades') else [])
            lr = []
            for c in self.d['locais']:
                r = [td(E(c['nome']), 'l'), td(brl(c['custo'])), td(n1(c['conv'])), td(brl(c['cpl']))]
                if tem_v:
                    s = seg.get(mapa.get(c['nome'], ''), None)
                    cps = (c['cpl'] / s['taxa']) if s and s['taxa'] and c['cpl'] else None
                    r += [td(n0(s['leads']) if s else '-'), td(f"{s['vendas']} ({pc(s['taxa'] * 100, 0)})" if s else '-'), td(brl(cps, 0))]
                if P.get('obs_cidades'):
                    r.append(td(E(P['obs_cidades'].get(c['nome'], '-'))))
                lr.append(row(r))
            out.append(f'<div class="card"><h3>{E(P.get("titulo_cidades", "Por cidade: do termo à venda"))}</h3>{tab(head, lr)}'
                       f'<p class="note">{self.t(P.get("nota_cidades", "A cidade vem do texto da busca, que é só uma aproximação da cidade do lead."))}</p>'
                       + ''.join(call(c.get('tipo', ''), self.t(c.get('titulo', '')), self.t(c.get('texto', ''))) for c in P.get('callouts_cidades', [])) + '</div>')
        out.append('</section>')
        self.secoes.append(('termos', 'Termos'))
        return ''.join(out)

    # ---------------------------------------------------------------- negativas
    def negativas(self):
        if not self.d.get('negativas'):
            return ''
        N = self.d['negativas']
        P = self.p.get('negativas', {})
        cen = N['cenarios']
        lead = (f"Divididas por risco. Efeito combinado no CPL dos termos visíveis: Tier 1 {pc(cen['tier1']['var_pct'])}; Tier 1 + concorrentes {pc(cen['tier1_mais_concorrentes']['var_pct'])}.")

        def cartao(c):
            cj = N['conjuntos'].get(c['conjunto'], {})
            rows = [row([td(E(x['termo']), 'l'), td(n0(x['cliques'])), td(brl(x['custo'])), td(n1(x['conv']))]) for x in cj.get('top', [])[:c.get('max', 12)]]
            tags = ''.join(f'<span class="tag">{E(x)}</span>' for x in c.get('tags', []))
            nota = f'<p class="note">{self.t(c.get("nota", ""))}{(" Negativas de frase: " + tags) if tags else ""}</p>'
            return (f'<div class="card"><h3>{E(c.get("titulo", c["conjunto"]))} ({brl(cj.get("custo"))} · {n1(cj.get("conv"))} conv.)</h3>'
                    f'{tab(["Termo", "Cliques", "Custo", "Conv."], rows, "mini")}{nota}</div>')
        cartoes = P.get('cartoes') or [
            {'conjunto': 'suporte', 'tier': 1, 'titulo': 'Marca + suporte'}, {'conjunto': 'concorrente_contato', 'tier': 1, 'titulo': 'Concorrente + contato'},
            {'conjunto': 'fora_area', 'tier': 1, 'titulo': 'Fora da área'}, {'conjunto': 'concorrente', 'tier': 2, 'titulo': 'Nomes de concorrentes'}]
        out = [f'<section id="neg"><h2>Negativas</h2><p class="lead">{lead}</p>']
        for tier, titulo, tipo, txt in [(1, 'Tier 1: aplicar já.', '', P.get('texto_tier1', 'Baixo risco, sem conversões relevantes sendo perdidas.')),
                                        (2, 'Tier 2: aplicar depois de olhar as vendas no CRM.', 'warn', P.get('texto_tier2', 'Há conversões nesses termos: confirmar que não viram venda antes de negativar.'))]:
            cs = [c for c in cartoes if c.get('tier', 1) == tier]
            if cs:
                out.append(call(tipo, titulo, self.t(txt)) + '<div class="cols">' + ''.join(cartao(c) for c in cs) + '</div>')
        if P.get('onde'):
            out.append('<div class="card"><h3>Onde cadastrar</h3>' + bullets([self.t(x) for x in P['onde']]) + '</div>')
        out.append('</section>')
        self.secoes.append(('neg', 'Negativas'))
        return ''.join(out)

    # ---------------------------------------------------------------- palavras-chave atuais
    def palavras(self):
        if not self.d.get('palavras'):
            return ''
        P = self.p.get('palavras_chave', {})
        dec = P.get('decisoes', {})
        rs = self.d['palavras_resumo']
        tem_v = bool(self.v)
        head = ['Palavra-chave', 'Custo', 'Cliques', 'Conv.', 'CPL'] + (['Leads→venda', 'Custo/venda est.'] if tem_v else []) + ['IQ', 'Decisão', 'Porquê']
        rows = []
        for k in self.d['palavras']:
            d = dec.get(k['nome'], dec.get(k['nome'].lower(), {'decisao': 'Revisar', 'cor': 'warn', 'porque': ''}))
            r = [td(f'{E(k["nome"])}<small>{E(k["campanha"])} · {E(k["grupo"])} · {E(k["correspondencia"])}</small>', 'l seg'), td(brl(k['custo'])), td(n0(k['cliques'])), td(n1(k['conv'])), td(brl(k.get('cpl')))]
            if tem_v:
                s = self.venda_palavra(k['nome'])
                if s and s['leads'] >= P.get('minimo_leads', 15):
                    r += [td(f"{s['vendas']} de {s['leads']} ({pc(s['taxa'] * 100, 0)})"), td(brl(s['custo_venda'], 0))]
                else:
                    r += [td('-'), td('-')]
            r += [td('-' if k.get('iq') is None else n0(k['iq'])), td(f'<span class="st {d.get("cor", "warn")}">{E(d["decisao"])}</span>'), td(self.t(E(d.get('porque', ''))) if '{{' not in d.get('porque', '') else self.t(d['porque']), 'l txt')]
            rows.append(row(r))
        self.secoes.append(('kw', 'Palavras-chave'))
        return (f'<section id="kw"><h2>Palavras-chave</h2><p class="lead">A conta tem {rs["total"]} palavras-chave, {rs["amplas"]} em correspondência ampla; {rs["com_custo"]} tiveram custo no período.</p>'
                f'<div class="card">{tab(head, rows, left=(len(head) - 1,))}<p class="note">{self.t(P.get("nota", ""))}</p></div></section>')

    # ---------------------------------------------------------------- novas palavras (Semrush)
    def tag_kw(self, kwd):
        n = norm(kwd)
        s = self.sem_idx.get(n)
        vol = int(s['vol']) if s and s.get('vol') is not None else None
        ja = (n in self.termos_ativos) or (n in self.nomes_kw)
        txt = f'[{kwd}] "{kwd}"' if (vol or 0) >= 100 else f'"{kwd}"'
        return f'<span class="tag{"" if ja else " new"}">{E(txt)} <b>{"n/d" if vol is None else n0(vol)}</b></span>', ja, vol

    def tabela_semrush(self, lista):
        rows = []
        for kwd in lista:
            n = norm(kwd)
            s = self.sem_idx.get(n)
            if not s:
                continue
            at = self.termos_ativos.get(n)
            ja = f"Sim: {at['cliques']} {'clique' if at['cliques'] == 1 else 'cliques'}, {brl(at['custo'])}, {n1(at['conv'])} conv." if at else 'Não'
            vol = int(s['vol'] or 0)
            rows.append(row([td(E(kwd), 'l'), td(n0(vol)), td(f"{s['cpc']:.2f}".replace('.', ',') if s.get('cpc') else '-'), td(f"{s['co']:.2f}".replace('.', ',') if s.get('co') is not None else '-'),
                             td('-' if not s.get('kd') else n0(s['kd'])), td(s.get('intencao', '-')), td(ja, 'l txt'), td('Exata + frase' if vol >= 100 else 'Frase')]))
        return tab(['Palavra-chave', 'Volume/mês (BR)', 'CPC ref.', 'Concorrência', 'Dificuldade', 'Intenção', 'Na conta no período?', 'Correspondência'], rows, left=(5, 6))

    def novas(self):
        P = self.p.get('novas_palavras')
        if not P or not self.sem:
            return ''
        gr = P.get('grupos', [])

        def soma(g):
            return sum(int(self.sem_idx[norm(k)]['vol'] or 0) for k in g['palavras'] if norm(k) in self.sem_idx)
        kp = ''.join(f'<div class="kpi{" hi" if i == 0 else ""}"><div class="l">{E(g["titulo_kpi"])}</div><div class="v">≈ {n0(round(soma(g), -1 if soma(g) < 2000 else -2))}</div><div class="s">{E(g.get("sub_kpi", ""))}</div></div>' for i, g in enumerate(gr) if g.get('titulo_kpi'))
        out = [f'<section id="novas"><h2>Palavras-chave novas (Semrush)</h2><p class="lead">{self.t(P.get("intro", ""))}</p>', f'<div class="kpis">{kp}</div>' if kp else '']
        for c in P.get('callouts', []):
            out.append(call(c.get('tipo', ''), self.t(c.get('titulo', '')), self.t(c.get('texto', ''))))
        for g in gr:
            out.append(f'<div class="card"><h3>{E(g["titulo"])}</h3>{self.tabela_semrush(g["palavras"])}<p class="note">{self.t(g.get("nota", ""))}</p></div>')
        out.append('</section>')
        self.secoes.append(('novas', 'Novas palavras'))
        return ''.join(out)

    # ---------------------------------------------------------------- estrutura
    def estrutura(self):
        P = self.p.get('estrutura')
        if not P:
            return ''
        camps = P['campanhas']
        rows = [row([td(E(c['nome']), 'l'), td(self.t(c.get('objetivo', '')), 'l txt'), td(self.t(c.get('resumo_grupos', '')), 'l txt'), td(self.t(c.get('correspondencia', '')), 'l'), td(E(c.get('orcamento_dia', '')))]) for c in camps]
        t1 = tab(['Campanha', 'Objetivo', 'Grupos e palavras-chave', 'Correspondência', 'Orçamento/dia'], rows, left=(1, 2, 3))
        out = [f'<section id="estr"><h2>Estrutura recomendada</h2><p class="lead">{self.t(P.get("lead", "Orçamento total mantido no teste, para o CPL ser comparável. Valores são ponto de partida."))}</p><div class="card">{t1}{bullets([self.t(b) for b in P.get("bullets", [])])}</div>']
        # lista de palavras por campanha/grupo
        linhas = []
        for c in camps:
            if not c.get('grupos'):
                continue
            linhas.append(f'<tr class="grp"><td colspan="3">{E(c["nome"])} · {E(c.get("orcamento_dia", ""))}</td></tr>')
            for g in c['grupos']:
                tags = [self.tag_kw(k) for k in g['palavras']]
                novos = sum(1 for _, ja, _ in tags if not ja)
                linhas.append(f'<tr><td class="l seg">{E(g["nome"])}<small>{len(tags)} palavras-chave, {novos} novas</small></td><td class="kws">{"".join(t for t, _, _ in tags)}</td><td class="l txt">{self.t(g.get("obs", ""))}</td></tr>')
        if linhas:
            out.append('<div class="card"><h3>Palavras-chave recomendadas por campanha e grupo</h3>'
                       '<p class="note" style="margin:0 0 10px">[colchetes] = exata · "aspas" = frase · número = buscas por mês no Brasil (Semrush). <span class="tag new">verde</span> = não apareceu na conta no período · <span class="tag">cinza</span> = já na conta.</p>'
                       f'<div class="wrap"><table class="kwt"><thead><tr><th class="l">Grupo</th><th class="l">Palavras-chave</th><th class="l">Observação</th></tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'
                       + bullets([self.t(b) for b in P.get('regras_palavras', [])]) + '</div>')
        # de onde sai cada grupo atual
        if self.d.get('grupos') and P.get('destinos'):
            gr = []
            for g in self.d['grupos']:
                d = P['destinos'].get(g['nome'])
                if not d:
                    continue
                gr.append(row([td(f'{E(g["nome"])}<small>{E(g["campanha"])}</small>', 'l seg'), td(brl(g['custo'])), td(pc(g['custo'] / self.k['custo'] * 100)), td(n1(g['conv'])), td(brl(g['cpl'])), td(brl(g['cpc'])),
                               td(f'<span class="st {d.get("cor", "warn")}">{E(d["destino"])}</span>'), td(self.t(d.get('porque', '')), 'l txt')]))
            if gr:
                out.append('<div class="card"><h3>De onde sai cada grupo atual</h3>' + tab(['Grupo atual', 'Custo', '% da conta', 'Conv.', 'CPL', 'CPC', 'Destino', 'Porquê'], gr, left=(7,)) + '</div>')
        out.append('</section>')
        self.secoes.append(('estr', 'Estrutura'))
        return ''.join(out)

    # ---------------------------------------------------------------- checagens, plano, limites
    def checagens(self):
        itens = [self.t(x) for x in self.p.get('checagens', [])]
        if not itens:
            return ''
        self.secoes.append(('checks', 'Checagens'))
        return f'<section id="checks"><h2>Checagens antes de mexer</h2><p class="lead">{self.t(self.p.get("lead_checagens", "Itens que podem explicar o resultado fora da estrutura da conta."))}</p><div class="card"><ol>' + ''.join(f'<li>{i}</li>' for i in itens) + '</ol></div></section>'

    def plano_teste(self):
        P = self.p.get('plano_teste')
        if not P:
            return ''
        et = ''.join(f'<div class="card"><div class="d">{E(e["data"])}</div><h3>{E(e["titulo"])}</h3>{bullets([self.t(i) for i in e.get("itens", [])])}</div>' for e in P.get('etapas', []))
        mt = [row([td(self.t(m['indicador']), 'l'), td(self.t(m.get('hoje', ''))), td(self.t(m.get('meta', '')), 'l'), td(self.t(m.get('trava', '')), 'l')]) for m in P.get('metas', [])]
        self.secoes.append(('plano', 'Plano de teste'))
        return (f'<section id="plano"><h2>Plano de teste</h2><p class="lead">{self.t(P.get("lead", "Medir pelo CPL e pelo custo por venda juntos, para não cortar o que vende."))}</p><div class="tl">{et}</div>'
                f'<div class="card" style="margin-top:14px"><h3>Metas e travas</h3>{tab(["Indicador", "Hoje", "Meta", "Trava"], mt, left=(2, 3))}<p class="note">{self.t(P.get("nota", "As metas são hipóteses calculadas a partir do cenário de cada alavanca, não promessas."))}</p></div></section>')

    def limites(self):
        itens = []
        if self.d.get('termos'):
            itens.append(f"Os termos de pesquisa visíveis cobrem {pc(self.d['termos']['pct_visivel'], 0)} do gasto; o Google oculta o resto.")
        if self.v:
            q = self.v['qualidade']
            itens.append(f"Planilha de leads: {n0(q['linhas'])} linhas lidas, {n0(q['sem_data'])} sem data interpretável e {n0(q['sem_telefone'])} sem telefone válido. Vendas casadas por telefone: {n0(self.v['crm']['vendas_achadas'])} de {n0(self.v['crm']['vendas'])}.")
        itens += [self.t(x) for x in self.p.get('limites', [])]
        self.secoes.append(('limites', 'Limites'))
        return f'<section id="limites"><h2>Dados e limites</h2><div class="card">{bullets(itens)}</div></section>'

    # ---------------------------------------------------------------- página
    def montar(self):
        cab = self.p.get('cabecalho', {})
        corpo = [self.resumo(), self.diagnostico(), self.termos(), self.negativas(), self.palavras(), self.novas(), self.estrutura(), self.checagens(), self.plano_teste(), self.limites()]
        nav = ''.join(f'<a href="#{i}">{E(r)}</a>' for i, r in self.secoes)
        logos = ''
        if cab.get('logo_cliente') or cab.get('logo_agencia'):
            logos = '<div class="brand">' + (f'<img class="cl" src="{E(cab["logo_cliente"])}" alt="{E(self.d["meta"]["cliente"])}">' if cab.get('logo_cliente') else '<span></span>') \
                    + (f'<img class="co" src="{E(cab["logo_agencia"])}" alt="Logo da agência">' if cab.get('logo_agencia') else '') + '</div>'
        voltar = f'<a class="back" href="{E(cab["voltar"])}">← Todos os materiais</a>' if cab.get('voltar') else ''
        titulo = cab.get('titulo', 'Plano para reduzir o CPL do Google Ads')
        sub = self.t(cab.get('subtitulo', f"{self.d['meta']['cliente']} · base: Google Ads de {self.d['meta']['periodo']} · documento interno"))
        fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">'
        doc = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="color-scheme" content="light">'
               f'<title>{E(cab.get("titulo_aba", "Plano Google Ads " + self.d["meta"]["cliente"]))}</title>{fonts}<style>{CSS}</style></head><body><div class="bar"></div>'
               f'<div class="top">{voltar}{logos}<h1>{E(titulo)}</h1><p class="sub">{sub}</p></div><div class="nav"><div class="in">{nav}</div></div><main>{"".join(corpo)}</main>'
               f'<footer>{E(cab.get("rodape", "Análise de mídia paga"))} · {E(self.d["meta"]["cliente"])} · {E(self.p.get("data", self.d["meta"]["gerado_em"]))}</footer></body></html>')
        return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dados', required=True)
    ap.add_argument('--plano', required=True)
    ap.add_argument('--semrush')
    ap.add_argument('--saida', required=True)
    a = ap.parse_args()
    dados = json.load(open(a.dados, encoding='utf-8'))
    plano = json.load(open(a.plano, encoding='utf-8'))
    sem = json.load(open(a.semrush, encoding='utf-8')) if a.semrush else []
    pg = Pagina(dados, plano, sem)
    doc = pg.montar()
    os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
    open(a.saida, 'w', encoding='utf-8').write(doc)
    print('ok ->', a.saida, f'({len(doc):,} bytes) | seções:', ', '.join(i for i, _ in pg.secoes))
    if pg.T.faltando:
        print('ATENÇÃO: caminhos do template não encontrados em dados.json:')
        for f in sorted(set(pg.T.faltando)):
            print('  -', f)
        sys.exit(2)


if __name__ == '__main__':
    main()
