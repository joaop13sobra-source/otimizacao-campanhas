#!/usr/bin/env python3
"""Analisa uma conta de Google Ads (Search) e grava dados.json para o gerar_plano.py.

    python3 -I analise.py config.json [--saida dados.json]

Entradas: os relatórios do Google Ads (campanhas, grupos, palavras-chave, termos de pesquisa) e,
opcionalmente, o bloco "vendas" do config (planilha de leads x relatório do CRM, ver cruzar_vendas.py).
Tudo que sai daqui é calculado; a narrativa (decisões, estrutura) é escrita depois, em plano.json.
"""
import json
import math
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

import cruzar_vendas
from gads import norm, numerica, pick, read_report

# regras de texto que valem para qualquer provedor/negócio; o config pode sobrescrever
PADRAO = {
    'suporte': r'suporte|2 ?via|segunda via|boleto|desbloqueio|fatura|pix|login|area do cliente|\bapp\b|central|cliente',
    'contato': r'whatsapp|telefone|numero|contato|0800',
    'contato_concorrente': r'whatsapp|telefone|numero|contato|central|atendimento|cobertura',
}
TEMAS = ['Marca pura', 'Marca + suporte/cliente', 'Marca + contato (WhatsApp/telefone)', 'Marca + cidade/bairro',
         'Concorrentes / outras operadoras', 'Genérico + cidade/bairro', 'Genérico sem cidade / outros']


def limpar(nome):
    """'[PREFIXO][SEARCH] Institucional' -> 'Institucional'."""
    return re.sub(r'^(\[[^\]]*\]\s*)+', '', str(nome)).strip()


def _rx(cfg, chave, padrao=''):
    v = cfg.get('regex', {}).get(chave, padrao)
    return v or ''


def _tem(rx, n):
    return bool(rx) and re.search(rx, n) is not None


# --------------------------------------------------------------------------- campanhas / grupos
def tabela_campanhas(df):
    c = pd.DataFrame({
        'nome': df[pick(df, 'Campanha')].map(limpar),
        'status': df[pick(df, 'Status da campanha')] if pick(df, 'Status da campanha') else '',
        'motivos': (df[pick(df, 'Motivos do status')] if pick(df, 'Motivos do status') else '').astype(str),
        'orcamento': numerica(df, 'Orçamento'),
        'custo': numerica(df, 'Custo'),
        'cliques': numerica(df, 'Cliques', 'Interações'),
        'impr': numerica(df, 'Impr.'),
        'conv': numerica(df, 'Conversões'),
        'parcela': numerica(df, 'Parcela impr rede de pesquisa', 'Parcela de impr. da rede de pesquisa',
                            'Parcela de impressões da Rede de Pesquisa'),
        'perd_orc': numerica(df, 'Parc impr perd rede de pesquisa (orç)', 'Parc impr perd rede de pesquisa (orç.)',
                             'Parcela de impr. perdida da rede de pesquisa (orçamento)'),
        'perd_class': numerica(df, 'Parc impr perd rede de pesquisa (class.)',
                               'Parcela de impr. perdida da rede de pesquisa (classificação)'),
    })
    c = c[c.status.isin(['Ativada', 'Pausada', 'Ativado', 'Pausado', '']) | (c.custo > 0)].copy()
    c['cpc'] = c.custo / c.cliques.replace(0, np.nan)
    c['cvr'] = c.conv / c.cliques.replace(0, np.nan) * 100
    c['cpl'] = c.custo / c.conv.replace(0, np.nan)
    return c.reset_index(drop=True)


def tabela_grupos(df):
    g = pd.DataFrame({
        'nome': df[pick(df, 'Grupo de anúncios')],
        'campanha': df[pick(df, 'Campanha')].map(limpar),
        'status': df[pick(df, 'Status do grupo de anúncios')] if pick(df, 'Status do grupo de anúncios') else '',
        'custo': numerica(df, 'Custo'),
        'cliques': numerica(df, 'Cliques', 'Interações'),
        'impr': numerica(df, 'Impr.'),
        'conv': numerica(df, 'Conversões'),
    })
    g = g[g.custo > 0].copy()
    g['cpc'] = g.custo / g.cliques.replace(0, np.nan)
    g['cvr'] = g.conv / g.cliques.replace(0, np.nan) * 100
    g['cpl'] = g.custo / g.conv.replace(0, np.nan)
    return g.reset_index(drop=True)


def tabela_palavras(df):
    k = pd.DataFrame({
        'nome': df[pick(df, 'Palavra-chave')],
        'status': df[pick(df, 'Status da palavra-chave')] if pick(df, 'Status da palavra-chave') else '',
        'correspondencia': df[pick(df, 'Tipo de corresp.')].str.replace('Correspondência ', '', regex=False),
        'campanha': df[pick(df, 'Campanha')].map(limpar),
        'grupo': df[pick(df, 'Grupo de anúncios')],
        'custo': numerica(df, 'Custo'),
        'cliques': numerica(df, 'Cliques', 'Interações'),
        'impr': numerica(df, 'Impr.'),
        'conv': numerica(df, 'Conversões'),
        'iq': numerica(df, 'Índice de qualidade'),
    })
    k['cpl'] = k.custo / k.conv.replace(0, np.nan)
    k['cpc'] = k.custo / k.cliques.replace(0, np.nan)
    k['n'] = k.nome.map(norm)
    return k


# --------------------------------------------------------------------------- termos de pesquisa
def classificar_termo(n, cfg):
    marca, conc = _rx(cfg, 'marca'), _rx(cfg, 'concorrentes')
    sup, con = _rx(cfg, 'suporte', PADRAO['suporte']), _rx(cfg, 'contato', PADRAO['contato'])
    locais = '|'.join(x for x in list(cfg.get('regex', {}).get('cidades', {}).values()) + [_rx(cfg, 'fora_area'), _rx(cfg, 'locais_extra')] if x)
    if _tem(marca, n):
        if _tem(sup, n):
            return TEMAS[1]
        if _tem(con, n):
            return TEMAS[2]
        if _tem(locais, n):
            return TEMAS[3]
        return TEMAS[0]
    if _tem(conc, n):
        return TEMAS[4]
    if _tem(locais, n):
        return TEMAS[5]
    return TEMAS[6]


def tabela_termos(df, cfg):
    t = pd.DataFrame({
        'termo': df[pick(df, 'Termo de pesquisa')],
        'campanha': df[pick(df, 'Campanha')].map(limpar),
        'grupo': df[pick(df, 'Grupo de anúncios')],
        'cliques': numerica(df, 'Cliques'),
        'impr': numerica(df, 'Impr.'),
        'custo': numerica(df, 'Custo'),
        'conv': numerica(df, 'Conversões'),
    })
    t['n'] = t.termo.map(norm)
    t['tema'] = t.n.map(lambda x: classificar_termo(x, cfg))
    return t


def _resumo(df, total_custo):
    g = df.groupby('tema').agg(termos=('n', 'nunique'), cliques=('cliques', 'sum'), custo=('custo', 'sum'), conv=('conv', 'sum'))
    g = g.reindex([x for x in TEMAS if x in g.index])
    g['pct'] = g.custo / total_custo * 100
    g['cpc'] = g.custo / g.cliques.replace(0, np.nan)
    g['cvr'] = g.conv / g.cliques.replace(0, np.nan) * 100
    g['cpl'] = g.custo / g.conv.replace(0, np.nan)
    return g


def _top_termos(df, mask, n=14):
    x = df[mask].groupby('termo').agg(cliques=('cliques', 'sum'), custo=('custo', 'sum'), conv=('conv', 'sum'))
    x = x[x.custo > 0].sort_values('custo', ascending=False).head(n)
    return [dict(termo=i, cliques=int(r.cliques), custo=round(r.custo, 2), conv=round(r.conv, 1)) for i, r in x.iterrows()]


def negativas(t, cfg):
    marca = _rx(cfg, 'marca')
    sup, conc = _rx(cfg, 'suporte', PADRAO['suporte']), _rx(cfg, 'concorrentes')
    con_c, fora = _rx(cfg, 'contato_concorrente', PADRAO['contato_concorrente']), _rx(cfg, 'fora_area')
    mm = t.n.map(lambda x: _tem(marca, x))
    conjuntos = {
        'suporte': mm & t.n.map(lambda x: _tem(sup, x)),
        'concorrente_contato': ~mm & t.n.map(lambda x: _tem(conc, x) and _tem(con_c, x)),
        'concorrente': ~mm & t.n.map(lambda x: _tem(conc, x) and not _tem(con_c, x)),
        'fora_area': ~mm & t.n.map(lambda x: _tem(fora, x)),
    }
    for nome, rx in cfg.get('negativas_extra', {}).items():
        conjuntos[nome] = t.n.map(lambda x, rx=rx: _tem(rx, x))
    T, C = t.custo.sum(), t.conv.sum()
    out = {}
    for nome, m in conjuntos.items():
        x = t[m]
        out[nome] = dict(custo=round(x.custo.sum(), 2), conv=round(x.conv.sum(), 1),
                         zero_conv=round(x[x.conv == 0].custo.sum(), 2),
                         termos_com_custo=int((x.custo > 0).sum()), top=_top_termos(t, m))

    def cenario(chaves):
        m = pd.Series(False, index=t.index)
        for k in chaves:
            m |= conjuntos[k]
        c, v = t[m].custo.sum(), t[m].conv.sum()
        novo = (T - c) / (C - v) if C - v > 0 else None
        return dict(remove_custo=round(c, 2), remove_conv=round(v, 1), cpl=None if novo is None else round(novo, 2),
                    var_pct=None if novo is None else round((novo / (T / C) - 1) * 100, 1))
    base = ['suporte', 'concorrente_contato', 'fora_area'] + list(cfg.get('negativas_extra', {}).keys())
    return dict(conjuntos=out, cenarios=dict(tier1=cenario(base), tier1_mais_concorrentes=cenario(base + ['concorrente'])),
                cpl_base=round(T / C, 2) if C else None)


def locais(t, cfg):
    cid = cfg.get('regex', {}).get('cidades', {})
    linhas = []
    for nome, rx in cid.items():
        m = t.n.map(lambda x: _tem(rx, x))
        c, v = t[m].custo.sum(), t[m].conv.sum()
        linhas.append(dict(nome=nome, custo=round(c, 2), conv=round(v, 1), cpl=round(c / v, 2) if v else None,
                           cliques=int(t[m].cliques.sum())))
    return linhas


# --------------------------------------------------------------------------- principal
def decompor(cur, ref):
    """CPL = CPC / (conv/clique). Divide a variação do CPL em parte de CPC e parte de conversão (log)."""
    cpl0, cpl1 = ref['custo'] / ref['conversoes'], cur['custo'] / cur['conversoes']
    cpc0, cpc1 = ref['custo'] / ref['cliques'], cur['custo'] / cur['cliques']
    cvr0, cvr1 = ref['conversoes'] / ref['cliques'], cur['conversoes'] / cur['cliques']
    tot = math.log(cpl1 / cpl0)
    if abs(tot) < 1e-9:
        return None
    return dict(cpl_ref=round(cpl0, 2), cpc_ref=round(cpc0, 2), cvr_ref=round(cvr0 * 100, 1),
                var_cpl_pct=round((cpl1 / cpl0 - 1) * 100, 1),
                parte_cpc_pct=round(math.log(cpc1 / cpc0) / tot * 100), parte_conversao_pct=round(-math.log(cvr1 / cvr0) / tot * 100))


def alertas(camp, kw, cobertura):
    def v1(x):
        return f'{x:.1f}'.replace('.', ',')
    a = []
    for _, r in camp.iterrows():
        if re.search('reprov', str(r.motivos), re.I):
            a.append(dict(tipo='bad', texto=f'Campanha "{r.nome}": o Google informa "{r.motivos.strip()}". Conferir o relatório de anúncios.'))
        if r.perd_orc == r.perd_orc and r.perd_orc >= 15:
            a.append(dict(tipo='warn', texto=f'Campanha "{r.nome}" perde {v1(r.perd_orc)}% das impressões por orçamento.'))
        if r.perd_class == r.perd_class and r.perd_class >= 25:
            a.append(dict(tipo='warn', texto=f'Campanha "{r.nome}" perde {v1(r.perd_class)}% das impressões por classificação (lance/qualidade).'))
    ativas = kw[kw.custo > 0]
    if len(ativas) and (ativas.correspondencia.str.lower() == 'ampla').all():
        a.append(dict(tipo='warn', texto=f'Todas as {len(ativas)} palavras-chave com gasto estão em correspondência ampla.'))
    peso = kw[(kw.iq == kw.iq) & (kw.iq <= 5) & (kw.custo >= 0.05 * max(kw.custo.sum(), 1))]
    for _, r in peso.iterrows():
        a.append(dict(tipo='warn', texto=f'Palavra-chave "{r.nome}" com índice de qualidade {int(r.iq)} e {r.custo / kw.custo.sum() * 100:.0f}% do gasto.'))
    if cobertura < 85:
        a.append(dict(tipo='info', texto=f'Os termos de pesquisa visíveis cobrem {cobertura:.0f}% do gasto; o Google oculta o resto.'))
    return a


def rodar(cfg):
    G = cfg['gads']
    camp_df, per_c = read_report(G['campanhas'])
    camp = tabela_campanhas(camp_df)
    grp = tabela_grupos(read_report(G['grupos'])[0]) if G.get('grupos') else pd.DataFrame()
    kw = tabela_palavras(read_report(G['palavras_chave'])[0]) if G.get('palavras_chave') else pd.DataFrame()
    t = tabela_termos(read_report(G['termos'])[0], cfg) if G.get('termos') else pd.DataFrame()

    custo = cfg.get('custo_total_conta') or round(camp.custo.sum(), 2)
    cliques, conv = camp.cliques.sum(), camp.conv.sum()
    kpis = dict(custo=round(custo, 2), cliques=int(cliques), conversoes=round(conv, 1), cpl=round(custo / conv, 2),
                cpc=round(custo / cliques, 2), cvr=round(conv / cliques * 100, 1))
    ref = cfg.get('referencia')
    decomp = decompor(dict(custo=custo, cliques=cliques, conversoes=conv), ref) if ref else None

    out = dict(meta=dict(cliente=cfg['cliente'], periodo=cfg['periodo']['rotulo'], gerado_em=date.today().isoformat(),
                         arquivos=G), kpis=kpis, referencia=ref, decomposicao=decomp)
    out['campanhas'] = json.loads(camp.to_json(orient='records'))
    out['grupos'] = json.loads(grp.to_json(orient='records')) if len(grp) else []

    cobertura = 100.0
    if len(t):
        vis = t.custo.sum()
        cobertura = vis / custo * 100
        out['termos'] = dict(visivel=round(vis, 2), total=round(custo, 2), pct_visivel=round(cobertura, 1),
                             conv_visivel=round(t.conv.sum(), 1), cpl_visivel=round(vis / t.conv.sum(), 2) if t.conv.sum() else None,
                             clicados=int((t.cliques > 0).sum()))
        res = _resumo(t, vis)
        out['temas'] = [dict(tema=k, **{c: (None if v != v else round(float(v), 2)) for c, v in r.items()}) for k, r in res.iterrows()]
        marca_camp = cfg.get('campanha_marca')
        if marca_camp:
            fora = t[(t.campanha != marca_camp) & t.tema.str.startswith('Marca')]
            outra = t[t.campanha != marca_camp]
            out['marca_fora_da_campanha_de_marca'] = dict(
                campanha_nao_marca=sorted(set(outra.campanha)), custo=round(fora.custo.sum(), 2),
                pct_da_campanha=round(fora.custo.sum() / outra.custo.sum() * 100, 1) if outra.custo.sum() else None,
                conv=round(fora.conv.sum(), 1), cpl=round(fora.custo.sum() / fora.conv.sum(), 2) if fora.conv.sum() else None)
        out['negativas'] = negativas(t, cfg)
        out['locais'] = locais(t, cfg)
        concorr = t[t.tema == TEMAS[4]]
        out['concorrentes'] = dict(com_clique=int(concorr[concorr.cliques > 0].n.nunique()),
                                   sem_conversao=int(concorr[(concorr.cliques > 0) & (concorr.conv == 0)].n.nunique()))
    if len(kw):
        ativ = kw[kw.custo > 0].sort_values('custo', ascending=False)
        out['palavras'] = json.loads(ativ.to_json(orient='records'))
        out['palavras_resumo'] = dict(total=int(len(kw)), com_custo=int(len(ativ)), pausadas=int((kw.status.str.lower() == 'pausado').sum()),
                                      amplas=int((kw.correspondencia.str.lower() == 'ampla').sum()))
    # listas compactas (sem dado pessoal) para o gerador marcar "novo" x "já na conta"
    if len(t):
        ta = t.groupby('n').agg(cliques=('cliques', 'sum'), custo=('custo', 'sum'), conv=('conv', 'sum'))
        ta = ta[(ta.cliques > 0) | (ta.custo > 0)]
        out['termos_ativos'] = {i: dict(cliques=int(r.cliques), custo=round(r.custo, 2), conv=round(r.conv, 1)) for i, r in ta.iterrows()}
    if len(kw):
        out['palavras_nomes'] = sorted(set(kw.n))
    out['alertas'] = alertas(camp, kw if len(kw) else pd.DataFrame(columns=['correspondencia', 'custo', 'iq', 'nome']), cobertura)

    # ---- vendas (opcional)
    if cfg.get('vendas'):
        V = cfg['vendas']
        frac = V.get('fracao_gasto')
        if frac is None and V.get('gasto_janela_total'):
            frac = V['gasto_janela_total'] / custo
        frac = frac or 1.0
        gc = {r.nome: r.custo * frac for _, r in camp.iterrows() if r.custo > 0}
        gg = {}
        for _, r in grp.iterrows():
            gg[r.nome] = gg.get(r.nome, 0) + r.custo * frac
        gp = {}
        for _, r in kw.iterrows():
            if r.custo > 0:
                gp[r.n] = gp.get(r.n, 0) + r.custo * frac
        v = cruzar_vendas.rodar(V, dict(gasto_campanha=gc, gasto_grupo=gg, gasto_palavra=gp))
        v['fracao_gasto'] = round(frac, 4)
        out['vendas'] = v
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    saida = sys.argv[sys.argv.index('--saida') + 1] if '--saida' in sys.argv else 'dados.json'
    d = rodar(cfg)
    json.dump(d, open(saida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    k = d['kpis']
    print('ok ->', saida)
    print(f"custo {k['custo']} | conv {k['conversoes']} | CPL {k['cpl']} | CPC {k['cpc']} | conv/clique {k['cvr']}%")
    if d.get('decomposicao'):
        print('decomposição:', d['decomposicao'])
    if d.get('negativas'):
        print('cenários de negativas:', d['negativas']['cenarios'])
    if d.get('vendas'):
        v = d['vendas']
        print('vendas:', v['leads']['estados'], '| achadas', f"{v['crm']['vendas_achadas']}/{v['crm']['vendas']}")
    for a in d['alertas']:
        print(' -', a['tipo'], a['texto'])
