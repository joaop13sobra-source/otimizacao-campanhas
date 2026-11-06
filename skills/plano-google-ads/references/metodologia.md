# Metodologia

Fórmulas e regras de decisão usadas por `analise.py` e esperadas em `plano.json`. Todas foram calibradas em um caso real e conferidas no caso de demonstração (ver `exemplo-demo.md`).

## 1. O CPL é CPC dividido pela conversão

`CPL = CPC ÷ (conversões ÷ cliques)`. Quando o CPL muda, a causa é uma de duas: o clique ficou mais caro, ou menos cliques viram lead.

`analise.py` divide a variação (em log) entre as duas causas e grava em `decomposicao` (`parte_cpc_pct`, `parte_conversao_pct`). Exemplo do caso real: CPL +56%, sendo 59% por CPC e 41% por conversão.

- **Parte de CPC alta:** olhe mix de campanhas (a campanha de genéricos tem CPC maior), orçamento subindo (mais verba empurra para leilões mais caros), perda de impressões por classificação, índice de qualidade baixo, estratégia de lance.
- **Parte de conversão alta:** olhe LP/formulário que mudou, ação de conversão que mudou, anúncios reprovados, termos de baixa intenção entrando por correspondência ampla. Confirme com o histórico de alterações.

O período de comparação vem da planilha de acompanhamento mensal (campo `referencia` do config). Sem ele, a decomposição não existe e o resumo não pode afirmar "subiu".

## 2. Temas de busca (por intenção)

`classificar_termo` aplica, nesta ordem, regras de texto (regex sobre o termo sem acento):

| Tema | Regra | O que costuma ser |
|---|---|---|
| Marca + suporte/cliente | marca e (suporte, boleto, 2ª via, fatura, login, central...) | cliente atual pedindo atendimento: ruído |
| Marca + contato | marca e (whatsapp, telefone, número, contato) | prospect querendo falar: costuma ter o melhor CPL |
| Marca + cidade/bairro | marca e cidade-alvo ou fora de área | prospect local de alta intenção |
| Marca pura | marca sem nada acima | motor da conta |
| Concorrentes | nomes em `regex.concorrentes` | baixa intenção, CPL mais alto |
| Genérico + cidade | cidade-alvo sem marca | maior intenção entre os genéricos, CPC alto |
| Genérico sem cidade | o resto | topo, CPL mais alto |

A classificação é por texto e erra em casos de borda. Os **CPLs por tema costumam ficar próximos entre si**; se ficarem muito distantes, procure um problema real (tema vazando para a campanha errada, conversão duvidosa).

## 3. Marca vazando para a campanha de genéricos

`marca_fora_da_campanha_de_marca` mede quanto do gasto da campanha que **não** é de marca vai para termos de marca. A marca deve ficar na campanha própria (índice de qualidade alto, CPC baixo, controle de orçamento). Corrija com negativa de marca exata nas outras campanhas. Isso reorganiza a verba, mas **não reduz o CPL sozinho** (o CPL da marca costuma estar abaixo da média).

## 4. Negativas

Dois níveis de risco:

- **Tier 1 (aplicar já):** suporte/cliente da marca, concorrente + contato/atendimento (cliente do concorrente pedindo telefone), cidades fora da área. Baixo risco: quase nenhuma conversão sendo perdida.
- **Tier 2 (validar com vendas antes):** nomes de concorrentes (há conversões, e algumas podem virar venda) e qualquer corte de cidade.

`cenarios` calcula o CPL após remover o conjunto: `CPL_novo = (custo − custo_removido) ÷ (conversões − conversões_removidas)`, supondo que a verba liberada rende o CPL médio do que sobra. É o efeito **máximo realista**; em geral fica entre −1% e −3%. Diga isso: negativas são higiene, não a alavanca.

Regras:
- Negative por **frase**, nunca palavra solta ambígua (ex.: "net" casa com "internet").
- Nunca negativar o que converte e vende (marca + contato).
- Lista compartilhada, aplicada às campanhas atuais e às novas. Revise a lista existente antes.
- Os termos listados são evidência; as palavras do campo `tags` são o que se cadastra.

## 5. Palavras-chave: decisão

Use **custo por venda** quando houver venda; sem venda, CPL com ressalva. Só decida por taxa com **15 leads ou mais** na palavra.

| Situação | Decisão |
|---|---|
| Marca | Manter. Migrar de ampla para exata/frase, negativas de suporte, liberar orçamento se perde impressão por verba |
| Custo por venda ≤ média da conta | Manter e priorizar |
| Custo por venda > 1,3× a média com ≥ 15 leads | Reduzir: frase, lance menor, reavaliar em 14 dias |
| CPL alto, mas custo por venda no nível da marca | **Manter** (não cortar por CPL) |
| Gasto ≥ 2× o CPL médio e zero conversão | Pausar |
| Redundante (coberta por outra) ou gasto irrisório sem conversão | Pausar |
| Índice de qualidade ≤ 5 | Reescrever anúncios do grupo antes de escalar |
| Poucos dados | Observar, reavaliar em 2 semanas |
| CPC muito alto em ampla (ex.: palavra local) | Mover para campanha local, em frase/exata, com teto de CPC |

## 6. Do lead à venda (cruzamento por telefone)

`cruzar_vendas.py`:
1. Lê a planilha de leads, tenta **todos os formatos de data** e acusa linhas sem data.
2. Chave do telefone: DDD + últimos 8 dígitos (ignora o 9 extra, o 55 e o zero).
3. Estados do CRM por regras do config: `venda`, `desq`, `aberto`. Lead sem registro no CRM conta como `aberto` e é contado à parte.
4. **Vendas do CRM × planilha, ignorando a data:** `taxa_cruzamento` = vendas achadas ÷ vendas do CRM. Abaixo de ~70%, investigue antes de seguir.
5. **Leads da janela, sem repetidos por telefone** (o último lead do telefone). A janela termina na data do relatório do CRM.
6. **Gasto na janela:** quando o export do Ads cobre mais dias que o CRM, escale: `fração = gasto_janela_total ÷ custo_total_conta`. Rotule "estimado".
7. **Custo por venda** = gasto ÷ vendas, por campanha, grupo e palavra-chave (onde há gasto). Por anúncio, cidade e status só taxa de venda.

Leituras que costumam aparecer:
- O lead da marca e o dos genéricos podem **vender na mesma taxa**; a diferença de custo vem de CPC e conversão por clique.
- O melhor anúncio **muda de um grupo para outro**: compare sempre dentro do grupo e mostre o n.
- O status da planilha tem valor preditivo mas **não serve como corte**: parte das vendas vem de leads "inválidos".

Amostra: com menos de 5 vendas por segmento a taxa é só indicativa; diga isso na página.

## 7. Orçamento e impressões perdidas

- `perd_orc ≥ 15%` com CPL abaixo da média: candidata a mais verba (o volume existe e está sendo perdido).
- `perd_class ≥ 25%`: problema de lance ou qualidade (índice de qualidade, relevância do anúncio), não de verba.
- Campanha "limitada pelo volume de pesquisas": o teto é a demanda, não o orçamento. Escalar verba só em Search não resolve.

## 8. Semrush: como usar sem se enganar

1. **Sementes:** as palavras que já convertem e as cidades-alvo; 20 a 40 linhas por semente (`phrase_fullsearch`, ~40 unidades por linha).
2. **Filtrar** (`semrush.py filtrar`): remove marca de concorrente, informacional/suporte, fora de área. Os **concorrentes locais vêm disfarçados de termo genérico** (nomes de provedores): cure à mão.
3. **Cure as listas dentro do `plano.json`** e só então rode `volumes --plano` (~10 unidades por linha).
4. **Volume é do Brasil inteiro.** A parte local só aparece quando a cidade está no texto. "Perto de mim" é filtrado pela localização do usuário, então o volume nacional não vira gasto fora da área.
5. **Marca local é subestimada** (um termo de marca + cidade com 10 buscas/mês no Semrush e dezenas de conversões na conta). Use o desempenho da conta como verdade.
6. **CPC e concorrência são referências** para ordenar, não o leilão do cliente (há valores absurdos em termos de grandes concorrentes).
7. **Abaixo de 20 buscas o Semrush não mede**; agrupe essas variações em frase na campanha local.
8. **Cada termo novo de localidade precisa de checagem de cobertura** no CRM por bairro antes de entrar (um distrito sem viabilidade já apareceu como "oportunidade").
9. **Teto da demanda:** compare a soma dos volumes de marca, locais e de intenção alta. Se a demanda local for pequena, Search não absorve a verba planejada: diga isso e recomende olhar outros canais.

## 9. Metas e travas

Meta de CPL = CPL atual × (1 + efeito dos cenários calculados), nunca uma promessa. A meta traz sempre uma **trava**: custo por venda não pode piorar mais de 10%, leads por dia não podem cair abaixo de 85% do atual. Mexa em uma alavanca por vez e leia em 14 dias.
