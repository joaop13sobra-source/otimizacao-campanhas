"""Gera os arquivos fictícios da demonstração. Nenhum dado aqui é real. Uso: python3 -I gerar_demo.py"""
import csv, random
from pathlib import Path

random.seed(42)
AQUI = Path(__file__).resolve().parent / 'dados'
AQUI.mkdir(exist_ok=True)
ETAPAS = ['Novo Lead', 'Em Atendimento', 'MQL', 'Reunião Agendada', 'Proposta Enviada', 'Venda ganha']
MOTIVOS = ['Sem resposta', 'Fora do perfil', 'Sem orçamento', 'Escolheu concorrente', '']
META = {'Remarketing Quente': {'Lookalike 1% Compradores': ['Carrossel Depoimentos', 'Vídeo Prova Social'], 'Retargeting 7 dias': ['Oferta Limitada', 'Antes e Depois']},
        'Interesse Amplo': {'Interesse Marketing': ['Imagem Institucional', 'Vídeo Longo'], 'Interesse Negócios': ['Carrossel Produto', 'Estático Preço']},
        'Teste Replicado': {'Público A': ['Ad Replicado'], 'Público B': ['Ad Replicado']}}
GOOGLE = {'Search Marca': {'Marca Exata': ['ad01', 'ad02']}, 'Search Serviço': {'Serviço Principal': ['ad01', 'ad02'], 'Serviço Cidade': ['ad01']}, 'Display Genérico': {'Afinidade': ['ad01']}}
KW = {'Marca Exata': ['acme consultoria', 'acme telefone'], 'Serviço Principal': ['consultoria financeira', 'consultoria para empresas'], 'Serviço Cidade': ['consultoria financeira campinas'], 'Afinidade': []}
QUALIDADE = {'Remarketing Quente': .6, 'Interesse Amplo': .12, 'Teste Replicado': .3, 'Search Marca': .55, 'Search Serviço': .35, 'Display Genérico': .05}

with open(AQUI / 'meta.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Nome da campanha', 'Nome do conjunto de anúncios', 'Nome do anúncio', 'Valor usado (BRL)'])
    for c, gs in META.items():
        for g, ads in gs.items():
            for a in ads:
                w.writerow([c, g, a, f'{random.uniform(300, 1900):.2f}'])

def br(v):
    return f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

# export da UI do Google: título, período, cabeçalho na linha 3 e subtotais que não podem ser somados
with open(AQUI / 'google_anuncios.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Relatório de anúncios']); w.writerow(['1 de setembro de 2026 - 30 de setembro de 2026'])
    w.writerow(['Campanha', 'Grupo de anúncios', 'Sufixo do URL final', 'Custo'])
    tot = 0
    for c, gs in GOOGLE.items():
        for g, ads in gs.items():
            for a in ads:
                v = random.uniform(250, 1400); tot += v
                w.writerow([c, g, f'utm_source=google&utm_campaign={c.replace(" ", "-")}&utm_medium={g.replace(" ", "-")}&utm_content={a}', br(v)])
    w.writerow(['Total: Conta', '', '', br(tot)])
with open(AQUI / 'google_palavras.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Relatório de palavras-chave']); w.writerow(['1 de setembro de 2026 - 30 de setembro de 2026'])
    w.writerow(['Palavra-chave', 'Campanha', 'Grupo de anúncios', 'Tipo de corresp.', 'Custo'])
    for c, gs in GOOGLE.items():
        for g in gs:
            for k in KW[g]:
                w.writerow([k, c, g, 'Frase', br(random.uniform(60, 500))])
    w.writerow(['', '', '', 'Total: Palavras-chave', '9.999,00'])

def jornada(q):
    """Sorteia até onde o lead foi e se foi perdido."""
    fim = 1
    while fim < len(ETAPAS) - 1 and random.random() < (q if fim == 1 else .55):
        fim += 1
    perdeu = fim < len(ETAPAS) - 1 and random.random() < .55
    return ETAPAS[:fim + 1], perdeu

linhas, n = [], 0
def lead(c, g, a, fonte, termo=''):
    global n
    n += 1
    hist, perdeu = jornada(QUALIDADE.get(c, .3))
    atual = 'Venda perdida' if perdeu else hist[-1]
    linhas.append([f'Lead Demo {n:03d}', f'2026-{random.choice(["08", "09"])}-{random.randint(1, 28):02d} {random.randint(8, 20):02d}:{random.randint(0, 59):02d}:00',
                   atual, '|'.join(hist), random.choice(MOTIVOS) if perdeu else '', fonte, c, g, a, termo])

for c, gs in META.items():
    for g, ads in gs.items():
        for a in ads:
            for _ in range(random.randint(9, 34)):
                lead(c, g, a, random.choice(['Instagram_Feed', 'Facebook_Reels']))
for _ in range(9):  # anúncio replicado sem conjunto na UTM: não dá para saber qual público gerou
    lead('Teste Replicado', '', 'Ad Replicado', 'Instagram_Feed')
for c, gs in GOOGLE.items():
    for g, ads in gs.items():
        for a in ads:
            for _ in range(random.randint(8, 26)):
                lead(c, g, a, 'google', random.choice(KW[g]) if KW[g] else '')
for _ in range(4):   lead('Campanha Antiga Excluída', 'Conjunto Antigo', 'Ad Antigo', 'Instagram_Feed')  # sem gasto no período
for _ in range(3):   lead('{{campaign.name}}', '{{adset.name}}', '{{ad.name}}', 'Instagram_Feed')        # macro não substituída
for _ in range(12):  lead('', '', '', '')                                                                # sem UTM
for _ in range(2):   lead('Search Marca', 'Marca Exata', 'ad01', 'google', 'acme telefone'); linhas[-1][0] = 'Teste Interno'

with open(AQUI / 'leads.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Nome', 'Criado em', 'Etapa', 'Histórico', 'Motivo de perda', 'utm_source', 'utm_campaign', 'utm_medium', 'utm_content', 'utm_term'])
    w.writerows(linhas)
print('leads', len(linhas))
