#!/usr/bin/env python3
"""Cruza a planilha de leads com o relatório de vendas do CRM por telefone.

Responde: de onde vieram as vendas (campanha, grupo, anúncio, palavra-chave, cidade) e quanto
custa cada venda. Chamado por analise.py (bloco "vendas" do config) ou direto:

    python3 -I cruzar_vendas.py config.json [--saida vendas.json]

Regras que não podem ser quebradas (aprendidas em um caso real, ver references/armadilhas.md):
  * a data da planilha pode ter MAIS DE UM formato; o script tenta todos e acusa linhas sem data.
  * o telefone casa ignorando a data (chave = DDD + últimos 8 dígitos).
  * o campo utm_term costuma trazer a PALAVRA-CHAVE e não a pesquisa do usuário.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from gads import norm


# ---------------------------------------------------------------- leitura
def chave_telefone(x):
    """DDD + últimos 8 dígitos (ignora o 9 extra, 55 e zero à esquerda). '' se inválido."""
    t = ''.join(c for c in str(x) if c.isdigit())
    if t.startswith('55') and len(t) >= 12:
        t = t[2:]
    t = t.lstrip('0')
    return (t[:2] + t[-8:]) if len(t) >= 10 else ''


def ler_sheets(sheet_id, intervalo, credencial):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    cred = service_account.Credentials.from_service_account_file(
        os.path.expanduser(credencial), scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    svc = build('sheets', 'v4', credentials=cred)
    r = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=intervalo,
                                        valueRenderOption='UNFORMATTED_VALUE',
                                        dateTimeRenderOption='FORMATTED_STRING').execute()
    v = r.get('values', [])
    cab = [str(c).replace('\n', ' ').strip() for c in v[0]]
    linhas = [row + [''] * (len(cab) - len(row)) for row in v[1:]]
    return pd.DataFrame(linhas, columns=cab)


def carregar_leads(cfg):
    L = cfg['leads']
    if L.get('sheet_id'):
        df = ler_sheets(L['sheet_id'], L['intervalo'], L['credencial'])
    else:
        df = pd.read_csv(os.path.expanduser(L['csv']), sep=L.get('sep', ','), dtype=str, encoding='utf-8-sig').fillna('')
        df.columns = [c.replace('\n', ' ').strip() for c in df.columns]
    col = L['colunas']
    out = pd.DataFrame({k: df[v] if v in df.columns else '' for k, v in col.items()})
    # data: tenta todos os formatos e combina
    formatos = L.get('formatos_data', ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y%H:%M:%S', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y'])
    bruto = out['data'].astype(str).str.strip()
    dt = pd.Series(pd.NaT, index=out.index)
    por_formato = {}
    for f in formatos:
        p = pd.to_datetime(bruto, format=f, errors='coerce')
        novos = dt.isna() & p.notna()
        por_formato[f] = int(novos.sum())
        dt = dt.fillna(p)
    out['dt'] = dt
    out['k'] = out['telefone'].map(chave_telefone)
    for c in ('campanha', 'grupo', 'anuncio', 'termo', 'cidade', 'status'):
        if c not in out:
            out[c] = ''
        out[c] = out[c].astype(str).str.strip()
    out['termo'] = out['termo'].str.lower()
    qual = {'linhas': int(len(out)), 'sem_data': int(out.dt.isna().sum()), 'sem_telefone': int((out.k == '').sum()),
            'linhas_por_formato_de_data': por_formato}
    return out[out.dt.notna()].copy(), qual


# ---------------------------------------------------------------- CRM
def _casa(regra, linha):
    for k, v in regra.items():
        neg = k.startswith('!')
        coluna = k[1:] if neg else k
        valor = str(linha.get(coluna, '')).strip()
        vs = v if isinstance(v, list) else [v]
        achou = valor in vs
        if neg and achou:
            return False
        if not neg and not achou:
            return False
    return True


def estado_crm(linha, estados):
    """(estado, motivo). estado em venda|desq|aberto. Regras em ordem; sem regra = aberto."""
    for nome in ('venda', 'desq', 'aberto'):
        for r in estados.get(nome, []):
            if _casa(r['onde'], linha):
                motivo = r.get('motivo', '')
                for c in ([r['motivo_col']] if isinstance(r.get('motivo_col'), str) else r.get('motivo_col', [])):
                    v = str(linha.get(c, '')).strip().strip('.')
                    if v:
                        motivo = v[:1].upper() + v[1:]
                        break
                if nome == 'desq' and not motivo:
                    motivo = r.get('motivo_padrao', '(sem motivo informado)')
                return nome, re.sub(r'\s+', ' ', motivo)
    return 'aberto', '(sem regra para este desfecho)'


def carregar_crm(cfg):
    C = cfg['crm']
    df = pd.read_csv(os.path.expanduser(C['csv']), sep=C.get('sep', ';'), dtype=str, encoding='utf-8-sig').fillna('')
    df.columns = [c.strip() for c in df.columns]
    tel = C['colunas']['telefone']
    df['k'] = df[tel].map(chave_telefone)
    r = df.apply(lambda row: estado_crm(row, C['estados']), axis=1, result_type='expand')
    df['estado'], df['motivo'] = r[0], r[1]
    prior = {'venda': 0, 'aberto': 1, 'desq': 2}
    df['p'] = df['estado'].map(prior)
    if C.get('prioridade_tipos'):
        ordem = {t: i for i, t in enumerate(C['prioridade_tipos'])}
        df['p2'] = df[C['colunas']['tipo']].map(lambda t: ordem.get(t, 99))
        df = df.sort_values('p2')
    else:
        df = df.sort_values('p')
    return df


# ---------------------------------------------------------------- análise
def _contagem(df):
    return dict(leads=int(len(df)), mql=int((df.estado == 'venda').sum()), lost=int((df.estado == 'desq').sum()),
                lostReasons={k: int(v) for k, v in df[df.estado == 'desq'].motivo.value_counts().items()})


def _seg(df, col, gasto=None, minimo=1):
    linhas = []
    for nome, g in df.groupby(col):
        if not str(nome) or len(g) < minimo:
            continue
        v = int((g.estado == 'venda').sum())
        gst = (gasto or {}).get(nome)
        linhas.append(dict(nome=nome, leads=int(len(g)), vendas=v, taxa=v / len(g) if len(g) else 0.0,
                           desq=int((g.estado == 'desq').sum()),
                           gasto=None if gst is None else round(gst, 2),
                           custo_venda=(round(gst / v, 2) if gst and v else None)))
    return sorted(linhas, key=lambda x: (-x['vendas'], -x['leads']))


def rodar(cfg, ctx=None):
    """ctx: {'gasto_campanha':{}, 'gasto_grupo':{}, 'gasto_palavra':{}} já na janela (escalado se preciso)."""
    ctx = ctx or {}
    V = cfg
    leads, qual = carregar_leads(V)
    crm = carregar_crm(V)
    j = V['janela']
    ini, fim = pd.Timestamp(j['inicio']), pd.Timestamp(j['fim']) + pd.Timedelta(days=1)
    mc = V.get('mapa_campanhas', {})
    mg = V.get('mapa_grupos', {})
    leads['camp'] = leads.campanha.map(lambda x: mc.get(x, x))
    leads['grp'] = leads.grupo.map(lambda x: mg.get(x, x))

    # --- vendas do CRM x planilha (ignora a data)
    ven = crm[(crm.estado == 'venda') & (crm.k != '')].drop_duplicates('k')
    achadas = ven[ven.k.isin(set(leads.k))]
    cidcol = V['crm']['colunas'].get('cidade')
    nao = ven[~ven.k.isin(set(leads.k))]
    crm_info = dict(linhas=int(len(crm)), vendas=int(len(ven)), vendas_achadas=int(len(achadas)),
                    taxa_cruzamento=round(len(achadas) / len(ven), 4) if len(ven) else None,
                    nao_achadas=int(len(nao)),
                    nao_achadas_por_cidade=({k: int(v) for k, v in nao[cidcol].value_counts().items()} if cidcol else {}))

    # --- leads da janela, sem repetidos por telefone
    L = leads[(leads.dt >= ini) & (leads.dt < fim)].sort_values('dt')
    L = pd.concat([L[L.k != ''].groupby('k').tail(1), L[L.k == '']]).copy()
    ix = crm[crm.k != ''].drop_duplicates('k').set_index('k')[['estado', 'motivo']]
    L = L.join(ix, on='k')
    sem_reg = L.estado.isna()
    L['estado'] = L.estado.fillna('aberto')
    L['motivo'] = np.where(sem_reg, '(sem registro no CRM)', L.motivo.fillna(''))
    L['sem_registro'] = sem_reg

    gasto_c = ctx.get('gasto_campanha', {})
    gasto_g = ctx.get('gasto_grupo', {})
    gasto_p = ctx.get('gasto_palavra', {})
    L['tn'] = L.termo.map(norm)
    seg = dict(
        campanha=_seg(L, 'camp', gasto_c),
        grupo=_seg(L, 'grp', gasto_g),
        anuncio=_seg(L, 'anuncio'),
        palavra=_seg(L, 'tn', gasto_p),
        cidade=_seg(L, L.cidade.map(norm).rename('cid')),
        status_planilha=_seg(L, L.status.str.lower().rename('st')),
    )
    # anúncio dentro do grupo (a pergunta "qual anúncio vende mais" depende do grupo)
    anun_grupo = []
    for (g, a), x in L.groupby(['grp', 'anuncio']):
        if not a:
            continue
        v = int((x.estado == 'venda').sum())
        anun_grupo.append(dict(grupo=g, anuncio=a, leads=int(len(x)), vendas=v, taxa=v / len(x)))
    seg['anuncio_por_grupo'] = sorted(anun_grupo, key=lambda x: (x['grupo'], -x['taxa']))

    # --- árvore campanha > grupo > anúncio, com qualificados (vendas), desqualificados e motivos
    def no(id_, nome, invest, df, filhos=None):
        n = dict(id=id_, name=nome, invest=None if invest is None else round(invest, 2), **_contagem(df))
        if filhos:
            n['children'] = filhos
        return n
    arvore = []
    for ci, (camp, cdf) in enumerate(L.groupby('camp'), 1):
        if not camp:
            continue
        grupos = []
        for gi, (g, gdf) in enumerate(cdf.groupby('grp'), 1):
            ads = [no(f'g{ci}a{gi}a{ai}', f'Anúncio {a or "(sem utm_content)"}', None, adf)
                   for ai, (a, adf) in enumerate(gdf.groupby('anuncio'), 1)]
            grupos.append(no(f'g{ci}a{gi}', g or '(grupo não identificado)', gasto_g.get(g), gdf, ads))
        arvore.append(no(f'g{ci}', camp, gasto_c.get(camp), cdf, grupos))
    resto = L[L.camp == '']
    if len(resto):
        arvore.append(no('g9', '(Lead sem UTM de campanha)', None, resto))
    palavras = []
    for t, g in L.groupby('tn'):
        if t:
            c = _contagem(g)
            palavras.append(dict(name=t, invest=(round(gasto_p[t], 2) if t in gasto_p else None),
                                 leads=c['leads'], mql=c['mql'], lost=c['lost']))
    palavras.sort(key=lambda k: (-k['mql'], -k['leads']))

    return dict(
        janela=j, qualidade=qual, crm=crm_info,
        leads=dict(linhas_janela=int(((leads.dt >= ini) & (leads.dt < fim)).sum()), unicos=int(len(L)),
                   sem_registro_crm=int(sem_reg.sum()),
                   estados={k: int(v) for k, v in L.estado.value_counts().items()}),
        segmentos=seg,
        motivos=[dict(nome=k, qtd=int(v)) for k, v in L[L.estado == 'desq'].motivo.value_counts().items()],
        arvore=arvore, palavras=palavras)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    saida = sys.argv[sys.argv.index('--saida') + 1] if '--saida' in sys.argv else 'vendas.json'
    res = rodar(cfg.get('vendas', cfg))
    json.dump(res, open(saida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ok ->', saida)
    print('leads únicos:', res['leads']['unicos'], '| estados:', res['leads']['estados'],
          '| vendas achadas:', f"{res['crm']['vendas_achadas']}/{res['crm']['vendas']}")
