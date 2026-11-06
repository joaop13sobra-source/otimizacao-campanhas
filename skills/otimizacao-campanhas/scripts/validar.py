"""Valida o dashboard antes de publicar: placeholders, dado pessoal e execução real do JavaScript no Chrome headless.

Uso:  python3 -I validar.py deploy/index.html

Ler o código não basta: um bug de ordem de declaração já quebrou um dashboard inteiro sem nenhum erro visível.
O motor grava data-render-ok no <html> só depois de rodar até o fim; é isso que este script confere.
"""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

CANDIDATOS = [os.environ.get('CHROME_PATH'), '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser'), shutil.which('chrome')]


def main():
    arq = Path(sys.argv[1]).resolve()
    h = arq.read_text(encoding='utf-8')
    erros = []
    faltando = sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', h)))
    if faltando:
        erros.append(f'placeholders sem preencher: {faltando}')
    dados = '\n'.join(l for l in h.splitlines() if re.match(r'const [A-Z_]+ = ', l))
    if re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', dados):
        erros.append('possível e-mail nos dados embutidos')
    if re.search(r'\b(?:\+?55\s?)?\(?\d{2}\)?\s?9\d{4}-?\d{4}\b', dados):
        erros.append('possível telefone nos dados embutidos')

    chrome = next((c for c in CANDIDATOS if c and Path(c).exists()), None)
    if not chrome:
        print('AVISO: Chrome não encontrado (defina CHROME_PATH). JavaScript NÃO foi executado.')
    else:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([chrome, '--headless=new', '--disable-gpu', f'--user-data-dir={tmp}', '--virtual-time-budget=4000', '--dump-dom', arq.as_uri()],
                               capture_output=True, text=True, timeout=120)
        dom = r.stdout
        if 'data-render-ok="1"' not in dom:
            erros.append('o JavaScript não rodou até o fim no Chrome (abra o console do navegador para ver o erro)')
        else:
            vazios = [k for k in ('kpi-invest', 'kpi-g-leads', 'kpi-lost') if re.search(rf'id="{k}"[^>]*></', dom)]
            if vazios:
                erros.append(f'KPIs vazios: {vazios}')
            if re.search(r'>[^<]*(NaN|Infinity|undefined)[^<]*<', dom.split('<script')[0]):
                erros.append('NaN/Infinity/undefined visível na página')
    if erros:
        print('REPROVADO:')
        for e in erros:
            print(' -', e)
        sys.exit(1)
    print('OK:', arq)


if __name__ == '__main__':
    main()
