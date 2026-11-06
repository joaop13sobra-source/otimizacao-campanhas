"""Escreve um diagnóstico (lista de elementos JSON) numa aba VAZIA de um Google Doc, no formato do Doc de comitê.

Uso:  python3 -I build_doc.py <documentId> <tabId> "<título exato da aba>" <elementos.json>
Elementos (gerados por um script de conteúdo por cliente, ver exemplo-conteudo.py):
  {"k": "p", "style": "H2"|"H3"|"NORMAL", "bullet": bool, "runs": [{"t": texto, "b": negrito, "i": itálico, "link": url}]}
  {"k": "t", "rows": [[cabeçalho...], [linha...]], "widths": [pt por coluna]}
  {"k": "rule"}   linha divisória final (borda inferior num parágrafo vazio)
Credencial: conta de serviço em GOOGLE_SERVICE_ACCOUNT_JSON (padrão ~/.config/google/service-account.json), com Docs API ativa;
o Doc precisa estar compartilhado com ela ou editável por link.
"""
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

DOC, TAB, TAB_TITLE, ELEMS = sys.argv[1:5]
CRED = os.path.expanduser(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '~/.config/google/service-account.json'))
cr = service_account.Credentials.from_service_account_file(CRED,
                                                           scopes=['https://www.googleapis.com/auth/documents'])
svc = build('docs', 'v1', credentials=cr)
E = json.load(open(ELEMS))
GREY = {'color': {'rgbColor': {'red': 0.6, 'green': 0.6, 'blue': 0.6}}}
FONT = {'fontFamily': 'Inter'}

def find(tabs, tid):
    for t in tabs:
        if t['tabProperties']['tabId'] == tid: return t
        r = find(t.get('childTabs', []), tid)
        if r: return r

def read():
    doc = svc.documents().get(documentId=DOC, includeTabsContent=True).execute()
    t = find(doc['tabs'], TAB)
    assert t['tabProperties']['title'] == TAB_TITLE, t['tabProperties']
    return doc['revisionId'], t['documentTab']['body']['content']

def send(reqs, rev):
    for i in range(0, len(reqs), 400):
        r = svc.documents().batchUpdate(documentId=DOC, body={'requests': reqs[i:i + 400], 'writeControl': {'requiredRevisionId': rev}}).execute()
        rev = r['writeControl']['requiredRevisionId']
    return rev

def rng(a, b): return {'startIndex': a, 'endIndex': b, 'tabId': TAB}

def empty(e): return 'paragraph' in e and ''.join(x.get('textRun', {}).get('content', '') for x in e['paragraph']['elements']) == '\n' and 'borderBottom' not in e['paragraph']['paragraphStyle']
def ins_point(C):
    """Início do primeiro parágrafo vazio da sequência de vazios no fim da aba."""
    j = len(C) - 1
    while j - 1 >= 1 and empty(C[j - 1]): j -= 1
    return C[j]['startIndex']

rev, C = read()
if len(C) > 2 or C[-1]['endIndex'] > 2:
    sys.exit(f'Aba {TAB_TITLE} não está vazia — abortando')
parent = None

def para_reqs(group, start):
    """Insere um bloco de parágrafos em start e devolve requests de texto + estilo."""
    text = ''.join(''.join(r['t'] for r in p['runs']) + '\n' for p in group)
    reqs = [{'insertText': {'location': {'index': start, 'tabId': TAB}, 'text': text}}]
    pos = start
    for p in group:
        pl = sum(len(r['t']) for r in p['runs']) + 1
        st = {'H2': 'HEADING_2', 'H3': 'HEADING_3'}.get(p['style'], 'NORMAL_TEXT')
        ps = {'namedStyleType': st}
        fields = 'namedStyleType'
        if st == 'NORMAL_TEXT':
            ps.update(spaceAbove={'magnitude': 12, 'unit': 'PT'}, spaceBelow={'magnitude': 12, 'unit': 'PT'}); fields += ',spaceAbove,spaceBelow'
        elif st == 'HEADING_2':
            ps.update(spaceBelow={'magnitude': 4, 'unit': 'PT'}); fields += ',spaceBelow'
        reqs.append({'updateParagraphStyle': {'range': rng(pos, pos + pl), 'paragraphStyle': ps, 'fields': fields}})
        size = {'H2': 17, 'H3': 13}.get(p['style'], 14)
        q = pos
        for r in p['runs']:
            ts = {'weightedFontFamily': FONT, 'fontSize': {'magnitude': size, 'unit': 'PT'},
                  'bold': bool(r.get('b')) or p['style'] in ('H2', 'H3'), 'italic': bool(r.get('i'))}
            f = 'weightedFontFamily,fontSize,bold,italic'
            if r.get('link'):
                ts['link'] = {'url': r['link']}; f += ',link'
            if r['t']:
                reqs.append({'updateTextStyle': {'range': rng(q, q + len(r['t'])), 'textStyle': ts, 'fields': f}})
            q += len(r['t'])
        if p['bullet']:
            reqs.append({'createParagraphBullets': {'range': rng(pos, pos + pl - 1), 'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'}})
        pos += pl
    return reqs

def table(rows, widths):
    global rev
    _, C = read()
    at = ins_point(C) - 1  # newline do parágrafo anterior: a tabela entra sem parágrafo vazio antes
    rev = send([{'insertTable': {'rows': len(rows), 'columns': len(rows[0]), 'location': {'index': at, 'tabId': TAB}}}], rev)
    rev, C = read()
    tb = [e for e in C if 'table' in e and e['startIndex'] >= at][0]
    reqs = []
    cells = [(ri, ci, c) for ri, r in enumerate(tb['table']['tableRows']) for ci, c in enumerate(r['tableCells'])]
    for ri, ci, c in reversed(cells):
        txt = rows[ri][ci]
        if txt:
            reqs.append({'insertText': {'location': {'index': c['content'][0]['startIndex'], 'tabId': TAB}, 'text': txt}})
    rev = send(reqs, rev)
    rev, C = read()
    tb = [e for e in C if 'table' in e and e['startIndex'] >= at][0]
    ts0 = tb['startIndex']
    reqs = [{'updateTableColumnProperties': {'tableStartLocation': {'index': ts0, 'tabId': TAB}, 'columnIndices': [i],
             'tableColumnProperties': {'widthType': 'FIXED_WIDTH', 'width': {'magnitude': w, 'unit': 'PT'}}, 'fields': 'widthType,width'}} for i, w in enumerate(widths)]
    bd = {'color': GREY, 'width': {'magnitude': 0.5, 'unit': 'PT'}, 'dashStyle': 'SOLID'}
    pad = {'magnitude': 5, 'unit': 'PT'}
    reqs.append({'updateTableCellStyle': {'tableRange': {'tableCellLocation': {'tableStartLocation': {'index': ts0, 'tabId': TAB}, 'rowIndex': 0, 'columnIndex': 0},
                                                         'rowSpan': len(rows), 'columnSpan': len(rows[0])},
                                          'tableCellStyle': {'borderLeft': bd, 'borderRight': bd, 'borderTop': bd, 'borderBottom': bd,
                                                             'paddingLeft': pad, 'paddingRight': pad, 'paddingTop': pad, 'paddingBottom': pad},
                                          'fields': 'borderLeft,borderRight,borderTop,borderBottom,paddingLeft,paddingRight,paddingTop,paddingBottom'}})
    reqs.append({'updateTableRowStyle': {'tableStartLocation': {'index': ts0, 'tabId': TAB}, 'rowIndices': list(range(len(rows))),
                                         'tableRowStyle': {'minRowHeight': {'magnitude': 26.5, 'unit': 'PT'}}, 'fields': 'minRowHeight'}})
    for ri, r in enumerate(tb['table']['tableRows']):
        for c in r['tableCells']:
            a, b = c['content'][0]['startIndex'], c['content'][-1]['endIndex']
            reqs.append({'updateParagraphStyle': {'range': rng(a, b), 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'alignment': 'CENTER' if ri == 0 else 'START',
                         'spaceAbove': {'unit': 'PT'}, 'spaceBelow': {'unit': 'PT'}, 'lineSpacing': 100}, 'fields': 'namedStyleType,alignment,spaceAbove,spaceBelow,lineSpacing'}})
            if b - 1 > a:
                reqs.append({'updateTextStyle': {'range': rng(a, b - 1), 'textStyle': {'weightedFontFamily': FONT, 'fontSize': {'magnitude': 14, 'unit': 'PT'},
                             'bold': ri == 0, 'italic': False}, 'fields': 'weightedFontFamily,fontSize,bold,italic'}})
    rev = send(reqs, rev)

i = 0
while i < len(E):
    e = E[i]
    if e['k'] == 'p':
        grp = []
        while i < len(E) and E[i]['k'] == 'p':
            grp.append(E[i]); i += 1
        rev, C = read()
        rev = send(para_reqs(grp, ins_point(C)), rev)
    elif e['k'] == 't':
        table(e['rows'], e['widths']); i += 1
    else:  # linha divisória: borda inferior num parágrafo vazio
        rev, C = read(); at = ins_point(C)
        rev = send([{'insertText': {'location': {'index': at, 'tabId': TAB}, 'text': '\n'}},
                    {'updateParagraphStyle': {'range': rng(at, at + 1), 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT',
                     'borderBottom': {'color': GREY, 'width': {'magnitude': 1, 'unit': 'PT'}, 'padding': {'magnitude': 1, 'unit': 'PT'}, 'dashStyle': 'SOLID'}},
                     'fields': 'namedStyleType,borderBottom'}}], rev)
        i += 1
    print('ok', i, '/', len(E), flush=True)
rev, C = read()
# apaga os parágrafos vazios que sobraram depois da linha divisória
k = max((i for i, e in enumerate(C) if 'paragraph' in e and 'borderBottom' in e['paragraph']['paragraphStyle']), default=None)
if k is not None and C[-1]['endIndex'] - 1 > C[k]['endIndex']:
    rev = send([{'deleteContentRange': {'range': rng(C[k]['endIndex'], C[-1]['endIndex'] - 1)}}], rev)
rev, C = read()
print('fim', C[-1]['endIndex'], 'elementos', len(C))
