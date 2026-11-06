"""Leitura de relatórios exportados do Google Ads (CSV pt-BR).

Formato do export: linha 1 = título do relatório, linha 2 = período, linha 3 = cabeçalho,
depois os dados e linhas "Total: ..." no fim. Números: ponto = milhar, vírgula = decimal.
"""
import csv
import io
import re

import numpy as np
import pandas as pd


def num(x):
    """'1.208' -> 1208.0 | '1933,46' -> 1933.46 | '23,80%' -> 23.8 | ' --', '< 10%' -> NaN."""
    if x is None:
        return np.nan
    s = str(x).strip().replace('%', '')
    if s in ('', '--', 'nan') or s.startswith('<') or s.startswith('>'):
        return np.nan
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return np.nan


def _ler_texto(path):
    for enc in ('utf-8-sig', 'utf-16', 'latin-1'):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeError, UnicodeDecodeError):
            continue
    raise ValueError(f'não consegui ler {path}')


def read_report(path):
    """Devolve (DataFrame de strings sem as linhas Total, texto do período)."""
    linhas = _ler_texto(path).splitlines()
    periodo = linhas[1].strip() if len(linhas) > 1 else ''
    corpo = '\n'.join(linhas[2:])
    # exports com tab (TSV) aparecem às vezes: detectar o separador
    sep = '\t' if corpo.split('\n', 1)[0].count('\t') > corpo.split('\n', 1)[0].count(',') else ','
    df = pd.read_csv(io.StringIO(corpo), sep=sep, dtype=str, quoting=csv.QUOTE_MINIMAL).fillna('')
    primeira = df.columns[0]
    df = df[~df[primeira].str.startswith('Total')].reset_index(drop=True)
    return df, periodo


def pick(df, *candidatos):
    """Primeiro nome de coluna existente (ignora maiúsculas/acentos de espaço)."""
    mapa = {c.strip().lower(): c for c in df.columns}
    for c in candidatos:
        if c.strip().lower() in mapa:
            return mapa[c.strip().lower()]
    return None


def numerica(df, *candidatos):
    """Série numérica da primeira coluna que existir; NaN se nenhuma."""
    c = pick(df, *candidatos)
    if c is None:
        return pd.Series(np.nan, index=df.index)
    return df[c].map(num)


def norm(s):
    """minúsculas, sem acento, espaços colapsados (para casar termos)."""
    s = str(s).lower().strip()
    for a, b in {'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e', 'í': 'i',
                 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c'}.items():
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s)


def brl(x, d=2):
    if x is None or x != x:
        return '-'
    return 'R$ ' + f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
