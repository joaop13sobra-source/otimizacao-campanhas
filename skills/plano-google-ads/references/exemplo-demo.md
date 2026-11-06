# Caso de demonstração (NetExemplo, dados sintéticos)

O repositório traz dados **inventados** (operadora fictícia "NetExemplo") nos formatos reais de entrada, em `assets/demo/dados/`. Eles são gerados por `assets/demo/gerar_demo.py` com semente fixa: o resultado é sempre o mesmo, então os números abaixo servem para **testar se os scripts continuam corretos**. Nada aqui vem de cliente real.

```bash
python3 assets/demo/gerar_demo.py                       # recria os arquivos sintéticos
python3 -I scripts/analise.py assets/config.exemplo.json --saida dados.json
python3 -I scripts/gerar_plano.py --dados dados.json --plano assets/plano.exemplo.json \
         --semrush assets/demo/semrush.demo.json --saida plano/index.html
python3 -I scripts/validar_pagina.py plano/index.html
```
(Rode da raiz do repositório. Os volumes do Semrush do demo são sintéticos; com chave real, use `semrush.py`.)

## Números de referência (saída de `analise.py`)

| Item | Valor |
|---|---|
| Custo / conversões / CPL | R$ 3.775,20 / 226.3 / **R$ 16,69** |
| CPC / conversão por clique | R$ 3,85 / 23,1% |
| Referência (Setembro) | R$ 11,28 / R$ 3,40 / 30,1% |
| Decomposição da variação do CPL (48%) | **32%** CPC e **68%** conversão |
| Campanha de marca | R$ 1.699,20 · CPL R$ 15,12 · CPC R$ 3,05 · perde 21,7% por orçamento |
| Campanha de genéricos | R$ 2.076,00 · CPL R$ 18,23 · CPC R$ 4,91 · perde 31,3% por orçamento e 28,3% por classificação |
| Marca vazando na campanha de genéricos | R$ 163,05 (10,7% da campanha) |
| Termos visíveis | R$ 2.796,53 (74% do gasto) |
| Negativas Tier 1 / com concorrentes | -3,5% (CPL R$ 18,64) / -5,9% (CPL R$ 18,17) |
| Palavras-chave | 12 (12 em ampla), 11 com gasto |

Temas de busca (custo · CPL):

| Tema | Custo | CPL |
|---|---|---|
| Marca pura | R$ 756,90 | R$ 19,21 |
| Marca + suporte/cliente | R$ 63,73 | R$ 17,22 |
| Marca + contato (WhatsApp/telefone) | R$ 310,12 | R$ 16,24 |
| Marca + cidade/bairro | R$ 300,09 | R$ 17,97 |
| Concorrentes / outras operadoras | R$ 220,42 | R$ 66,79 |
| Genérico + cidade/bairro | R$ 253,08 | R$ 20,92 |
| Genérico sem cidade / outros | R$ 892,19 | R$ 17,67 |

## Lead → venda (janela 01 a 17/10, gasto escalado por 0.886)

| Item | Valor |
|---|---|
| Linhas lidas da planilha / sem data | 222 / **0** (o arquivo tem dois formatos de data de propósito: `62` no 1º e `160` no 2º) |
| Vendas do CRM achadas na planilha | **38 de 44** (86%) |
| Leads únicos / venda / desqualificado / em aberto | 198 / 38 / 62 / 98 (68 sem registro no CRM) |
| Taxa de venda por lead | marca 18,6% · genéricos 19,8% |
| Custo por venda estimado | marca R$ 84 · genéricos R$ 92 · conta R$ 88 |
| Por palavra-chave (≥ 15 leads) | "netexemplo" R$ 79 (18/92), "servico internet" R$ 59 (6/16), "internet residencial" R$ 101 (5/37), "provedor de internet" R$ 127 (4/28), "internet fibra regional" R$ 100 (4/18) |
| Anúncio por grupo (≥ 20 leads) | Internet Fibra: ad02 32% (9/28); Internet Fibra: ad01 8% (2/24); Marca: ad03 24% (7/29); Marca: ad01 18% (7/38); Marca: ad02 13% (4/30) |

## O que o demo ensina

- **Decida por custo por venda, não por CPL:** compare a tabela de palavras-chave (CPL) com o custo por venda: a ordem muda.
- **Negativas são higiene:** o cenário mais amplo mexe poucos pontos percentuais no CPL.
- **Concorrentes** custam mais por lead e convertem pouco (Tier 2: validar com o CRM antes de negativar).
- **Marca vazando** para a campanha de genéricos deve ser corrigida com negativa de marca exata nas demais campanhas.
- **Dois formatos de data** na planilha: `sem_data` precisa ser 0 (ver `armadilhas.md`).
