---
name: plano-google-ads
description: Monta o plano de otimização de uma conta de Google Ads (Search) de um cliente a partir dos relatórios do Google Ads, da planilha de leads e do relatório de vendas do CRM. Entrega diagnóstico do CPL (CPC × conversão por clique), campanhas e grupos, termos de pesquisa por intenção, negativas por risco, palavras-chave com decisão, cruzamento de leads com vendas por telefone (custo por venda por campanha, grupo, anúncio, palavra-chave e cidade), palavras novas do Semrush e a estrutura de campanhas recomendada (grupos, palavras, correspondência, orçamento, lance, geografia) com plano de teste e metas. Sai como página HTML (tema branco e vermelho) que pode ser publicada em um link único por cliente. Use quando pedirem "plano para reduzir o CPL", "analisar a conta do Google Ads", "estrutura de campanhas", "o que negativar", "palavras-chave novas", "quais palavras-chave vendem", "reestruturar o Google Ads". NÃO monta a árvore campanha > grupo > anúncio com MQL, não faz retrospectiva de trimestre e não altera nada na conta do Google Ads (só recomenda).
---

# Plano de Google Ads: CPL + estrutura de campanhas

Roteiro para transformar os dados de uma conta de Google Ads em **decisões**: onde o CPL está subindo e por quê, o que negativar, quais palavras manter ou mover, quais vendem de verdade e como estruturar as campanhas. Foi desenhado a partir de um caso real (provedor regional de internet, outubro/2026) e generalizado para qualquer conta de Search com planilha de leads e CRM.

## O que entrega

Uma página HTML (`index.html`) com 10 seções, sempre nesta ordem:

| # | Seção | De onde vem |
|---|---|---|
| 1 | Resumo: KPIs, decomposição do CPL, alertas e alavancas | `analise.py` + narrativa |
| 2 | Diagnóstico por campanha + **Do lead à venda** | Relatório de campanhas, planilha de leads × CRM |
| 3 | Termos de pesquisa por intenção e por cidade | Relatório de termos de pesquisa |
| 4 | Negativas em dois níveis de risco, com o efeito no CPL | Termos + cenários calculados |
| 5 | Palavras-chave atuais com decisão e custo por venda | Relatório de palavras-chave + vendas |
| 6 | Palavras novas (Semrush) | API do Semrush, filtrada e curada |
| 7 | Estrutura recomendada: campanhas, grupos, palavras, orçamento | Narrativa (`plano.json`) |
| 8 | Checagens antes de mexer | Alertas automáticos + narrativa |
| 9 | Plano de teste com metas e travas | Narrativa |
| 10 | Dados e limites | Automático + narrativa |

Tudo que é **número** sai de script e entra no texto por `{{caminho|formato}}`; o que é **julgamento** (decisões, estrutura, metas) é escrito em `plano.json`.

## O que esta skill NÃO faz
- Não altera a conta do Google Ads. Só recomenda (a aplicação é humana, via Editor ou painel).
- Não cria a árvore clicável campanha → grupo → anúncio com MQL/desqualificação. O `dados.json` já traz a árvore pronta em `vendas.arvore` para quem quiser montá-la.
- Não faz retrospectiva de trimestre nem análise de Meta Ads.
- Não coloca dado pessoal (nome, telefone) na página. O validador barra.

## Princípios (aprendidos em campo)
1. **CPL não é guia de corte.** Cortar o termo de CPL mais alto pode tirar venda. Quando há dado de venda, decida por **custo por venda**; o CPL serve para diagnóstico.
2. **Nenhum número de cabeça.** Toda conta sai dos scripts; a narrativa só referencia. Se um número não está no `dados.json`, calcule antes de escrever.
3. **Valide a base antes de concluir.** Totais batem com o painel, cobertura de termos conhecida, linhas sem data = 0, taxa de cruzamento com o CRM razoável. Um parse errado de data já me fez publicar três conclusões falsas (ver `references/armadilhas.md`).
4. **Estimativa é rotulada.** Gasto escalado para a janela do CRM, volumes do Semrush, taxas com poucas vendas: tudo aparece como "estimado" ou "indicativo".
5. **Amostra pequena não decide.** Abaixo de 15 leads por palavra-chave ou 5 vendas por segmento, mostre o número mas não corte por ele.
6. **Geografia por bairro, pelo CRM.** O STATUS da planilha de leads não é cobertura nem falta de venda. Corte de cidade só com "sem viabilidade" do CRM por bairro, confirmado com o cliente.
7. **Semrush é referência, não verdade.** Volume nacional, CPC de referência, marca local subestimada, concorrentes disfarçados de termo genérico. Cure a lista antes de pagar as unidades.
8. **Errou depois de publicar? Refaça tudo e diga.** Corrija a página, avise o que mudou e por quê, e registre o aprendizado.

## Fluxo

### Passo 0: perguntas (não repergunte o que o usuário já disse)
1. **Cliente/projeto.** Reúna os links do cliente: planilha de acompanhamento mensal, projeção de metas, pasta de arquivos e a página de publicação.
2. **Período a analisar e período de comparação** (normalmente mês corrente × mês anterior).
3. **Objetivo e meta:** reduzir CPL, custo por venda ou ambos; meta da projeção mensal.
4. **Fontes disponíveis:** relatórios do Google Ads, planilha de leads (com UTM e telefone), relatório de vendas do CRM, acesso ao Semrush.
5. **Definição de venda (qualificado) no CRM**, com o nome exato dos estados. Nunca infira.
6. **Onde publicar** (hub do cliente, ver `references/publicacao.md`).

### Passo 1: coletar os arquivos
Peça os exports exatos em `references/coleta-de-dados.md` (campanhas, grupos, palavras-chave, termos de pesquisa, anúncios, negativas, locais, ações de conversão, histórico de alterações; período corrente e anterior). **Confirme que os arquivos são do cliente certo** (nomes de campanha e de grupo) antes de usar: já chegou export de outro cliente na mesma pasta.

### Passo 2: configurar
Copie `assets/config.exemplo.json` para `<pasta do cliente>/plano-google-ads/<AAAA-MM>/config.json` e ajuste: caminhos, `custo_total_conta`, `referencia`, `campanha_marca`, expressões de `marca`, `concorrentes`, `fora_area`, `cidades`, e o bloco `vendas` (planilha de leads, CRM, regras de estado, mapas de UTM). Formato em `references/formatos.md`.

### Passo 3: analisar
```bash
SK=~/.claude/skills/plano-google-ads/scripts
python3 -I $SK/analise.py config.json --saida dados.json
```
Leia a saída antes de seguir e faça a **checagem de sanidade**:
- soma das campanhas = total da conta do painel (±R$ 0,05);
- cobertura de termos visíveis (o Google oculta 20% a 40% do gasto);
- `vendas.qualidade.sem_data` = 0 e `taxa_cruzamento` de vendas ≥ 70% (se menor, investigue formato de data e de telefone);
- CPL e CPC batem com a planilha de acompanhamento do mesmo período;
- alertas automáticos (anúncios reprovados, orçamento limitando, tudo em ampla, índice de qualidade baixo).

### Passo 4: Semrush (opcional, mas recomendado)
```bash
python3 -I $SK/semrush.py unidades
python3 -I $SK/semrush.py descobrir --sementes "internet fibra;internet residencial" --limite 40 --saida descoberta.json
python3 -I $SK/semrush.py filtrar --config config.json --descoberta descoberta.json --saida filtrada.json   # só para curar
# depois de curar as listas dentro do plano.json:
python3 -I $SK/semrush.py volumes --plano plano.json --saida volumes.json
python3 -I $SK/semrush.py filtrar --config config.json --volumes volumes.json --saida semrush.json
```
Poucas sementes (as palavras que já convertem e as cidades-alvo), 20 a 40 linhas cada. Confira o saldo antes. A chave vem de `SEMRUSH_API_KEY` ou de um arquivo indicado em `--chave-arquivo` (nunca imprimir).

### Passo 5: escrever o `plano.json`
Parta de `assets/plano.exemplo.json` (caso de demonstração) e adapte. É aqui que mora o julgamento: decisões por palavra-chave, tiers de negativa, estrutura de campanhas, metas. Use `references/metodologia.md` (regras de decisão) e `references/estrutura-de-campanhas.md` (playbook de estrutura). Todo número do texto vem de `{{caminho|formato}}`.

### Passo 6: gerar e validar
```bash
python3 -I $SK/gerar_plano.py --dados dados.json --plano plano.json --semrush semrush.json --saida index.html
python3 -I $SK/validar_pagina.py index.html
```
O gerador sai com erro se um `{{caminho}}` não existir no `dados.json`. Tire print real com o Chrome headless e leia (ver `references/publicacao.md`) antes de dizer que está pronto.

### Passo 7: publicar
No hub do cliente (um link só por cliente), seguindo `references/publicacao.md`: página em `/plano/`, card na página inicial, deploy, conferência de cada URL.

### Passo 8: entregar
Responda com: o resultado em 3 a 5 achados, as decisões, o que **não** foi possível medir e **o que falta** (exports, acessos). Se algum número da conversa anterior mudou, diga.

## Definition of Done
- [ ] Perguntas do Passo 0 respondidas (ou assumidas e declaradas).
- [ ] Checagem de sanidade do Passo 3 feita e registrada na seção "Dados e limites".
- [ ] Nenhum número escrito à mão em `plano.json`: tudo por `{{...}}`, exceto fatos externos (volumes do Semrush citados em texto, metas).
- [ ] Negativas separadas em Tier 1 (aplicar já) e Tier 2 (validar com vendas), com o efeito no CPL calculado.
- [ ] Palavras-chave decididas por custo por venda quando há venda, e por CPL com ressalva quando não há.
- [ ] Estrutura recomendada com campanhas, grupos, palavras (novas × já na conta), correspondência, orçamento, lance, geografia, anúncios/extensões e páginas.
- [ ] Plano de teste com metas **e travas**.
- [ ] `validar_pagina.py` sem erros; print conferido; todas as URLs do hub respondem 200.
- [ ] Limites declarados: período, cobertura de termos, amostras pequenas, o que não foi exportado.

## Referências
- `references/coleta-de-dados.md`: quais relatórios pedir e como baixar.
- `references/metodologia.md`: fórmulas, classificação de termos, negativas, decisão por palavra-chave, cruzamento com vendas, Semrush.
- `references/estrutura-de-campanhas.md`: playbook de estrutura, orçamento, lance, geografia, anúncios, plano de teste.
- `references/formatos.md`: esquema do `config.json`, do `dados.json` e do `plano.json`.
- `references/publicacao.md`: hub do cliente no Vercel, validação visual.
- `references/armadilhas.md`: erros que já aconteceram e como evitar.
- `references/exemplo-demo.md`: números de referência do caso de demonstração, para testar os scripts.
