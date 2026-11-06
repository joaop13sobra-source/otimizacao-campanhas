"""Leitura de exports (CSV/XLSX), números, datas e normalização de texto. Usado pelos outros scripts."""
import csv, io, re, unicodedata
from datetime import datetime
from pathlib import Path

MESES = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7,
         'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}


def norm(s):
    """Minúsculo, sem acento, sem aspas/colchetes, com + _ - tratados como espaço. Chave de cruzamento de UTM."""
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'["\'\[\]]', ' ', s)
    s = re.sub(r'[+_\-]', ' ', s)
    return ' '.join(s.split())


def num(valor, formato='auto'):
    """Converte dinheiro/número. formato: 'br' (1.234,56), 'us' (1,234.56) ou 'auto'. Vazio e '--' viram 0.

    O export do Meta costuma vir em 'us' e o do Google em 'br': declare no config, não confie no 'auto'
    para valores como 1.183, que são ambíguos.
    """
    if isinstance(valor, (int, float)):
        return float(valor)
    s = re.sub(r'[^\d,.\-]', '', str(valor or ''))
    if not s or s in ('-', '--', '.', ','):
        return 0.0
    if formato == 'br':
        s = s.replace('.', '').replace(',', '.')
    elif formato == 'us':
        s = s.replace(',', '')
    elif ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    return float(s)


def data(valor):
    """Aceita ISO, dd/mm/aaaa, dd/mm/aaaaHH:MM:SS (sem espaço) e '1 de setembro de 2025 às 10:46'. None se não entender."""
    s = ' '.join(str(valor or '').split())
    if not s:
        return None
    m = re.match(r'(\d{1,2}) de (\w+) de (\d{4})(?: às (\d{1,2}):(\d{2}))?', s, re.I)
    if m and m.group(2).lower() in MESES:
        return datetime(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1)), int(m.group(4) or 0), int(m.group(5) or 0))
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})\s*(\d{2}:\d{2}(?::\d{2})?)?', s)
    if m:
        h = (m.group(4) or '00:00').split(':')
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), int(h[0]), int(h[1]), int(h[2]) if len(h) > 2 else 0)
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).replace(tzinfo=None)
    except ValueError:
        return None


def _decodificar(caminho):
    b = Path(caminho).expanduser().read_bytes()
    if b[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return b.decode('utf-16')
    for enc in ('utf-8-sig', 'latin-1'):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError(f'Encoding desconhecido em {caminho}')


def _linhas_csv(caminho):
    txt = _decodificar(caminho)
    amostra = '\n'.join(txt.splitlines()[:8])
    delim = max(',;\t', key=amostra.count)
    return list(csv.reader(io.StringIO(txt), delimiter=delim))


def _linhas_xlsx(caminho, aba=None):
    import openpyxl
    wb = openpyxl.load_workbook(Path(caminho).expanduser(), read_only=True, data_only=True)
    ws = wb[aba] if aba else wb.worksheets[0]
    return [['' if c is None else c for c in r] for r in ws.iter_rows(values_only=True)]


def tabela(caminho, colunas, aba=None):
    """Lê o arquivo e devolve dicionários só com as colunas pedidas ({nome_interno: 'Nome no arquivo'}).

    Acha o cabeçalho sozinho (o export do Google traz título e período antes dele) e descarta toda linha com
    'Total:' em QUALQUER célula: no relatório de palavras-chave a marca não fica na primeira coluna, e somar
    esses subtotais infla o investimento várias vezes.
    """
    bruto = _linhas_xlsx(caminho, aba) if str(caminho).lower().endswith(('.xlsx', '.xlsm')) else _linhas_csv(caminho)
    alvo = {norm(v) for v in colunas.values() if v}
    idx_cab = next((i for i, r in enumerate(bruto) if alvo <= {norm(c) for c in r}), None)
    if idx_cab is None:
        raise ValueError(f'{caminho}: não achei as colunas {sorted(colunas.values())} em nenhuma linha')
    pos = {norm(c): i for i, c in enumerate(bruto[idx_cab])}
    saida = []
    for r in bruto[idx_cab + 1:]:
        if not any(str(c).strip() for c in r) or any(str(c).strip().lower().startswith('total') for c in r):
            continue
        saida.append({k: (r[pos[norm(v)]] if v and pos[norm(v)] < len(r) else '') for k, v in colunas.items()})
    return saida
