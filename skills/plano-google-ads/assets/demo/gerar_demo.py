#!/usr/bin/env python3
"""Gera dados SINTÉTICOS (operadora fictícia "NetExemplo") nos formatos reais de entrada da skill.

    python3 assets/demo/gerar_demo.py            # grava em assets/demo/dados/

Saída: 4 relatórios do Google Ads (pt-BR), planilha de leads (CSV, com dois formatos de data de propósito)
e relatório de vendas do CRM. Nada aqui vem de cliente real: nomes, telefones e números são inventados
(semente fixa, resultado sempre igual). Serve para testar a skill e como exemplo de formato.
"""
import csv
import os
import random
from datetime import datetime, timedelta

R = random.Random(42)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados')
os.makedirs(OUT, exist_ok=True)


def m(x, d=2):            # 1933.46 -> "1933,46"
    return f'{x:.{d}f}'.replace('.', ',')


def i(x):                  # 2769 -> "2.769"
    return f'{int(round(x)):,}'.replace(',', '.')


def p(x):                  # 21.68 -> "21,68%"
    return f'{x:.2f}'.replace('.', ',') + '%'


def escrever(nome, titulo, periodo, cab, linhas):
    with open(os.path.join(OUT, nome), 'w', encoding='utf-8-sig', newline='') as f:
        f.write(titulo + '\n' + periodo + '\n')
        w = csv.writer(f)
        w.writerow(cab)
        w.writerows(linhas)


PERIODO = '1 de outubro de 2026 - 19 de outubro de 2026'
P = '[DEMO][SEARCH][LEADS] '
CAMP_I, CAMP_C = P + 'Institucional', P + 'Campanha Core'

# palavra-chave: (campanha, grupo, correspondência, IQ, cliques, CPC, taxa de conversão por clique)
KW = [
    ('NetExemplo', CAMP_I, 'Marca', 10, 520, 3.10, 0.205),
    ('Net Exemplo', CAMP_I, 'Marca', 10, 34, 2.30, 0.17),
    ('NetExemplo Internet', CAMP_I, 'Marca', 10, 3, 3.00, 0.0),
    ('internet residencial', CAMP_C, 'Internet Fibra', 5, 110, 5.20, 0.36),
    ('Internet Fibra Regional', CAMP_C, 'Internet Fibra', 4, 94, 4.80, 0.23),
    ('Serviço Internet', CAMP_C, 'Internet Fibra', None, 68, 5.90, 0.27),
    ('Internet em casa', CAMP_C, 'Internet Fibra', None, 3, 2.70, 0.0),
    ('provedor de internet', CAMP_C, 'Provedor de Internet', 3, 140, 4.10, 0.22),
    ('internet cidade alfa', CAMP_C, 'Provedor de Internet', 8, 5, 9.50, 0.30),
    ('internet em cidade alfa', CAMP_C, 'Provedor de Internet', 8, 1, 14.80, 1.0),
    ('fibra óptica', CAMP_C, 'Provedor de Internet', 4, 2, 3.60, 0.50),
]
tot = {}
kw_rows = []
for nome, camp, grupo, iq, cl, cpc, cvr in KW:
    custo, conv = cl * cpc, cl * cvr
    impr = cl / R.uniform(0.07, 0.25)
    t = tot.setdefault(camp, dict(custo=0, cl=0, conv=0, impr=0))
    t['custo'] += custo; t['cl'] += cl; t['conv'] += conv; t['impr'] += impr
    kw_rows.append(['Ativado', nome, 'Correspondência ampla', camp, grupo, 'Qualificado', i(impr), i(cl), m(custo), m(conv), m(custo / conv) if conv else '0,00', str(iq) if iq else ' --'])
kw_rows.append(['Pausado', 'operadoras de internet residencial', 'Correspondência ampla', CAMP_C, 'Provedor de Internet', 'Pausado', '0', '0', '0,00', '0,00', '0,00', ' --'])
escrever('palavras-chave.csv', 'Relatório de palavras-chave da rede de pesquisa', PERIODO,
         ['Status da palavra-chave', 'Palavra-chave', 'Tipo de corresp.', 'Campanha', 'Grupo de anúncios', 'Status', 'Impr.', 'Interações', 'Custo', 'Conversões', 'Custo / conv.', 'Índice de qualidade'], kw_rows)

# campanhas
orc = {CAMP_I: 100, CAMP_C: 100}
info = {CAMP_I: ('Qualificado', 'a maioria dos anúncios foi reprovada', 69.4, 21.7, 8.9), CAMP_C: ('Qualificado (limitado)', 'a maioria dos anúncios foi reprovada; limitada pelo volume de pesquisas', 40.4, 31.3, 28.3)}
camp_rows = []
for c, t in tot.items():
    st, mot, parc, po, pc_ = info[c]
    camp_rows.append(['Ativada', c, m(orc[c]), st, mot, 'Pesquisa', i(t['impr']), i(t['cl']), i(t['cl']), m(t['custo']), m(t['conv']), p(parc), p(po), p(pc_)])
escrever('campanhas.csv', 'Relatório de campanha', PERIODO,
         ['Status da campanha', 'Campanha', 'Orçamento', 'Status', 'Motivos do status', 'Tipo de campanha', 'Impr.', 'Interações', 'Cliques', 'Custo', 'Conversões',
          'Parcela impr rede de pesquisa', 'Parc impr perd rede de pesquisa (orç)', 'Parc impr perd rede de pesquisa (class.)'], camp_rows)

# grupos
gr = {}
for nome, camp, grupo, iq, cl, cpc, cvr in KW:
    g = gr.setdefault((camp, grupo), dict(custo=0, cl=0, conv=0, impr=0))
    g['custo'] += cl * cpc; g['cl'] += cl; g['conv'] += cl * cvr; g['impr'] += cl / 0.12
grp_rows = [['Ativado', g, c, 'Qualificado', i(v['impr']), i(v['cl']), m(v['custo']), m(v['conv']), m(v['custo'] / v['conv'])] for (c, g), v in gr.items()]
escrever('grupos.csv', 'Relatório do grupo de anúncios', PERIODO,
         ['Status do grupo de anúncios', 'Grupo de anúncios', 'Campanha', 'Status', 'Impr.', 'Interações', 'Custo', 'Conversões', 'Custo / conv.'], grp_rows)

# termos de pesquisa (cobrem ~75% do gasto; o resto fica oculto, como no Google Ads)
VAR = {
    'NetExemplo': ['netexemplo', 'netexemplo internet', 'netexemplo cidade alfa', 'netexemplo cidade beta', 'netexemplo whatsapp', 'netexemplo telefone', 'numero da netexemplo', 'netexemplo boleto', 'netexemplo 2 via', 'netexemplo suporte', 'netexemplo planos'],
    'Net Exemplo': ['net exemplo', 'net exemplo internet', 'net exemplo cidade gama'],
    'NetExemplo Internet': ['internet netexemplo'],
    'internet residencial': ['internet residencial', 'internet residencial barata', 'melhor internet residencial', 'internet residencial vivo', 'plano internet residencial claro'],
    'Internet Fibra Regional': ['internet fibra regional', 'internet fibra cidade beta', 'internet fibra cidade omega', 'internet fibra nova cidade sigma', 'concorrente local telefone', 'netexemplo cidade beta'],
    'Serviço Internet': ['serviço internet', 'serviço de internet cidade gama', 'wifi'],
    'Internet em casa': ['internet em casa'],
    'provedor de internet': ['provedor de internet', 'provedor de internet cidade alfa', 'provedores de internet perto de mim', 'vivo fibra', 'oi fibra telefone', 'tim fibra', 'netexemplo cidade alfa', 'netexemplo planos'],
    'internet cidade alfa': ['internet cidade alfa', 'internet cidade alfa rj'],
    'internet em cidade alfa': ['internet em cidade alfa'],
    'fibra óptica': ['fibra óptica internet'],
}
PESOS = {'NetExemplo': [0.40, 0.12, 0.07, 0.04, 0.12, 0.06, 0.07, 0.015, 0.015, 0.02, 0.07]}
term_rows = []
for nome, camp, grupo, iq, cl, cpc, cvr in KW:
    alvo = cl * 0.75
    termos = VAR[nome]
    pesos = PESOS.get(nome) or [R.random() ** 2 + 0.05 for _ in termos]
    s = sum(pesos)
    for t, w in zip(termos, pesos):
        c_ = max(0, round(alvo * w / s)) if len(termos) > 1 else round(alvo)
        cust = c_ * cpc * R.uniform(0.9, 1.1)
        conv = round(c_ * cvr * R.uniform(0.7, 1.2), 1) if c_ else 0
        if any(x in t for x in ('vivo', 'oi fibra', 'tim fibra', 'concorrente local', 'claro')):
            conv = round(conv * 0.3, 1)
        conv = min(conv, c_)
        impr = max(c_, round(c_ / R.uniform(0.08, 0.3))) if c_ else R.randint(1, 8)
        tipo = R.choice(['Correspondência de frase (variação aproximada)', 'Correspondência ampla', 'Correspondência de frase'])
        term_rows.append([t, tipo, 'Nenhum', camp, grupo, 'BRL', m(R.uniform(100, 700)), str(c_), i(impr), p(c_ / impr * 100 if impr else 0), m(cpc), m(cust), 'Pesquisa', p(conv / c_ * 100 if c_ else 0), m(conv), m(cust / conv) if conv else '0,00'])
# cauda de termos sem clique
for k in range(180):
    term_rows.append([f'internet termo raro {k}', 'Correspondência de frase (variação aproximada)', 'Nenhum', CAMP_C, 'Provedor de Internet', 'BRL', '0,00', '0', str(R.randint(1, 6)), '0,00%', '0', '0,00', 'Pesquisa', '0,00%', '0,00', '0,00'])
escrever('termos-de-pesquisa.csv', 'Relatório de termos de pesquisa', PERIODO,
         ['Termo de pesquisa', 'Tipo de corresp.', 'Adicionada/excluída', 'Campanha', 'Grupo de anúncios', 'Código da moeda', 'CPM médio', 'Cliques', 'Impr.', 'CTR', 'CPC méd.', 'Custo', 'Tipo de campanha', 'Taxa de conv.', 'Conversões', 'Custo / conv.'], term_rows)

# ---------------- leads (CSV) e CRM ----------------
# Telefones sintéticos usam o DDD 20 (que não existe no Brasil) para nunca coincidir com um número real.
CIDADES = [('CIDADE ALFA', 0.55), ('CIDADE BETA', 0.2), ('CIDADE GAMA', 0.15), ('CIDADE DELTA', 0.10)]
BAIRROS = {'CIDADE ALFA': ['Centro', 'Bairro Norte', 'Bairro Sul'], 'CIDADE BETA': ['Centro', 'Vila Nova'], 'CIDADE GAMA': ['Centro', 'Jardim'], 'CIDADE DELTA': ['Distrito 1', 'Distrito 2']}
GRP_UTM = {'Marca': ('institucional', 'marca'), 'Internet Fibra': ('core', 'internet-fibra'), 'Provedor de Internet': ('core', 'provedor-internet')}
leads, fone = [], 90000000
for nome, camp, grupo, iq, cl, cpc, cvr in KW:
    n = round(cl * cvr * 0.95 * 1.04)
    for _ in range(n):
        fone += R.randint(1, 37)
        ts = datetime(2026, 10, 1) + timedelta(seconds=R.randint(0, 19 * 86400 - 1))
        cidade = R.choices([c for c, _ in CIDADES], [w for _, w in CIDADES])[0]
        ad = R.choices(['ad01', 'ad02', 'ad03'], [0.35, 0.32, 0.33] if grupo == 'Marca' else [0.3, 0.4, 0.3])[0]
        u_c, u_m = GRP_UTM[grupo]
        leads.append(dict(ts=ts, tel=f'20 9{fone // 10000 % 10000:04d}-{fone % 10000:04d}', cidade=cidade, bairro=R.choice(BAIRROS[cidade]), st=R.choice(['valido'] * 11 + ['invalido'] * 9),
                          utm_c=u_c, utm_m=u_m, ad=ad, term=nome.lower()))
leads.sort(key=lambda x: x['ts'])
with open(os.path.join(OUT, 'leads.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['DATA E HORÁRIO  DE ENTRADA', 'NOME', 'TELEFONE', 'STATUS', 'CIDADE', 'BAIRRO', 'UTM:CAMPANHA', 'UTM:PÚBLICO', 'UTM:CRIATIVO', 'UTM TERM'])
    for k, l in enumerate(leads, 1):
        # dois formatos de data no mesmo arquivo, de propósito (a planilha real mudou no meio do período)
        d = l['ts'].strftime('%Y-%m-%d %H:%M:%S') if l['ts'] < datetime(2026, 10, 7) else l['ts'].strftime('%d/%m/%Y%H:%M:%S')
        w.writerow([d, f'Lead de teste {k:03d}', l['tel'], l['st'], l['cidade'], l['bairro'], l['utm_c'], l['utm_m'], l['ad'], l['term']])

crm = []
corte = datetime(2026, 10, 17, 23, 59, 59)
for k, l in enumerate(leads):
    if l['ts'] > corte or R.random() < 0.38:       # lead novo demais ou ainda sem registro no CRM
        continue
    r = R.random()
    base = dict(Telefone='(' + l['tel'][:2] + ') ' + l['tel'][3:], Cidade=l['cidade'].title(), Bairro=l['bairro'], Campanha='Google LP', Razao=f'Cliente teste {k:03d}')
    if r < 0.33:
        contrato = R.choices(['Ativo', 'Pre-contrato', 'Desistiu'], [0.5, 0.42, 0.08])[0]
        crm.append(dict(base, Tipo='NEGOCIAÇÕES VENCEMOS', Contrato=contrato, Motivo='', Segmento='', Plano=R.choice(['1G', '1G', '600M'])))
    elif r < 0.45:
        crm.append(dict(base, Tipo='NEGOCIAÇÕES PERDEMOS', Contrato='', Motivo=R.choice(['CLIENTE OPTOU POR NÃO CONTRATAR', 'PRAZO DE INSTALAÇÃO', 'NÃO APROVADO GRATUIDADE']), Segmento='', Plano=''))
    elif r < 0.70:
        crm.append(dict(base, Tipo='LEADS SEM VIABILIDADE', Contrato='', Motivo='', Segmento='Sem viabilidade no local', Plano=''))
    elif r < 0.78:
        crm.append(dict(base, Tipo='LEADS SEM ENDEREÇO OU VIABILIDADE CONFIRMADA', Contrato='', Motivo='', Segmento=R.choice(['', 'Lead Duplicado', 'Ja e Cliente']), Plano=''))
    else:
        crm.append(dict(base, Tipo='NEGOCIAÇÕES EM ANDAMENTO', Contrato='', Motivo='', Segmento='', Plano=''))
for k in range(6):                                 # vendas de leads que nunca entraram na planilha
    crm.append(dict(Telefone=f'(20) 98{R.randint(1000, 9999)}-{R.randint(1000, 9999)}', Cidade='Cidade Alfa', Bairro='Centro', Campanha='Google LP', Razao=f'Cliente externo {k}', Tipo='NEGOCIAÇÕES VENCEMOS', Contrato='Ativo', Motivo='', Segmento='', Plano='1G'))
with open(os.path.join(OUT, 'crm-vendas.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['Tipo Relatório', 'Motivo Perdemos', 'Razão', 'Telefone', 'Cidade', 'Bairro', 'Segmento', 'Campanha', 'Status Prospecção', 'Status Contrato', 'Plano Vendido'])
    for r in crm:
        w.writerow([r['Tipo'], r['Motivo'], r['Razao'], r['Telefone'], r['Cidade'], r['Bairro'], r['Segmento'], r['Campanha'], '', r['Contrato'], r['Plano']])

print('dados sintéticos gravados em', OUT)
for nome in sorted(os.listdir(OUT)):
    print(' ', nome, os.path.getsize(os.path.join(OUT, nome)), 'bytes')


# ---------------- volumes SINTÉTICOS do Semrush (para a seção de palavras novas renderizar offline) ----------------
import json
plano_path = os.path.join(os.path.dirname(OUT), '..', 'plano.exemplo.json')
if os.path.exists(plano_path):
    plano = json.load(open(plano_path, encoding='utf-8'))
    palavras = []
    for g in plano.get('novas_palavras', {}).get('grupos', []):
        palavras += g.get('palavras', [])
    for c in plano.get('estrutura', {}).get('campanhas', []):
        for g in c.get('grupos', []):
            palavras += g.get('palavras', [])
    vistos, linhas = set(), []
    RS = random.Random(7)
    GRANDES = {'netexemplo': 6200, 'net exemplo': 900, 'disponibilidade internet fibra': 2400, 'planos de internet residencial': 5100, 'internet residencial barata': 1300,
               'internet residencial perto de mim': 700, 'vivo fibra': 90000, 'claro internet': 30000, 'tim fibra': 22000, 'provedor de internet perto de mim': 600,
               'internet residencial': 21000, 'provedor de internet': 9800, 'internet fibra regional': 1500}
    for k in palavras:
        if k in vistos:
            continue
        vistos.add(k)
        vol = GRANDES.get(k) or max(10, int(RS.choice([10, 20, 20, 30, 40, 50, 90, 170, 320, 480, 880, 1300]) / (1 + 0.15 * len(k.split()))) // 10 * 10)
        linhas.append(dict(kw=k, vol=float(vol), cpc=round(RS.uniform(0.3, 3.4), 2), co=round(RS.uniform(0.1, 0.95), 2), kd=float(RS.choice([0, 0, 18, 25, 31, 44])),
                           intent='0', intencao='Comercial', n=k, classe='demo'))
    json.dump(linhas, open(os.path.join(os.path.dirname(OUT), 'semrush.demo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('semrush.demo.json (volumes sintéticos):', len(linhas), 'palavras')
