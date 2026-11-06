#!/usr/bin/env python3
"""Portão de qualidade da página gerada: acusa o que não pode ir ao ar.

    python3 -I validar_pagina.py index.html

Falha (exit 1) se achar: marcadores de template não resolvidos, NaN/undefined/Infinity, telefone,
e-mail ou CPF no texto (dado pessoal), links relativos para arquivos que não existem ao lado da página.
Avisos: seções vazias e números com ponto decimal (deveriam ter vírgula).
"""
import os
import re
import sys

caminho = sys.argv[1]
s = open(caminho, encoding='utf-8').read()
corpo = re.sub(r'<style.*?</style>', '', s, flags=re.S)
texto = re.sub(r'<[^>]+>', ' ', corpo)
erros, avisos = [], []

if '[[?' in s:
    erros.append('marcador de template não resolvido: ' + ', '.join(sorted(set(re.findall(r'\[\[\?[^\]]+\]\]', s)))[:5]))
for p in ('NaN', 'undefined', 'Infinity'):
    if re.search(rf'\b{p}\b', texto):
        erros.append(f'"{p}" aparece no texto da página')
if re.search(r'\(?\b\d{2}\)?[ -]?9?\d{4}[- ]?\d{4}\b', texto):
    erros.append('há sequência parecida com telefone no texto (dado pessoal)')
if re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', texto):
    erros.append('há e-mail no texto (dado pessoal)')
if re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', texto):
    erros.append('há CPF no texto')
base = os.path.dirname(os.path.abspath(caminho))
for ref in sorted(set(re.findall(r'(?:src|href)="([^"#:]+)"', s))):
    if ref.startswith(('http', '//', 'mailto')):
        continue
    alvo = os.path.normpath(os.path.join(base, ref))
    if not os.path.exists(alvo):
        avisos.append(f'link relativo sem arquivo ao lado da página: {ref} (ok se o arquivo for copiado no deploy)')
for sec in re.findall(r'<section id="(\w+)">(.*?)</section>', s, flags=re.S):
    if len(re.sub(r'<[^>]+>', '', sec[1]).strip()) < 80:
        avisos.append(f'seção "{sec[0]}" quase vazia')
if re.search(r'\b\d+\.\d+%', texto):
    avisos.append('há percentuais com ponto decimal (ex.: 21.7%): usar vírgula')

print(f'{caminho}: {len(s):,} bytes, {len(re.findall("<section", s))} seções')
for a in avisos:
    print('  aviso:', a)
for e in erros:
    print('  ERRO:', e)
sys.exit(1 if erros else 0)
