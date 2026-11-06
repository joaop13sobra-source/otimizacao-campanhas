# CRM e fontes de mídia

Todo acesso a CRM nesta skill é **somente leitura**. Token fica em variável de ambiente ou `.env` do cliente, nunca em arquivo versionado, página ou resposta.

## Kommo

`scripts/puxar_kommo.py` cobre o caminho comum. O que a API exige:

| Precisa de | Chamada | Atenção |
|---|---|---|
| Funis e etapas | `GET /api/v4/leads/pipelines` | Puxe ao vivo em toda rodada: etapas mudam |
| Leads | `GET /api/v4/leads?filter[created_at][from]=&filter[created_at][to]=&with=contacts,loss_reason&limit=250&page=N` | Sem filtrar funil. Resposta 204 = acabou |
| Histórico | `GET /api/v4/events?filter[type][]=lead_status_changed&filter[entity]=lead&filter[created_at][from]=&limit=100&page=N` | `limit` máximo é 100. Vem de todos os funis misturados |
| Contatos | `GET /api/v4/contacts?filter[id][]=...` | Lote de 10 ids. Telefone e e-mail ficam aqui, não no lead |
| Motivos nativos | `GET /api/v4/leads/loss_reasons` | Muitas contas usam campo personalizado: confira qual está preenchido |

Peculiaridades que variam por conta, e vão no sub-playbook:

- UTM no lead ou no **contato** (`utm_no_contato: true`).
- Motivo de perda na lista nativa ou em campo personalizado (`campo_motivo_perda`). Conte o preenchimento: pode haver campo antigo quase vazio ao lado do campo real.
- Mais de um funil de venda (um por vendedor, ou SDR + vendedores). Liste todos em `kommo.funis` e dê a ordem unificada em `etapas.ordem`.
- Token de integração privada pode vir sem refresh token e vence: 401 significa renovar manualmente.
- **Quando o UTM do CRM não presta** (formulário gravado como `utm_campaign`, por exemplo): use a planilha de leads alimentada direto pelo evento de conversão. Cruze por telefone (DDD + últimos 8 dígitos), depois e-mail, e prefira a linha mais próxima do `criado_em`. Passe o resultado como planilha mapeada em `leads.colunas`.

## Bitrix24

Sem script pronto: use um webhook de entrada com permissão só de CRM e gere um arquivo no formato normalizado (abaixo).

- `crm.dealcategory.list` e `crm.dealcategory.stage.list` listam funis e etapas.
- `crm.deal.list` pagina de 50 em 50 (`start`).
- `crm.stagehistory.list` (`entityTypeId: 2`) traz o histórico de etapas.
- **Export manual pode vir filtrado:** o CSV de negócios às vezes só traz fases abertas, sem ganhos e perdidos. Confira as fases presentes antes de calcular. Faltando, complete com um export anterior ou peça de novo.

## CRM sem API, ERP ou planilha

Mapeie as colunas em `leads.colunas` e defina `leads.sem_historico: true` se só houver status atual.

- Datas podem vir em mais de um formato na mesma planilha (`2026-04-18 11:42:57`, `31/07/202609:05:19`, `1 de setembro de 2025 às 10:46`). O `comum.data()` aceita esses. Confira `sem_data` na saída: já se perderam centenas de linhas por isso.
- Status "válido/inválido" de planilha de leads costuma ser marcação de formulário, não qualidade nem cobertura. Não use como régua sem confirmar.
- Colunas UTM podem vir trocadas conforme a versão do formulário. Se o nome não bater com o conteúdo, classifique pelos valores conhecidos (nomes de campanha, público e anúncio da mídia).
- Formato normalizado, para qualquer fonte: lista JSON com `id`, `nome`, `criado_em`, `etapa_atual`, `historico` (lista de nomes de etapa), `motivo_perda`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`. Aponte em `leads.arquivo_normalizado`.

## Exports de mídia

**Confirme que o arquivo é do cliente certo**, pelos nomes das campanhas: em conta compartilhada o nome do arquivo não identifica o cliente.

| Plataforma | Exports | Armadilhas |
|---|---|---|
| Meta Ads | Relatório no nível de **anúncio**: campanha, conjunto, anúncio, valor | Número em formato US (`1183.83`) |
| Google Ads | Anúncios (com "Sufixo do URL final") e palavras-chave da rede de pesquisa | Número em formato BR. Título e período antes do cabeçalho. Linhas "Total:" em qualquer coluna, inclusive em "Tipo de corresp." |

PMax não tem grupo, anúncio nem palavra-chave nos relatórios comuns: fica só no nível de campanha, sem filhos. Exporte com UI do Google Ads, não o Editor.

## NEKT / Flow (MCP do Cockpit, opcional)

Permite puxar mídia sem CSV. Quem tem o MCP `cockpit` conectado:

- `flow_project_data_list_connections` lista as contas conectadas do projeto.
- `flow_media_query` roda SQL direto. É BigQuery: use `CAST(... AS FLOAT64)`, liste colunas (`SELECT *` falha em ARRAY/STRUCT), não use `UNNEST`, e filtre `account_id` sem o prefixo `act_`.
- `flow_media_query_reports` traz leads do gerenciador (`actionPresets: ["leads"]`). Pagine com `offset`: períodos longos passam de 500 linhas.

| Canal | Tabela | Colunas úteis |
|---|---|---|
| Meta | `*_adsinsights` | `date_start, campaign_name, adset_name, ad_name, spend, impressions, clicks` |
| Google anúncio | `*_ad_performance` | `campaign_name, ad_group_name, ad_group_ad_ad_id, date, metrics_cost_micros, metrics_clicks, metrics_conversions` |
| Google campanha | `*_campaign_performance` | `campaign_name, date, metrics_cost_micros, metrics_conversions` |
| Google palavra | `*_keyword_performance` | `campaign_name, ad_group_name, keyword_text, keyword_match_type, metrics_cost_micros` |
| Google termo | `*_search_term_performance` | `search_term, metrics_cost_micros` |
| Google sufixo | `*_ad` | `a.ad.final_url_suffix` (struct: precisa nomear), join `ad_group_ad_ad_id = a.id` |

Custo do Google = `metrics_cost_micros / 1000000`. Salve o resultado em CSV com as colunas do config e siga o fluxo normal.
