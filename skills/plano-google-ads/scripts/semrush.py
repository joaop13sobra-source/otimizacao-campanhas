#!/usr/bin/env python3
"""Cliente mínimo da API do Semrush para descobrir palavras-chave de Search (banco br).

    python3 -I semrush.py unidades
    python3 -I semrush.py descobrir --sementes "internet fibra;internet residencial" --limite 40 --saida descoberta.json
    python3 -I semrush.py volumes   --termos "netexemplo;disponibilidade internet fibra" --saida volumes.json
    python3 -I semrush.py volumes   --plano plano.json --saida volumes.json      # coleta sozinho todas as palavras citadas no plano
    python3 -I semrush.py filtrar   --config config.json [--descoberta descoberta.json] [--volumes volumes.json] --saida semrush.json

A chave NUNCA é impressa. Ordem de busca: variável SEMRUSH_API_KEY, depois o arquivo indicado em --chave-arquivo
(ou ~/.config/semrush/api-key.txt), que guarda só a chave ou "Apikey <chave>".
Cada linha devolvida gasta unidades (phrase_fullsearch ~40/linha): confira `unidades` antes e limite as sementes.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gads import norm

API = 'https://api.semrush.com/'
ARQ_PADRAO = '~/.config/semrush/api-key.txt'


def chave(arquivo=None):
    k = os.environ.get('SEMRUSH_API_KEY')
    if k:
        return k.strip()
    for a in ([arquivo] if arquivo else []) + [ARQ_PADRAO]:
        p = os.path.expanduser(a)
        if os.path.exists(p):
            m = re.search(r'(?:Apikey\s+|key=)?([A-Za-z0-9]{32})', open(p, encoding='utf-8').read())
            if m:
                return m.group(1)
    sys.exit('Chave do Semrush não encontrada (SEMRUSH_API_KEY, --chave-arquivo ou ' + ARQ_PADRAO + ').')


def chamar(params, arquivo=None):
    p = dict(params)
    p['key'] = chave(arquivo)
    url = API + '?' + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            return r.read().decode('utf-8', 'replace')
    except Exception as e:  # nunca vazar a chave na mensagem
        return 'ERROR ' + str(e).replace(p['key'], '<chave>')


def unidades(arquivo=None):
    url = 'https://www.semrush.com/users/countapiunits.html?key=' + chave(arquivo)
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode().strip()


def parse(txt):
    linhas = [l for l in txt.strip().splitlines() if l.strip()]
    if not linhas or linhas[0].startswith('ERROR'):
        return None, linhas[:1]
    cab = linhas[0].split(';')
    return cab, [dict(zip(cab, l.split(';'))) for l in linhas[1:]]


COLS = 'Ph,Nq,Cp,Co,Kd,In'
RENOMEAR = {'Keyword': 'kw', 'Search Volume': 'vol', 'CPC': 'cpc', 'Competition': 'co',
            'Keyword Difficulty Index': 'kd', 'Intent': 'intent'}


def _linhas(rows):
    out = []
    for r in rows:
        d = {RENOMEAR.get(k, k): v for k, v in r.items()}
        for c in ('vol', 'cpc', 'co', 'kd'):
            try:
                d[c] = float(d.get(c, ''))
            except ValueError:
                d[c] = None
        out.append(d)
    return out


def descobrir(sementes, limite, banco='br', arquivo=None):
    res = {}
    for s in sementes:
        txt = chamar({'type': 'phrase_fullsearch', 'phrase': s, 'database': banco, 'display_limit': limite,
                      'display_sort': 'nq_desc', 'export_columns': COLS}, arquivo)
        cab, rows = parse(txt)
        res[s] = _linhas(rows) if cab else []
        print(f'{s:34s} {len(res[s]):3d} linhas' + ('' if cab else f' | {rows}'))
        time.sleep(0.3)
    return res


def volumes(termos, banco='br', arquivo=None):
    out = []
    for i in range(0, len(termos), 40):  # phrase_these aceita lotes
        txt = chamar({'type': 'phrase_these', 'phrase': ';'.join(termos[i:i + 40]), 'database': banco,
                      'export_columns': COLS}, arquivo)
        cab, rows = parse(txt)
        if cab:
            out += _linhas(rows)
    return out


INTENCAO = {'0': 'Comercial', '1': 'Informacional', '2': 'Navegacional', '3': 'Transacional'}


def intencao(x):
    return ' / '.join(INTENCAO.get(i.strip(), '') for i in str(x or '').split(',') if i.strip()) or '-'


def coletar_palavras(plano):
    """Todas as palavras-chave citadas no plano.json (novas_palavras e estrutura), sem repetir."""
    achadas, vistas = [], set()

    def add(lista):
        for k in lista:
            if norm(k) not in vistas:
                vistas.add(norm(k))
                achadas.append(k)
    for g in plano.get('novas_palavras', {}).get('grupos', []):
        add(g.get('palavras', []))
    for c in plano.get('estrutura', {}).get('campanhas', []):
        for g in c.get('grupos', []):
            add(g.get('palavras', []))
    return achadas


def filtrar(cfg, descoberta, vols=None):
    """Separa o que interessa: tira concorrentes, ruído informacional/suporte e cidades fora da área.

    Usa as regex do config (marca, concorrentes, fora_area, cidades) + RUIDO padrão. Marca e cidades
    viram grupos próprios; nada é descartado em silêncio (cada linha sai com 'classe').
    """
    R = cfg.get('regex', {})
    ruido = R.get('ruido', r'trabalhe conosco|vagas|emprego|como |o que e|e bom|qual |quantos|mbps|teste|velocidade|grati|gratuit|'
                  r'segunda via|2 via|boleto|telefone|0800|numero|whatsapp|reclama|cancelar|fatura|app\b|aplicativo|wifi|wi-fi|roteador|'
                  r'modem|senha|chip|celular|rural|empresarial|cnpj|prefeitura|escola|governo')
    marca, conc, fora = R.get('marca', ''), R.get('concorrentes', ''), R.get('fora_area', '')
    cidades = '|'.join(R.get('cidades', {}).values())
    vistos = {}
    for sem, rows in descoberta.items():
        for r in rows:
            vistos.setdefault(r['kw'], dict(r, semente=sem))
    for r in (vols or []):
        vistos.setdefault(r['kw'], dict(r, semente='(volumes)'))
    saida = []
    for kwd, r in vistos.items():
        n = norm(kwd)
        t = lambda rx: bool(rx) and re.search(rx, n) is not None
        if t(marca):
            classe = 'marca'
        elif t(conc):
            classe = 'concorrente'
        elif t(fora) and not t(cidades):
            classe = 'fora_da_area'
        elif t(ruido):
            classe = 'ruido'
        elif t(cidades):
            classe = 'local'
        else:
            classe = 'generico'
        r = dict(r, n=n, classe=classe, intencao=intencao(r.get('intent')))
        saida.append(r)
    saida.sort(key=lambda r: -(r['vol'] or 0))
    return saida


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for nome in ('unidades', 'descobrir', 'volumes', 'filtrar'):
        s = sub.add_parser(nome)
        s.add_argument('--chave-arquivo')
        s.add_argument('--saida')
        if nome == 'descobrir':
            s.add_argument('--sementes', required=True)
            s.add_argument('--limite', type=int, default=40)
        if nome == 'volumes':
            s.add_argument('--termos')
            s.add_argument('--plano')
        if nome == 'filtrar':
            s.add_argument('--config', required=True)
            s.add_argument('--descoberta')
            s.add_argument('--volumes')
    a = ap.parse_args()
    if a.cmd == 'unidades':
        print('unidades restantes:', unidades(a.chave_arquivo))
        return
    if a.cmd == 'descobrir':
        res = descobrir([x.strip() for x in a.sementes.split(';') if x.strip()], a.limite, arquivo=a.chave_arquivo)
    elif a.cmd == 'volumes':
        termos = ([x.strip() for x in a.termos.split(';') if x.strip()] if a.termos
                  else coletar_palavras(json.load(open(a.plano, encoding='utf-8'))) if a.plano else [])
        if not termos:
            sys.exit('Informe --termos ou --plano.')
        print(f'consultando {len(termos)} palavras (≈ {len(termos) * 10} unidades)')
        res = volumes(termos, arquivo=a.chave_arquivo)
    else:
        cfg = json.load(open(a.config, encoding='utf-8'))
        res = filtrar(cfg, json.load(open(a.descoberta, encoding='utf-8')) if a.descoberta else {},
                      json.load(open(a.volumes, encoding='utf-8')) if a.volumes else None)
        cont = {}
        for r in res:
            cont[r['classe']] = cont.get(r['classe'], 0) + 1
        print('classificação:', cont)
    if a.saida:
        json.dump(res, open(a.saida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('ok ->', a.saida)
    print('unidades restantes:', unidades(a.chave_arquivo))


if __name__ == '__main__':
    main()
