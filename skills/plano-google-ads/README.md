# plano-google-ads

Skill para o [Claude Code](https://claude.com/claude-code) que monta o **plano de otimização de uma conta de Google Ads (Search)**: diagnóstico do CPL, termos de pesquisa, negativas, palavras-chave, cruzamento de leads com vendas do CRM e proposta de estrutura de campanhas, tudo numa página HTML.

Ela responde, com dados:

- **Por que o CPL subiu?** (quanto é CPC mais caro e quanto é conversão menor)
- **O que negativar** e quanto isso realmente ajuda (em geral, pouco: negativa é higiene).
- **Quais palavras-chave vendem**, e quanto custa cada venda por campanha, grupo, anúncio, palavra-chave e cidade, cruzando a planilha de leads com o relatório de vendas do CRM **por telefone**.
- **Quais palavras novas** vale testar (Semrush), já separadas entre "novas" e "já na conta".
- **Como estruturar as campanhas**: grupos, palavras, correspondência, orçamento, lance, geografia, anúncios, plano de teste, metas e travas.

> A skill **não altera nada** na conta do Google Ads. Ela recomenda; a aplicação é sua.

## Como funciona

```
relatórios do Google Ads ─┐
planilha de leads  ───────┼─► analise.py ─► dados.json ─┐
relatório de vendas (CRM) ┘                              ├─► gerar_plano.py ─► index.html ─► validar_pagina.py
Semrush (opcional) ─► semrush.py ─► semrush.json ────────┤
                                  plano.json (a sua narrativa e decisões) ─┘
```

- **Números** saem de scripts e entram no texto por `{{caminho|formato}}`, então a página nunca desencontra dos dados.
- **Julgamento** (decisões por palavra-chave, estrutura, metas) fica no `plano.json`, que você escreve a partir de `assets/plano.exemplo.json`.

## Instalação

```bash
git clone https://github.com/<usuario>/plano-google-ads.git ~/.claude/skills/plano-google-ads
cd ~/.claude/skills/plano-google-ads
pip install -r requirements.txt
```

No Claude Code a skill aparece como `/plano-google-ads`. Os scripts também funcionam sozinhos, fora do Claude.

Requisitos: Python 3.9+, `pandas` e `numpy`. Para ler a planilha de leads direto do Google Sheets: `google-auth` e `google-api-python-client` (opcional; CSV exportado funciona sem). Para o print de validação: Google Chrome (opcional).

## Teste rápido (dados sintéticos)

Não precisa de nenhum dado seu:

```bash
python3 assets/demo/gerar_demo.py
python3 -I scripts/analise.py assets/config.exemplo.json --saida dados.json
python3 -I scripts/gerar_plano.py --dados dados.json --plano assets/plano.exemplo.json \
        --semrush assets/demo/semrush.demo.json --saida plano/index.html
python3 -I scripts/validar_pagina.py plano/index.html
```

Abra `plano/index.html` no navegador. Os números esperados estão em `references/exemplo-demo.md`.

## Usando com uma conta real

1. Baixe os relatórios do Google Ads (campanhas, grupos, palavras-chave, termos de pesquisa) em `.csv`: ver `references/coleta-de-dados.md`.
2. Copie `assets/config.exemplo.json` e ajuste caminhos, expressões de marca/concorrentes/cidades e o bloco `vendas` (planilha de leads, relatório do CRM, regras do que é "venda"): ver `references/formatos.md`.
3. Rode `analise.py`, leia os alertas e faça a checagem de sanidade (`SKILL.md`, passo 3).
4. (Opcional) Semrush: `SEMRUSH_API_KEY=... python3 -I scripts/semrush.py descobrir ...` e depois `volumes --plano plano.json`.
5. Escreva o `plano.json`, gere a página e valide.

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `SKILL.md` | O fluxo em 8 passos, princípios e critério de pronto |
| `scripts/` | `analise.py`, `cruzar_vendas.py`, `semrush.py`, `gerar_plano.py`, `validar_pagina.py`, `gads.py` |
| `references/` | Coleta de dados, metodologia, estrutura de campanhas, formatos, publicação, armadilhas, caso de demonstração |
| `assets/` | `config.exemplo.json`, `plano.exemplo.json` e `demo/` (dados sintéticos e o gerador) |

## Armadilhas que a skill já trata

- **Datas em vários formatos** na mesma planilha: um leitor ingênuo descarta linhas e inventa conclusões falsas. `cruzar_vendas.py` tenta todos os formatos e acusa linhas sem data.
- **CPL não é guia de corte:** a palavra mais barata por lead pode ser a mais cara por venda.
- **O status da planilha de leads não é cobertura** nem falta de venda.
- **`utm_term` costuma ser a palavra-chave, não a pesquisa do usuário.**
- **Semrush é referência:** volumes nacionais, marca local subestimada, concorrentes disfarçados de termo genérico.

Mais em `references/armadilhas.md`.

## Privacidade

Os scripts não colocam nome nem telefone na página (`validar_pagina.py` barra). Mesmo assim, **não faça commit** de `config.json`, relatórios, planilhas ou `dados.json` de clientes reais: o `.gitignore` já cobre os nomes padrão. Os dados deste repositório são todos sintéticos.

## Licença

Nenhuma licença foi definida ainda. Sem uma licença, o código pode ser lido, mas não reutilizado legalmente. Defina uma (por exemplo MIT) antes de incentivar o reuso.
