"""Puxa do Kommo os leads do período com UTM, motivo de perda e histórico de etapas, no formato que montar_dados.py lê.

Uso:  KOMMO_SUBDOMAIN=conta KOMMO_TOKEN=... python3 -I puxar_kommo.py config.json --saida leads_normalizados.json
      python3 -I puxar_kommo.py config.json --listar-funis      (mostra funis e etapas, para confirmar a etapa de MQL)

Só leitura. O token vem do ambiente e nunca é impresso. O arquivo gerado tem nome de lead: não publique nem versione.
Regras que vieram de rodadas reais:
- A busca é por data de criação, SEM filtrar por funil: o time move lead para outros funis e o filtro perderia esses leads.
  A coorte é quem está num funil-alvo ou passou por ele (pelos eventos).
- O histórico vai até hoje, não até o fim do período: lead criado em setembro pode qualificar em outubro.
- /events aceita limit de no máximo 100; contatos são buscados de 10 em 10 ids.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

BASE = os.environ.get('KOMMO_BASE_URL') or f"https://{os.environ.get('KOMMO_SUBDOMAIN', '')}.kommo.com"
FUSO = timezone(timedelta(hours=-3))
UTMS = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term')


def get(caminho, params=None):
    url = f"{BASE}/api/v4/{caminho}?" + urllib.parse.urlencode(params or {}, doseq=True)
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['KOMMO_TOKEN']})
    for tentativa in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return None if r.status == 204 else json.loads(r.read() or b'null')
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return None
            if e.code == 429:
                time.sleep(2 * (tentativa + 1))
                continue
            sys.exit(f'Kommo respondeu {e.code} em {caminho}: confira token e subdomínio')
    sys.exit(f'Kommo limitou demais as chamadas em {caminho}')


def paginar(caminho, chave, params, limite):
    itens, pagina = [], 1
    while True:
        d = get(caminho, {**params, 'limit': limite, 'page': pagina})
        if not d:
            return itens
        itens += d['_embedded'][chave]
        pagina += 1
        time.sleep(0.25)


def campos(entidade):
    """{nome/código do campo em minúsculo: valor}. Campos de tracking vêm com field_code UTM_SOURCE etc."""
    saida = {}
    for f in entidade.get('custom_fields_values') or []:
        if f.get('values'):
            valor = f['values'][0].get('value')
            saida[str(f.get('field_name', '')).lower()] = valor
            if f.get('field_code'):
                saida[str(f['field_code']).lower()] = valor
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--saida', default='leads_normalizados.json')
    ap.add_argument('--listar-funis', action='store_true')
    a = ap.parse_args()
    if not os.environ.get('KOMMO_TOKEN'):
        sys.exit('Defina KOMMO_TOKEN (e KOMMO_SUBDOMAIN) no ambiente.')

    funis = get('leads/pipelines')['_embedded']['pipelines']
    if a.listar_funis:
        for p in funis:
            print(f"{p['id']}  {p['name']}")
            for s in sorted(p['_embedded']['statuses'], key=lambda x: x['sort']):
                print(f"   {s['sort']:>6}  {s['id']:>10}  {s['name']}")
        return

    cfg = json.load(open(a.config))
    K = cfg['kommo']
    alvo = set(K['funis'])
    nome_etapa = {(p['id'], s['id']): s['name'] for p in funis if p['id'] in alvo for s in p['_embedded']['statuses']}
    ini = datetime.fromisoformat(cfg['periodo']['inicio']).replace(tzinfo=FUSO)
    fim = datetime.fromisoformat(cfg['periodo']['fim']).replace(tzinfo=FUSO) + timedelta(days=1)

    brutos = paginar('leads', 'leads', {'filter[created_at][from]': int(ini.timestamp()), 'filter[created_at][to]': int(fim.timestamp()) - 1,
                                        'with': 'contacts,loss_reason'}, 250)
    print('leads no período:', len(brutos))
    ids = {l['id'] for l in brutos}
    eventos = paginar('events', 'events', {'filter[type][]': ['lead_status_changed'], 'filter[entity]': 'lead',
                                           'filter[created_at][from]': int(ini.timestamp())}, 100)
    print('eventos de etapa:', len(eventos))
    hist = {}
    for e in eventos:
        if e['entity_id'] in ids:
            for lado in ('value_before', 'value_after'):
                for v in e.get(lado) or []:
                    ls = v.get('lead_status')
                    if ls and (ls['pipeline_id'], ls['id']) in nome_etapa:
                        hist.setdefault(e['entity_id'], []).append(nome_etapa[(ls['pipeline_id'], ls['id'])])

    contatos = {}
    if K.get('utm_no_contato'):
        cids = sorted({c['id'] for l in brutos for c in l.get('_embedded', {}).get('contacts', [])})
        for i in range(0, len(cids), 10):
            d = get('contacts', {'filter[id][]': cids[i:i + 10]})
            for c in (d or {'_embedded': {'contacts': []}})['_embedded']['contacts']:
                contatos[c['id']] = campos(c)
            time.sleep(0.25)

    campo_motivo = str(K.get('campo_motivo_perda', '')).lower()
    leads = []
    for l in brutos:
        atual = nome_etapa.get((l['pipeline_id'], l['status_id']), '')
        if not atual and l['id'] not in hist:
            continue  # nunca passou por um funil-alvo
        cf = campos(l)
        if K.get('utm_no_contato'):
            for c in l.get('_embedded', {}).get('contacts', []):
                cf = {**contatos.get(c['id'], {}), **{k: v for k, v in cf.items() if v}}
        motivos = l.get('_embedded', {}).get('loss_reason') or []
        motivo = cf.get(campo_motivo) if campo_motivo else (motivos[0]['name'] if motivos else '')
        leads.append({'id': l['id'], 'nome': l.get('name') or '', 'criado_em': datetime.fromtimestamp(l['created_at'], FUSO).strftime('%Y-%m-%d %H:%M:%S'),
                      'etapa_atual': atual, 'historico': sorted(set(hist.get(l['id'], []))), 'motivo_perda': motivo or '',
                      'venda_valor': l.get('price') or 0, **{u: cf.get(u) or '' for u in UTMS}})
    json.dump(leads, open(a.saida, 'w'), ensure_ascii=False, indent=1)
    print(f'{len(leads)} leads na coorte gravados em {a.saida} (tem dado pessoal, não publique)')


if __name__ == '__main__':
    main()
