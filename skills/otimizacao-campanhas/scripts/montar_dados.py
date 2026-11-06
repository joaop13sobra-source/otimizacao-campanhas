"""Cruza leads do CRM com a mídia (Meta + Google) e gera o dados.json do dashboard.

Uso:  python3 -I montar_dados.py config.json --saida dados.json

Leads: leads_normalizados.json (puxar_kommo.py) ou planilha/CSV mapeada no config (sem API).
Regras: ver references/regua-do-funil.md e references/armadilhas.md. Em resumo:
- Qualificação pelo maior estágio já alcançado no histórico; Perdido nunca entra na ordem do funil.
- Todo lead pago cai em um balde só: qualificado (ativo ou perdido depois), desqualificado ou em aberto.
- Lead sem filho identificado vira nó sintético com investimento 0: a soma dos filhos sempre bate com o pai.
- Sai com erro se uma etapa do CRM não estiver no config, ou se a árvore não reconciliar.
O dados.json não leva nome, telefone nem e-mail de lead.
"""
import argparse, collections, html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import data, norm, num, tabela

# utm_source costuma trazer o posicionamento (Instagram_Feed, Facebook_Mobile_Reels), não só o nome da rede
GOOGLE_ORIGENS = re.compile(r'\b(google|adwords|gads)\b')
META_ORIGENS = re.compile(r'\b(facebook|fb|instagram|ig|meta|messenger|an)\b')
SEM_MOTIVO = '(sem motivo preenchido)'


class Arvore:
    """Nó da árvore de mídia. Guarda os leads em memória; o JSON final só leva contagens."""
    seq = 0

    def __init__(self, nome, invest=0.0, sintetico=False):
        Arvore.seq += 1
        self.id, self.nome, self.invest, self.sintetico = f'n{Arvore.seq}', nome, invest, sintetico
        self.filhos, self.leads = {}, []

    def filho(self, chave, nome=None, sintetico=False):
        if chave not in self.filhos:
            self.filhos[chave] = Arvore(nome or chave, sintetico=sintetico)
        return self.filhos[chave]

    def todos(self):
        saida = list(self.leads)
        for f in self.filhos.values():
            saida += f.todos()
        return saida

    def total_invest(self):
        return self.invest + sum(f.total_invest() for f in self.filhos.values())

    def json(self):
        L = self.todos()
        n = {'id': self.id, 'name': html.escape(self.nome), 'invest': round(self.total_invest(), 2), 'leads': len(L),
             'mql': sum(x['mql'] for x in L), 'sql': sum(x['sql'] for x in L), 'venda': sum(x['venda'] for x in L),
             'lost': sum(x['lost'] for x in L), 'qlost': sum(x['qlost'] for x in L),
             'lostReasons': contagem(x['motivo'] for x in L if x['lost']),
             'qualifiedLostReasons': contagem(x['motivo'] for x in L if x['qlost'])}
        if self.sintetico:
            n['synthetic'] = True
        if self.filhos:
            n['children'] = [f.json() for f in self.filhos.values()]
            # lead parado no próprio nó (sem filho) iria sumir do drill-down: vira filho sintético visível
            soltos = [x for x in self.leads]
            if soltos:
                extra = Arvore('(Não identificado neste nível)', sintetico=True)
                extra.leads = soltos
                n['children'].append(extra.json())
        return n


def contagem(it):
    return dict(collections.Counter(html.escape(str(i)) for i in it))


def carregar_leads(cfg, base):
    L = cfg['leads']
    if L.get('arquivo_normalizado'):
        return json.load(open(base / L['arquivo_normalizado']))
    linhas = tabela(base / L['arquivo'], L['colunas'], L.get('aba'))
    sep = L.get('separador_historico', '|')
    for l in linhas:
        l['historico'] = [e.strip() for e in str(l.get('historico') or '').split(sep) if e.strip()]
        l['criado_em'] = str(l.get('criado_em') or '')
    return linhas


def classificar(leads, cfg):
    """Marca mql/sql/venda/lost/qlost. Compara pela ORDEM do funil no config, nunca pelo id da etapa."""
    E = cfg['etapas']
    ordem = [norm(x) for x in E['ordem']]
    perdido = {norm(x) for x in E['perdido']}
    ignorar = {norm(x) for x in E.get('ignorar', [])}
    if perdido & set(ordem):
        sys.exit('Etapa de perda não pode estar em etapas.ordem: inflaria o "maior estágio" de todo lead perdido.')
    rank = {n: i for i, n in enumerate(ordem)}
    r_mql, r_sql = rank[norm(E['mql'])], rank[norm(E['sql'])] if E.get('sql') else 10 ** 6
    vendas = {norm(x) for x in E['venda']}
    desconhecidas = collections.Counter()
    for l in leads:
        atual = norm(l.get('etapa_atual'))
        passou = [norm(x) for x in l.get('historico') or []] + ([atual] if atual else [])
        for p in passou:
            if p and p not in rank and p not in perdido and p not in ignorar:
                desconhecidas[p] += 1
        m = max((rank[p] for p in passou if p in rank), default=-1)
        l['mql'], l['sql'] = m >= r_mql, m >= r_sql
        l['venda'] = any(p in vendas for p in passou)
        perdeu = atual in perdido
        l['lost'], l['qlost'] = perdeu and not l['mql'], perdeu and l['mql']
        l['motivo'] = str(l.get('motivo_perda') or '').strip() or SEM_MOTIVO
    if desconhecidas:
        sys.exit('Etapas fora do config (inclua em etapas.ordem, etapas.perdido ou etapas.ignorar): ' + ', '.join(sorted(desconhecidas)))
    return leads


def apelidos(mapa, nomes):
    """Índice {texto normalizado: nome real}: nomes reais + apelidos do config (slug de UTM, id de campanha)."""
    ind = {norm(n): n for n in nomes}
    for k, v in (mapa or {}).items():
        ind[norm(k)] = v
    return ind


def carregar_midia(cfg, base):
    """Devolve linhas {plataforma: [{campanha, grupo, anuncio, invest}]}, palavras-chave e o total de cada plataforma."""
    M, saida, palavras = cfg['midia'], {'meta': [], 'google': []}, []
    grupos = {norm(c): nome for nome, lista in (cfg.get('agrupar_campanhas') or {}).items() for c in lista}
    fora = re.compile(cfg['excluir']['campanhas_regex'], re.I) if (cfg.get('excluir') or {}).get('campanhas_regex') else None
    for plat in ('meta', 'google'):
        c = M.get(plat)
        if not c:
            continue
        for r in tabela(base / c['arquivo'], c['colunas'], c.get('aba')):
            camp = str(r.get('campanha') or '').strip()
            if not camp or (fora and fora.search(camp)):
                continue
            # RSA não tem nome: com a coluna "Sufixo do URL final" mapeada, o anúncio é o utm_content dela
            suf = re.search(r'utm_content=([^&]+)', str(r.get('sufixo') or ''))
            saida[plat].append({'campanha': grupos.get(norm(camp), camp), 'grupo': str(r.get('grupo') or '').strip(), 'anuncio': suf.group(1) if suf else str(r.get('anuncio') or '').strip(),
                                'invest': num(r.get('invest'), c.get('formato_numero', 'auto'))})
    k = (M.get('google') or {}).get('palavras')
    if k:
        for r in tabela(base / k['arquivo'], k['colunas'], k.get('aba')):
            camp = str(r.get('campanha') or '').strip()
            if camp and not (fora and fora.search(camp)):
                palavras.append({'campanha': grupos.get(norm(camp), camp), 'grupo': str(r.get('grupo') or '').strip(), 'palavra': str(r.get('palavra') or '').strip(),
                                 'invest': num(r.get('invest'), k.get('formato_numero', M['google'].get('formato_numero', 'auto')))})
    return saida, palavras


def esqueleto(linhas):
    """Árvore campanha > conjunto/grupo > anúncio com o investimento real dos exports."""
    raizes = {}
    for r in linhas:
        c = raizes.setdefault(norm(r['campanha']), Arvore(r['campanha']))
        if not r['grupo']:
            c.invest += r['invest']
            continue
        g = c.filho(norm(r['grupo']), r['grupo'])
        if not r['anuncio']:
            g.invest += r['invest']
            continue
        g.filho(norm(r['anuncio']), r['anuncio']).invest += r['invest']
    return raizes


def posicionar(l, raiz, utm_grupo, utm_anuncio, ap_grupo):
    """Desce o lead até o nível mais fundo que os UTMs permitem, sem chutar quando o anúncio se repete."""
    g = norm(ap_grupo.get(norm(utm_grupo), utm_grupo))
    a = norm(utm_anuncio)
    if g in raiz.filhos:
        grupo = raiz.filhos[g]
        if a in grupo.filhos:
            grupo.filhos[a].leads.append(l)
        elif grupo.filhos:
            grupo.filho('__sem_anuncio', '(Anúncio sem gasto no período / não identificado)', True).leads.append(l)
        else:
            grupo.leads.append(l)
        return
    candidatos = [f for f in raiz.filhos.values() if a in f.filhos] if a else []
    if len(candidatos) == 1:
        candidatos[0].filhos[a].leads.append(l)
    elif len(candidatos) > 1:
        raiz.filho('__replicado', '(Anúncio replicado em vários públicos/grupos: sem como saber qual gerou o lead)', True).leads.append(l)
    elif raiz.filhos:
        raiz.filho('__sem_grupo', '(Público/grupo sem gasto no período / não identificado)', True).leads.append(l)
    else:
        raiz.leads.append(l)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--saida', default='dados.json')
    a = ap.parse_args()
    base = Path(a.config).resolve().parent
    cfg = json.load(open(a.config))
    U = cfg['utm']
    leads = classificar(carregar_leads(cfg, base), cfg)
    midia, palavras = carregar_midia(cfg, base)

    Ex = cfg.get('excluir') or {}
    re_teste = re.compile(Ex['leads_teste_regex'], re.I) if Ex.get('leads_teste_regex') else None
    organico = {norm(x) for x in Ex.get('origens_organicas', [])}
    fora_camp = re.compile(Ex['campanhas_regex'], re.I) if Ex.get('campanhas_regex') else None

    raizes = {p: esqueleto(midia[p]) for p in midia}
    ind = {p: apelidos((U.get(p) or {}).get('apelidos_campanha'), [r['campanha'] for r in midia[p]]) for p in midia}
    ind_kw = collections.defaultdict(set)
    for k in palavras:
        ind_kw[norm(k['palavra'])].add((k['campanha'], k['grupo']))
    arv_kw = {}
    for k in palavras:
        no = arv_kw.setdefault(norm(k['palavra']), Arvore(k['palavra']))
        no.invest += k['invest']

    q = collections.Counter()
    sem_utm_com_mql = 0
    extras = {'meta': {}, 'google': {}}
    pagos = []
    for l in leads:
        if re_teste and re_teste.search(f"{l.get('nome', '')} {l.get('email', '')}"):
            q['teste'] += 1
            continue
        src, camp = norm(l.get('utm_source')), str(l.get('utm_campaign') or '').strip()
        if fora_camp and fora_camp.search(camp):
            q['campanha_excluida'] += 1
            continue
        if src in organico:
            q['organico'] += 1
            continue
        if not camp:
            q['sem_utm'] += 1
            sem_utm_com_mql += l['mql']
            continue
        # macro não substituída: {{...}} é sintaxe do Meta, {...} é ValueTrack do Google
        if '{' in camp:
            plat = 'meta' if '{{' in camp else 'google'
            q['utm_quebrada'] += 1
            pagos.append(l)
            extras[plat].setdefault('__quebrada', Arvore('(UTM quebrada: macro não substituída)', sintetico=True)).leads.append(l)
            continue
        c = norm(camp)
        # o nome real da campanha decide o canal; a origem só desempata (nunca o contrário)
        em_meta, em_google = c in ind['meta'], c in ind['google']
        plat = 'google' if em_google and not em_meta else 'meta' if em_meta and not em_google else \
            'google' if GOOGLE_ORIGENS.search(src) else 'meta' if META_ORIGENS.search(src) or em_meta else None
        if plat is None:
            q['canal_desconhecido'] += 1
            sem_utm_com_mql += l['mql']
            continue
        pagos.append(l)
        C = U[plat]
        utm_grupo, utm_anuncio = l.get(C.get('grupo', 'utm_medium')) or '', l.get(C.get('anuncio', 'utm_content')) or ''
        termo = norm(l.get(C.get('palavra', 'utm_term')))
        if plat == 'google' and termo:
            no_kw = arv_kw.get(termo) or arv_kw.setdefault(termo, Arvore(str(l.get(C.get('palavra', 'utm_term'))), sintetico=True))
            no_kw.leads.append(l)
        destino = norm(ind[plat][c]) if c in ind[plat] else None
        if plat == 'google' and destino is None and len(ind_kw.get(termo, ())) == 1:
            # campanha não bate pelo UTM (slug genérico): a palavra-chave, se for única, resolve
            destino_c, destino_g = next(iter(ind_kw[termo]))
            destino, utm_grupo = norm(destino_c), destino_g
            q['campanha_resolvida_por_palavra'] += 1
        if destino is None:
            q['campanha_sem_match'] += 1
            extras[plat].setdefault('__sem_match', Arvore('(Campanha da UTM sem gasto no período / não encontrada na mídia)', sintetico=True)).filho(c, camp, True).leads.append(l)
            continue
        posicionar(l, raizes[plat][destino], utm_grupo, utm_anuncio, apelidos(C.get('apelidos_grupo'), []))

    arv = {p: [n.json() for n in list(raizes[p].values()) + list(extras[p].values())] for p in raizes}

    # --- reconciliação: a soma dos filhos tem que bater com o pai, em todo nó, e a mídia com os exports
    def conferir(n):
        if n.get('children'):
            for k in ('leads', 'mql', 'sql', 'venda', 'lost', 'qlost'):
                assert n[k] == sum(f[k] for f in n['children']), (n['name'], k)
            assert n['invest'] >= sum(f['invest'] for f in n['children']) - 0.05, (n['name'], 'invest')
            for f in n['children']:
                conferir(f)
    for p in arv:
        for n in arv[p]:
            conferir(n)
    tot_leads = sum(n['leads'] for p in arv for n in arv[p])
    assert tot_leads == len(pagos), (tot_leads, len(pagos))
    inv = {p: round(sum(r['invest'] for r in midia[p]), 2) for p in midia}
    for p in midia:
        assert abs(sum(n['invest'] for n in arv[p]) - inv[p]) < 0.05, ('mídia não reconcilia', p)
        painel = (cfg.get('conferir_total') or {}).get(p)
        if painel is not None and abs(painel - inv[p]) > 0.05:
            sys.exit(f'Investimento {p}: export soma {inv[p]}, painel diz {painel}. Confira formato de número e linhas de total.')

    meses = collections.OrderedDict()
    for l in sorted(pagos, key=lambda x: data(x.get('criado_em')) or data('1900-01-01')):
        d = data(l.get('criado_em'))
        if d is None:
            q['sem_data'] += 1
            continue
        m = meses.setdefault(d.strftime('%Y-%m'), collections.Counter())
        for k in ('mql', 'sql', 'venda', 'lost'):
            m[k] += l[k]
        m['leads'] += 1

    dados = {
        'META_TREE': arv['meta'], 'GOOGLE_TREE': arv['google'],
        'GOOGLE_KEYWORDS': [n.json() for n in arv_kw.values()],
        'LOSS_REASONS': [{'name': k, 'qty': v} for k, v in contagem(x['motivo'] for x in pagos if x['lost']).items()],
        'QUALIFIED_LOST_REASONS': [{'name': k, 'qty': v} for k, v in contagem(x['motivo'] for x in pagos if x['qlost']).items()],
        'por_mes': [{'mes': k, **v} for k, v in meses.items()],
        'totais': {'investimento': inv, 'leads': len(pagos), 'mql': sum(x['mql'] for x in pagos), 'sql': sum(x['sql'] for x in pagos),
                   'venda': sum(x['venda'] for x in pagos), 'desqualificados': sum(x['lost'] for x in pagos),
                   'qualificados_perdidos': sum(x['qlost'] for x in pagos),
                   'em_aberto': len(pagos) - sum(x['mql'] for x in pagos) - sum(x['lost'] for x in pagos)},
        'qualidade': {'leads_no_crm': len(leads), 'pagos': len(pagos), **q, 'mql_fora_da_arvore': sem_utm_com_mql,
                      'perdidos_sem_motivo': sum(1 for x in pagos if x['motivo'] == SEM_MOTIVO and (x['lost'] or x['qlost'])),
                      'leads_com_historico': sum(1 for x in pagos if x.get('historico')),
                      'sem_historico': cfg['leads'].get('sem_historico', False)},
        'meta': {k: cfg.get(k) for k in ('cliente', 'crm', 'periodo', 'notas')} | {'etapas': {k: cfg['etapas'].get(k) for k in ('mql', 'sql', 'venda', 'rotulo_sql', 'rotulo_venda')}},
    }
    json.dump(dados, open(a.saida, 'w'), ensure_ascii=False, indent=1)
    t = dados['totais']
    print(f"Pagos {t['leads']} | MQL {t['mql']} | SQL {t['sql']} | Venda {t['venda']} | Desq. {t['desqualificados']} | Qualificou e perdeu {t['qualificados_perdidos']} | Em aberto {t['em_aberto']}")
    print('Investimento', inv)
    print('Qualidade', json.dumps(dados['qualidade'], ensure_ascii=False))


if __name__ == '__main__':
    main()
