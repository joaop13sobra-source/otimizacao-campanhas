---
name: otimizacao-campanhas
description: >
  Cruza export de campanhas Meta Ads + Google Ads (CSV/Excel) com leads do CRM do
  cliente (via UTM) pra descobrir quais campanhas, públicos (Meta) e palavras-chave
  (Google) geram MQL barato vs MQL caro, e gera um HTML padronizado de decisão de
  investimento (`assets/reference-otimizacao-campanhas.html`) — onde investir mais,
  onde investir menos, o que pausar, e uma segunda aba de desqualificação (taxa de
  leads perdidos e motivo de perda). É a rotina semanal de otimização de campanhas por
  cliente. Regra dura: toda vez que a skill é chamada, SEMPRE pergunta (nesta ordem)
  qual é o CRM do cliente, qual é o período a analisar, e qual é a etapa de MQL no
  funil daquele CRM — nunca infere, nunca reaproveita etapa/período de outro cliente ou
  de uma rodada anterior sem confirmar. CRM mais comum: Kommo. MQL = lead na etapa de
  MQL confirmada OU em qualquer etapa posterior do funil de vendas daquele CRM (quem já
  passou de MQL continua contando como MQL). Ativar quando o usuário pedir "otimização
  de campanhas", "otimizar campanhas do cliente X", mandar CSV/Excel de Meta e Google
  pra cruzar com CRM, pedir pra saber onde investir mais/menos, qual público/palavra-
  chave está performando bem ou mal, taxa de desqualificação, motivo de perda, ou rodar
  a rotina semanal de campanhas. IMPORTANTE: qualificado é medido pelo HISTÓRICO de
  etapas do lead (alcançou a etapa de MQL ou posterior alguma vez), nunca só pela etapa
  atual — um lead que virou MQL e depois foi movido pra Perdido continua contando como
  qualificado (a campanha entregou; o motivo de não fechar é comercial).
  Mede o funil completo (MQL, SQL e Venda). Inclui os scripts que puxam o CRM, cruzam com a mídia e geram o dashboard.
  Opcional: quando o usuário pedir, também lança o diagnóstico completo num Google Doc de comitê / Sprint Growth ("lança no Docs, semana N") no formato de `references/sprint-growth.md`. Complementa a skill `plano-google-ads` (CPL, negativas e estrutura de campanhas).
---

# Otimização de Campanhas (Meta + Google × CRM)

Rotina semanal, por cliente: cruza investimento de mídia (Meta + Google) com leads
qualificados do CRM via UTM, pra decidir onde aumentar/cortar verba e qual
público/keyword está funcionando.

Skill genérica, não amarrada a nenhum cliente: serve para qualquer projeto, com o CRM e as contas de quem está usando.
A calibração de cada projeto é opcional e fica com quem usa (ver [Sub-playbooks por cliente](#sub-playbooks-por-cliente)).

**O formato é fixo.** O layout em `assets/reference-otimizacao-campanhas.html` (três abas Geral/Qualificação/
Desqualificação, árvore clicável com delta vs média, ordenação por coluna, filtro por motivo de perda, funil
MQL + SQL + Venda, qualificação pelo histórico de etapas, tabela "Qualificados que não fecharam") é o padrão de
todo projeto. Só o dado muda: não redesenhar a estrutura. O que for específico de um CRM ou conta (peculiaridade de
UTM, campos extras) vai no config e, se quiser, no sub-playbook do projeto.

## O que precisa estar instalado

Nem tudo é obrigatório. O caminho mínimo é só Python + exports em CSV. Ver o `README.md` do repositório.

| Precisa de | Para quê | Sem isso |
|---|---|---|
| Python 3.9+ (`openpyxl` para .xlsx) | Scripts | Obrigatório |
| Token do CRM (`KOMMO_TOKEN`, `KOMMO_SUBDOMAIN`) | Puxar leads + histórico | Peça a planilha de leads e use a coluna `historico`, se existir |
| Google Chrome | `validar.py` roda o JavaScript de verdade | Valida só o estático e avisa |
| CLI do Vercel | Publicar o link | Entregue o `index.html` |
| Conta de serviço Google com Docs API | Doc de comitê / Sprint Growth | Só essa saída opcional fica indisponível |
| MCP do Cockpit/Flow (NEKT) | Mídia sem CSV, conferir gasto recente | Use os exports de Meta e Google |

## Quando usar

- Usuário manda CSV/Excel de campanhas Meta e/ou Google de um cliente pra analisar.
- Usuário pede "otimização de campanhas", "onde eu invisto mais/menos", "qual público
  tá performando melhor/pior", "qual palavra-chave tá boa/ruim".
- Rotina semanal já calibrada de um cliente (ver sub-playbook do cliente, se existir).

## O que sempre perguntar quando a skill é chamada (nesta ordem)

Toda vez que o usuário pedir pra rodar essa otimização — mesmo que já tenha calibrado
esse cliente antes — perguntar, nesta ordem, antes de pedir qualquer arquivo:

1. **Qual cliente/projeto.** Se já existe sub-playbook (`otimizacao-campanhas-<cliente>.md`
   nesta mesma pasta), carregar ele — ele já tem CRM, peculiaridade de export e a última
   etapa de MQL confirmada — mas isso não substitui o passo 3, só evita perguntar de novo
   o que não muda (CRM, forma de acesso).
2. **Qual é o CRM do cliente.** O mais comum na operação é **Kommo** — já existe
   familiaridade com como puxar UTM de lead no Kommo (ver
   [CRM padrão: Kommo](#crm-padrão-kommo)). Se for outro CRM (Bitrix, etc.), perguntar
   como acessar.
3. **Qual é o período a analisar** (data início e fim — a mesma janela vale pro CSV de
   mídia e pra busca de leads no CRM).
4. **Qual é a etapa de MQL no CRM desse funil — sempre perguntar, mesmo se o
   sub-playbook já tiver isso registrado de uma rodada anterior** (o funil pode ter
   mudado). Nunca inferir pelo nome da etapa, nunca assumir sem confirmar. Ver regra
   dura abaixo.

## O que o usuário entrega

Depois de responder as 4 perguntas acima, o papel do usuário é entregar:

1. **CSV/Excel de Meta Ads** do período definido (export de campanhas — precisa ter no
   mínimo campanha, conjunto/público, investimento; UTM de campanha se o cliente usa UTM
   customizada em vez do nome padrão da campanha).
2. **CSV/Excel de Google Ads** do período definido (campanha, grupo de anúncio,
   palavra-chave/termo de busca, investimento).
3. **Acesso ao CRM** — dois caminhos, perguntar qual se aplica:
   - **Com API/MCP** (caso comum do Kommo): credencial de acesso, e a busca dos leads +
     UTM + etapa é feita direto pela skill.
   - **Sem API**: o usuário manda uma planilha com os leads do período e a etapa atual
     de cada um (e, se for calcular a aba de desqualificação, o motivo de perda de quem
     foi pra "Perdido"). Nesse caso a skill não tenta acessar o CRM, trabalha só com a
     planilha.

## CRM padrão: Kommo

A maioria dos clientes dessa rotina usa Kommo. Reaproveitar o conhecimento já
consolidado na operação sobre esse CRM em vez de redescobrir do zero:

- Custom fields de UTM (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`) ficam no lead ou
  no contato, depende da conta (`kommo.utm_no_contato` no config).
- O token fica no ambiente ou em `.env` do projeto, nunca no repositório nem na conversa.
- `python3 -I scripts/puxar_kommo.py config.json --listar-funis` mostra funis e etapas ao vivo, para confirmar a etapa
  de MQL com o usuário. Etapa e funil variam por cliente: nunca reaproveitar o mapeamento de outro cliente, mesmo que
  o nome pareça igual.
- Detalhes da API, outros CRMs (Bitrix, sem API, ERP) e a régua pela conversa: `references/crm-e-fontes.md`.

## Regra dura: definição de MQL (nunca inferir, sempre pelo histórico)

> Cada projeto tem uma etapa de MQL diferente no CRM, geralmente com um nome que
> evidencia isso ("MQL", "Qualificado", etc.). Todo lead que **alcançou essa etapa ou
> qualquer etapa posterior alguma vez no histórico dele** conta como qualificado — não
> importa a etapa atual. Um lead que virou MQL, teve reunião marcada, e **depois foi
> movido pra Perdido** continua contando como qualificado: a campanha/anúncio fez o
> trabalho dela (gerou um lead com fit real), o motivo de não fechar é comercial
> (SDR/closer, orçamento, concorrência), não um problema de mídia/targeting. Leads que
> **nunca** alcançaram a etapa de MQL e foram perdidos são os únicos que contam como
> desqualificados de verdade pra fins de mídia.

**Consequência prática — usar histórico de etapas, não só o status atual do lead**:
- Se o CRM expõe histórico de mudança de etapa (ex.: Kommo `GET /api/v4/events?
  filter[type][]=lead_status_changed&filter[entity]=lead`, paginado pelo período),
  puxar isso pra cada lead e calcular o **maior estágio já alcançado** (comparando pela
  ordem real do funil, não pelo valor numérico do `status_id` — pipeline `sort`/posição,
  não o ID em si). Se esse maior estágio for MQL ou posterior, o lead é qualificado,
  mesmo que o status atual seja Perdido.
- Se o CRM **não** expõe histórico de forma acessível, usar só o status atual e
  **avisar explicitamente** no output que a taxa de qualificação pode estar subestimada
  (leads que qualificaram e depois foram perdidos aparecem como desqualificados nesse
  caso) — nunca silenciar essa limitação.
- Separar no output os qualificados em dois grupos pra transparência: **qualificado
  ativo** (etapa atual ainda é MQL+ ou ganhou) e **qualificado, perdido depois** (etapa
  atual é Perdido, mas alcançou MQL+ no histórico) — ver
  [Qualificados que não fecharam](#qualificados-que-não-fecharam).

Antes de calcular qualquer métrica, é obrigatório confirmar com o usuário qual etapa
exata do pipeline daquele CRM é a etapa de MQL. Se o usuário não disser, perguntar antes
de prosseguir — nunca assumir "provavelmente é a etapa X".

Definição de SQL e Venda, regra cumulativa e o que fazer quando a etapa do CRM não é confiável:
`references/regua-do-funil.md`.

## Como rodar (scripts)

```bash
SK=~/.claude/skills/otimizacao-campanhas
# 1. copie assets/config.exemplo.json para a pasta da rodada e ajuste (formato: references/config.md)
# 2. leads: pelo CRM (grava leads_normalizados.json; aponte leads.arquivo_normalizado no config) ou planilha mapeada em leads.colunas
python3 -I $SK/scripts/puxar_kommo.py config.json --saida leads_normalizados.json
# 3. cruza com a mídia e reconcilia (sai com erro se a árvore não fechar ou aparecer etapa desconhecida)
python3 -I $SK/scripts/montar_dados.py config.json --saida dados.json
# 4. escreva a leitura da rodada em notas.* no config, rode de novo o passo 3, e gere o HTML
python3 -I $SK/scripts/gerar_html.py dados.json --saida deploy/index.html
# 5. valida no Chrome real antes de publicar
python3 -I $SK/scripts/validar.py deploy/index.html
```

Teste sem nenhum acesso: `assets/demo/` traz dados fictícios. Entre na pasta e rode os passos 3 a 5 com o `config.json` dela.
Leia a linha "Qualidade" impressa pelo passo 3 antes de escrever qualquer conclusão, e consulte `references/armadilhas.md`.

## Fluxo de cálculo

Os scripts implementam os passos abaixo. Quando um projeto não couber neles, ajuste o script na pasta da rodada, sem alterar as regras.

1. **Buscar leads do CRM** no período pedido, com UTM completa
   (`utm_source`/`utm_medium`/`utm_campaign`/`utm_content`/`utm_term`, ou equivalente
   do CRM) e etapa atual do funil.
2. **Classificar MQL** aplicando a regra dura acima (etapa confirmada + tudo posterior).
3. **Cruzar por UTM**: casar `utm_campaign` (e `utm_source`/`utm_medium` quando precisar
   desambiguar Meta vs Google, ou quando duas campanhas têm nome parecido) dos leads
   MQL com as linhas de campanha do CSV de mídia correspondente. Documentar no output
   qualquer lead que não deu match (sem UTM, UTM quebrada, campanha não encontrada no
   CSV) — nunca descartar silenciosamente. Se o cruzamento encontrar uma sobreposição/
   ambiguidade de UTM entre duas campanhas (ex.: dois anúncios de campanhas diferentes
   usando o mesmo `utm_medium`), **descrever como ambiguidade a resolver, nunca como
   "erro"/"bug" do cliente** — pode ser intencional (mesmo tema/criativo reaproveitado
   entre campanhas). Resolver com outro campo do UTM que não tenha a mesma sobreposição
   (ex.: `utm_term`) e, se precisar recomendar mudança na configuração, confirmar com o
   usuário antes — não presumir que é erro.
4. **Métricas por campanha** (Meta e Google, tabelas separadas):
   Investimento, Leads totais, MQL, **Custo por MQL**, Taxa de MQL (MQL / Leads totais), SQL, Custo por SQL,
   Taxa de SQL e Venda.
5. **Métricas por público** (Meta, quebra por conjunto de anúncios/público) e **por
   anúncio** dentro de cada público: mesmas colunas, em estrutura de árvore
   (Campanha → Público → Anúncio) — ver [Drill-down](#drill-down-igual-ao-gerenciador).
6. **Métricas por palavra-chave** (Google, quebra por keyword/termo de busca) e **por
   grupo de anúncios → anúncio**: mesma lógica de árvore (Campanha → Grupo de Anúncios →
   Anúncio), com a tabela de palavra-chave à parte (dimensão cruzada, não é filha direta
   do grupo).
7. **Delta vs média da conta**: todo Custo por MQL e Taxa de MQL vem acompanhado do
   desvio percentual contra a média dos itens do **mesmo nível** (campanha com campanha,
   público com público, anúncio com anúncio — nunca campanha contra anúncio). Média
   simples entre irmãos, não ponderada por investimento, pra uma conta grande não
   mascarar quem é outlier de verdade. Selo verde = puxando o resultado pra cima
   (custo abaixo da média, taxa acima), vermelho = puxando pra baixo, cinza = dentro de
   ±8% (não é sinal, é ruído).
8. **Rankear e recomendar** — sempre pelo Custo por MQL e Taxa de MQL, nunca por CPL
   isolado (lead barato sem qualificação não é sinal de campanha boa):
   - Investir mais: menor custo por MQL, taxa de MQL saudável, volume não trivial.
   - Investir menos / pausar: maior custo por MQL, taxa de MQL baixa.
   - Inconclusivo / fora do ranking: menos de 3 MQL — volume baixo demais pra decidir
     (mostrar na tabela normalmente, só não entra no ranking "investir mais/menos").
9. **Gerar o HTML** seguindo `assets/reference-otimizacao-campanhas.html`.

## Aba Geral (qualificado × desqualificado × em aberto)

Terceira aba, primeira a aparecer no HTML (é o resumo antes do detalhe) — mesma árvore
Campanha → Público/Grupo → Anúncio, mas sem separar leitura por MQL ou por Perdido:
mostra os três estados juntos, pra dar noção de proporção antes de julgar campanha boa
ou ruim.

1. **Três estados, mutuamente exclusivos, somando 100% dos leads da linha**:
   - **Qualificado** = mesma contagem de MQL da aba de Qualificação.
   - **Desqualificado** = mesma contagem de Perdido da aba de Desqualificação.
   - **Em aberto** = `Leads − Qualificado − Desqualificado`. Lead que ainda não chegou
     na etapa de MQL nem foi movido pra Perdido — está em atendimento ou numa etapa
     inicial do funil. Não é bom nem ruim por si só, é "ainda não decidido".
2. **Visual**: barra de proporção (Qualificado/Desqualificado/Em aberto) por linha, em
   vez de uma métrica isolada com delta — o ponto da aba é dar a leitura de mix de
   relance, não comparar contra média.
3. **KPI da aba**: Investimento total, Leads, Qualificados (contagem + % do total),
   Desqualificados (contagem + % do total), Em aberto (contagem + % do total).
4. **Destaque no topo**: ranking de maior taxa de "em aberto" (piso de volume mínimo de
   8 leads) — sinaliza onde o funil está mais parado, o que pode ser problema de
   SLA/atendimento e não necessariamente de mídia. Não tem lado "bom" simétrico (baixo
   em aberto não é necessariamente notável), então é destaque único, não par
   investir-mais/investir-menos.
5. Não repete o ranking por palavra-chave nem o ranking "investir mais/menos" — esses
   ficam nas abas específicas (Qualificação e Desqualificação); a aba Geral é só o
   panorama de proporção.

## Aba de Desqualificação

Segunda aba do mesmo HTML (não mistura com a aba de MQL) — mesma leitura de dado, mesma
árvore Campanha → Público/Grupo → Anúncio, mesmo cruzamento por UTM, só que pros leads
que foram movidos pra **"Perdido"** no CRM em vez de MQL.

1. **Classificar desqualificado**: lead cuja etapa atual é a etapa de perda do funil
   (geralmente chamada "Perdido" — confirmar o nome exato junto com a etapa de MQL, não
   assumir) **E que nunca alcançou a etapa de MQL no histórico dele**. Um lead que
   qualificou e só depois foi perdido **não** entra aqui — ele é qualificado (ver regra
   do histórico acima) e aparece em
   [Qualificados que não fecharam](#qualificados-que-não-fecharam), não nesta aba. Todo
   lead pago cai em exatamente um de três baldes: qualificado (ativo ou perdido depois),
   desqualificado (nunca qualificou), em aberto — nunca em dois ao mesmo tempo.
2. **Métricas por nível** (mesma árvore da aba de MQL): Investimento, Leads, Desqualificados,
   Taxa de Desqualificação (Desqualificados / Leads) — sem Custo por Desqualificado (não é
   uma decisão de custo, é sinal de qualidade de targeting/copy).
3. **Delta vs média da conta**: mesma lógica da aba de MQL, mas invertida — abaixo da
   média é bom (verde), acima da média é ruim (vermelho), porque aqui menos é melhor.
4. **Motivo de perda**: ranking de todos os motivos pelos quais lead foi marcado como
   perdido (campo do CRM, ex.: sem resposta, fora do perfil, sem orçamento, concorrente,
   fora da região) — quantidade e % sobre o total de desqualificados. Se o CRM não tiver
   esse campo preenchido de forma consistente, sinalizar quantos leads perdidos estão
   sem motivo, não inventar categoria. Ao montar a árvore de campanha/público/anúncio
   desta aba, guardar também a contagem por motivo em cada nó (ex.: campo
   `lostReasons: {motivo: quantidade}`, somando o `lost` do nó) — é o que permite clicar
   num motivo no ranking e ver onde ele concentra por campanha (ver
   [Template HTML](#template-html)).
5. **KPI da aba**: Leads totais, Desqualificados, Taxa de Desqualificação geral, Motivo
   mais frequente.
6. **Destaque no topo da aba**: menor e maior taxa de desqualificação entre todos os
   níveis (mesmo princípio do "investir mais/menos" da aba de MQL, mas aqui é
   "saudável"/"crítico"), com piso de volume mínimo pra entrar no ranking (leads
   insuficientes ficam de fora do destaque, mas continuam nas tabelas).

## Qualificados que não fecharam

Tabela pequena na aba de Qualificação (depois do ranking de palavra-chave), só com
Motivo de Perda × Quantidade × % — dos leads que alcançaram MQL+ no histórico mas cuja
etapa atual é Perdido. Existe pra responder exatamente o que o usuário for perguntar
("teve muito lead que qualificou e não fechou, por quê?") sem misturar isso com a taxa
de desqualificação (que é sobre mídia/targeting, não sobre processo comercial). Não
precisa de nível por campanha nessa tabela (é um recorte pequeno, geralmente <10% do
total de leads pagos) — motivo agregado já é suficiente pra decisão. Se algum motivo
aqui parecer estranho pra ter vindo de um lead já qualificado (ex.: "Sem perfil" depois
de MQL), **não corrigir/filtrar silenciosamente** — reportar como está e mencionar a
inconsistência ao usuário, pode ser um lead que avançou e recuou de etapa por engano do
time comercial.

## Drill-down igual ao gerenciador

O HTML não é mais uma lista de tabelas soltas — é uma árvore clicável, igual ao Meta
Ads Manager / Google Ads Editor: clicar na campanha abre os públicos (Meta) ou grupos
de anúncios (Google); clicar no público/grupo abre os anúncios. Cada nível mostra as
mesmas colunas (Investimento, Leads, MQL, Custo/MQL com delta, Taxa de MQL com delta e
barra de magnitude), pra achar não só qual campanha é ruim, mas qual público *dentro*
dela é o problema, e qual anúncio *dentro* do público. O ranking "Investir mais/menos"
no topo do HTML varre todos os níveis (campanha, público/grupo, anúncio, palavra-chave)
de uma vez e traz os 3 melhores e 3 piores custo/MQL — não fica preso ao nível de
campanha.

**Regra dura de reconciliação:** a
soma dos filhos visíveis de todo nó (campanha → públicos/grupos visíveis, público/grupo →
anúncios visíveis) tem que bater exatamente com o total do nó pai — nunca um número que
só aparece "por dentro" sem estar refletido em nenhum filho clicável. Quando o cruzamento
por UTM não consegue descer um lead até o filho mais granular (ex.: o mesmo nome de
anúncio é reaproveitado em vários públicos/grupos ao mesmo tempo, o anúncio já não existe
mais no export atual, ou o UTM não tem conteúdo pra decidir), criar um **nó sintético
visível** no nível em que a resolução parou (ex.: "(Anúncio replicado em vários públicos
desta campanha — sem como saber qual gerou o lead)"), com `invest: 0` (não inventar
rateio de investimento) carregando os leads/MQL/lost reais. Esse nó sintético entra
normalmente nos rankings de taxa (desqualificação, em aberto), mas o ranking de
custo/MQL ("Investir mais/menos") filtra `invest > 0` — um nó sem investimento próprio
sempre teria custo/MQL = R$0, o que pareceria (erradamente) a melhor campanha da conta.
O `scripts/montar_dados.py` implementa isso e confere com `assert`.

**Um nó ambíguo entre campanhas ainda precisa de drill-down**, mesmo sem saber qual candidata gerou qual lead. Quando
várias campanhas dividem a mesma UTM sem nada que as separe, use `agrupar_campanhas` no config: elas viram uma linha só, com
o investimento somado e a árvore real de grupo e anúncio embaixo. Confirme o agrupamento com o usuário e declare na nota.

## Template HTML

Ver `assets/reference-otimizacao-campanhas.html`, desenhado para decisão de investimento. Estrutura:

- Header com cliente, CRM, período analisado e etapa de MQL confirmada.
- Três abas, nesta ordem: **Geral**, **Qualificação (MQL)** e **Desqualificação** — nunca
  misturar as três leituras na mesma tabela, mesmo reaproveitando a mesma árvore de
  campanha/público/anúncio. Geral é a aba padrão/ativa ao abrir o HTML.
- Aba Geral: KPIs de Investimento, Leads, Qualificados/Desqualificados/Em aberto (com %
  do total cada); destaque único de maior taxa de "em aberto"; árvore com barra de
  proporção (Qualificado/Desqualificado/Em aberto) por linha, sem delta vs média — ver
  [Aba Geral](#aba-geral-qualificado--desqualificado--em-aberto).
- Aba MQL: linha de KPIs do funil completo (Investimento total, Leads, MQL, Custo por
  MQL, SQL, Custo por SQL, Venda, Custo por Venda); bloco de destaque **"Invista mais" / "Invista menos"**
  logo no topo, varrendo todos os níveis; árvore clicável por plataforma (Meta:
  Campanha → Público → Anúncio; Google: Campanha → Grupo de Anúncios → Anúncio) com
  sinalização por cor baseada em custo por MQL relativo à média do próprio nível, selo
  de delta e barra de magnitude na Taxa de MQL; ranking por palavra-chave (Google) à
  parte; tabela **"Qualificados que não fecharam"** logo depois (ver
  [Qualificados que não fecharam](#qualificados-que-não-fecharam)).
- Aba Desqualificação: KPIs (Leads totais, Desqualificados, Taxa de Desqualificação,
  Motivo mais frequente); destaque de menor/maior taxa de desqualificação no topo;
  mesma árvore clicável, mas com Taxa de Desqualificação (delta invertido — abaixo da
  média é bom); ranking por motivo de perda (barra sempre em % do total, clicável — ver
  [Ordenação e filtro](#template-html) abaixo).
- Nota de qualidade de dado em cada aba: leads sem UTM/match (MQL) e leads perdidos sem
  motivo preenchido (Desqualificação) — nunca descartar silenciosamente.
- **Ordenação por coluna** em toda árvore/tabela (campanha, MQL, desqualificação e
  ranking de palavra-chave): um seletor "Ordenar por" (Investimento, Custo/MQL ou Taxa
  — o que fizer sentido pra aquela aba — e Leads) + botão de direção
  crescente/decrescente. Reordena só entre irmãos do mesmo nível, nunca achata a árvore.
  Nó sem Custo/MQL válido (0 MQL) sempre cai no fim da lista, nas duas direções.
- **Filtro por motivo de perda** na aba de Desqualificação: clicar numa linha do ranking
  de motivo recalcula Desqualificados/Taxa de Desqualificação das árvores de campanha
  usando só aquele motivo (cruza motivo × campanha/público/anúncio), com chip
  "Mostrando: {motivo} ✕" pra limpar. Barra do ranking de motivo é sempre % do total de
  desqualificados (não relativa ao maior motivo).

Estrutura e visual são o padrão fixo — só o dado (`META_TREE`, `GOOGLE_TREE`,
`GOOGLE_KEYWORDS`, `LOSS_REASONS`, `QUALIFIED_LOST_REASONS`) muda por cliente. Não
redesenhar layout, cores ou proporções por cliente; se algo genuinamente não couber
nesse formato pra um caso específico, tratar como exceção pontual no sub-playbook do
cliente, não como pretexto pra alterar o motor genérico sem necessidade.

## Saída opcional: diagnóstico no Google Docs (Doc de comitê / Sprint Growth)

Só quando o usuário pedir para "lançar no Docs", "colocar na aba da semana N" ou equivalente. O padrão da rotina é o HTML
publicado. Formato, seções, formatação e mecânica: `references/sprint-growth.md`. Gerador e montador:
`assets/docs-diagnostico/`. Tasks de uma reunião de Sprint Growth levam as tags da mesma referência.

## Quando usar também a skill `plano-google-ads`

Esta skill responde **onde mexer na verba** (árvore campanha > grupo > anúncio por MQL). A `plano-google-ads`, instalada junto
por este repositório, responde **o que fazer dentro do Google Ads**: por que o CPL subiu, o que negativar, quais palavras vendem e
como reestruturar. Se esta rodada apontar problema no Google (CPL subindo, palavra cara, campanha sem MQL) e o usuário quiser
o plano, siga para `/plano-google-ads`, reaproveitando os mesmos exports e a planilha de leads. Publique as duas páginas no
mesmo link do cliente: `references/publicacao.md`.

## Sub-playbooks por cliente

Opcional. Este repositório não traz calibração de nenhum projeto: quem usa começa pelas perguntas acima. Se quiser não
reperguntar CRM e acesso nas próximas rodadas, crie `otimizacao-campanhas-<cliente>.md` (modelo em
`references/sub-playbook-modelo.md`) nesta pasta, sem versionar em repositório público, com:

- CRM usado e como acessar (MCP, API, credenciais: nunca a credencial em si, aponte para onde ela mora,
  ex.: `.env` do projeto).
- Etapa de MQL confirmada (nome exato no pipeline) e nome do funil/pipeline.
- Peculiaridade do export CSV de Meta/Google daquele cliente (nomenclatura de campanha,
  se usa UTM customizada, timezone, etc.).
- Data da última calibração.

Nas rodadas seguintes com esse cliente, ainda confirmar rapidamente a etapa de MQL
antes de calcular (pode ter mudado o funil) — o sub-playbook evita reperguntar CRM e
credenciais, não substitui a confirmação da etapa.

## Definition of Done

- CRM, período e etapa de MQL confirmados explicitamente pelo usuário nesta rodada (não
  herdados sem confirmação, mesmo com sub-playbook existente).
- Qualificação calculada pelo **histórico** de etapas (maior estágio já alcançado), não
  só pela etapa atual — se o CRM não expõe histórico, isso está sinalizado explicitamente
  como limitação, não escondido.
- Todo lead MQL sem match de UTM está listado, não descartado silenciosamente.
- Ranking usa Custo por MQL / Taxa de MQL, nunca CPL isolado.
- Aba de Desqualificação presente, escopo restrito a quem **nunca** alcançou MQL — com
  taxa de desqualificação geral e ranking por motivo de perda — leads perdidos sem
  motivo preenchido sinalizados, não descartados.
- Tabela "Qualificados que não fecharam" presente na aba de Qualificação, com o motivo
  de perda de quem qualificou e depois foi perdido.
- Aba Geral presente e como aba padrão, com Qualificado + Desqualificado + Em aberto
  somando 100% dos leads em cada linha da árvore.
- HTML segue a estrutura de `assets/reference-otimizacao-campanhas.html` (três abas) e passou no `scripts/validar.py`.
- Nenhum nome, telefone ou e-mail de lead na página publicada.
- Recomendação de investir mais/menos (aba MQL) e de menor/maior taxa de desqualificação
  (aba Desqualificação) aparece logo no topo de cada aba, não enterrada nas tabelas.

## Referências

- `references/regua-do-funil.md`: MQL, SQL e Venda, regra cumulativa, coorte, régua pela conversa, projetado × realizado.
- `references/crm-e-fontes.md`: Kommo, Bitrix, CRM sem API, planilha, exports de mídia, NEKT/Flow.
- `references/config.md`: todos os campos do `config.json` e do `dados.json`.
- `references/sprint-growth.md`: Doc de comitê / Sprint Growth, seções, formatação, tags no Ekyte, 5W1H.
- `references/armadilhas.md`: erros que já aconteceram em rodadas reais e como evitar.
- `references/publicacao.md`: Vercel, link único por cliente, validação visual.
- `references/sub-playbook-modelo.md`: modelo opcional de calibração por projeto.
