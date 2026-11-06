# Formatos: `config.json` e `dados.json`

Modelo completo em `assets/config.exemplo.json`. Caminhos são relativos à pasta do config.

## `config.json`

| Campo | O que é |
|---|---|
| `cliente`, `crm`, `periodo.inicio`, `periodo.fim` | Cabeçalho do dashboard. Datas em `AAAA-MM-DD` |
| `etapas.ordem` | Etapas na ordem real do funil, **sem** a de perda |
| `etapas.mql`, `etapas.sql` | Etapa confirmada nesta rodada. Precisam estar em `ordem` |
| `etapas.venda` | Lista das etapas que contam como venda |
| `etapas.perdido` | Lista das etapas de perda |
| `etapas.ignorar` | Etapas que não contam em nada (ex.: funil de SDR antes da qualificação) |
| `etapas.rotulo_sql`, `rotulo_venda` | Rótulos no HTML (ex.: "Oportunidade") |
| `leads.arquivo_normalizado` | JSON de `puxar_kommo.py` ou equivalente. **Ou:** |
| `leads.arquivo`, `leads.colunas`, `leads.aba` | Planilha/CSV e mapa `{interno: "Coluna no arquivo"}` |
| `leads.separador_historico` | Separador das etapas na coluna `historico` |
| `leads.sem_historico` | `true` mostra o aviso de limitação no dashboard |
| `midia.meta`, `midia.google` | `arquivo`, `formato_numero` (`us`/`br`), `colunas`: `campanha`, `grupo`, `anuncio`, `invest` e opcional `sufixo` |
| `midia.google.palavras` | Export de palavras-chave: `palavra`, `campanha`, `grupo`, `invest` |
| `utm.<canal>.grupo`, `.anuncio`, `.palavra` | Qual campo UTM guarda cada nível nessa conta |
| `utm.<canal>.apelidos_campanha` | `{slug ou id da UTM: "Nome real da campanha"}` |
| `utm.<canal>.apelidos_grupo` | `{slug da UTM: "Nome real do grupo"}` |
| `agrupar_campanhas` | `{"Nome da linha": ["Campanha A", "Campanha B"]}`: quando UTMs não separam |
| `excluir.leads_teste_regex` | Remove leads de teste por nome/e-mail |
| `excluir.origens_organicas` | `utm_source` fora da análise de mídia |
| `excluir.campanhas_regex` | Campanhas com outro objetivo, fora da mídia **e** dos leads |
| `kommo.funis`, `utm_no_contato`, `campo_motivo_perda` | Só para `puxar_kommo.py` |
| `conferir_total.meta`, `.google` | Total do painel: o script sai com erro se o export não bater |
| `notas.*` | Texto da rodada (aceita HTML): `selo`, `geral`, `qualificacao`, `qualificados_perdidos`, `desqualificacao`, `secoes_extras_geral` |

## `dados.json`

```
META_TREE, GOOGLE_TREE    árvores de nós
GOOGLE_KEYWORDS           lista plana de nós por palavra-chave
LOSS_REASONS              [{name, qty}] de quem nunca qualificou
QUALIFIED_LOST_REASONS    [{name, qty}] de quem qualificou e foi perdido
por_mes, totais, qualidade, meta
```

Nó: `{id, name, invest, leads, mql, sql, venda, lost, qlost, lostReasons, qualifiedLostReasons, synthetic?, children?}`. `invest: null` aparece como "—" e fica fora de custos e rankings, para quando o export não traz gasto naquele nível.

## O que olhar em `qualidade`

`sem_utm`, `canal_desconhecido`, `campanha_sem_match`, `utm_quebrada`, `campanha_resolvida_por_palavra`, `organico`, `teste`, `sem_data`, `perdidos_sem_motivo`, `mql_fora_da_arvore`. Se muitos MQL ficaram fora da árvore, o custo por MQL está superestimado: **diga isso na entrega**.
