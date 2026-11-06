# Formatos: config.json, dados.json e plano.json

## config.json (entrada de `analise.py`)

Modelo completo em `assets/config.exemplo.json`.

```jsonc
{
  "cliente": "Nome",
  "periodo": {"rotulo": "01 a 19/10/2026", "inicio": "2026-10-01", "fim": "2026-10-19"},
  "gads": {                        // CSVs exportados do Google Ads (pt-BR)
    "campanhas": "...", "grupos": "...", "palavras_chave": "...", "termos": "..."
  },
  "custo_total_conta": 3912.87,    // opcional: total do painel (evita diferença de centavos)
  "referencia": {"rotulo": "Setembro", "fonte": "planilha de acompanhamento", "custo": 5300.00, "cliques": 1560, "conversoes": 470},
  "campanha_marca": "Institucional",   // nome (sem os colchetes do prefixo) da campanha de marca
  "regex": {                       // aplicadas ao termo sem acento e em minúsculas
    "marca": "...", "concorrentes": "...", "fora_area": "...",
    "cidades": {"Nome exibido": "regex"},
    "locais_extra": "...",         // tokens de lugar que também tornam o termo "com cidade"
    "suporte": "...", "contato": "...",   // opcionais: há padrão (ver analise.py)
    "ruido": "..."                 // só para o filtro do Semrush
  },
  "negativas_extra": {"nome": "regex"},   // conjuntos extras de negativas (entram no Tier 1)
  "vendas": { ... }                // bloco opcional, ver abaixo
}
```

### Bloco `vendas`

```jsonc
"vendas": {
  "janela": {"inicio": "2026-10-01", "fim": "2026-10-17"},   // termina na data do relatório do CRM
  "gasto_janela_total": 3465.47,   // gasto do Ads na janela (planilha diária de resultados); gera a fração de escala
  // ou "fracao_gasto": 0.8857
  "leads": {
    "sheet_id": "...", "intervalo": "'Aba'!A1:X6000", "credencial": "~/.config/gcloud/sheets-service-account.json",
    // ou "csv": "caminho.csv", "sep": ","
    "formatos_data": ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y%H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"],
    "colunas": {"data": "...", "telefone": "...", "status": "...", "cidade": "...",
                "campanha": "utm_campaign", "grupo": "utm_medium", "anuncio": "utm_content", "termo": "utm_term"}
  },
  "crm": {
    "csv": "...", "sep": ";",
    "colunas": {"telefone": "Telefone", "tipo": "Tipo Relatório", "cidade": "Cidade"},
    "prioridade_tipos": ["VENDA", "EM ANDAMENTO", "PERDIDO"],  // ordem de escolha quando o telefone aparece mais de uma vez
    "estados": {
      "venda":  [{"onde": {"Tipo Relatório": ["VENCEMOS"], "!Status Contrato": ["Desistiu"]}}],
      "desq":   [{"onde": {"Tipo Relatório": ["SEM VIABILIDADE"]}, "motivo": "Sem viabilidade"},
                 {"onde": {"Tipo Relatório": ["PERDEMOS"]}, "motivo_col": "Motivo Perdemos", "motivo_padrao": "(sem motivo informado)"}],
      "aberto": [{"onde": {"Tipo Relatório": ["EM ANDAMENTO"]}}]
    }
  },
  "mapa_campanhas": {"valor_no_utm": "Nome limpo da campanha no Ads"},
  "mapa_grupos":    {"valor_no_utm": "Nome do grupo no Ads"}
}
```

Regras de estado: cada regra tem `onde` (coluna → valores aceitos; prefixo `!` exclui) e, para `desq`, o motivo (`motivo` fixo ou `motivo_col` com uma ou mais colunas). Ordem de avaliação: `venda`, `desq`, `aberto`. Sem regra = `aberto`.

## dados.json (saída de `analise.py`)

| Chave | Conteúdo |
|---|---|
| `meta` | cliente, período, data, arquivos |
| `kpis` | custo, cliques, conversões, CPL, CPC, conversão por clique |
| `referencia`, `decomposicao` | período anterior e a divisão da variação do CPL (`parte_cpc_pct`, `parte_conversao_pct`) |
| `campanhas`, `grupos` | tabelas com custo, CPC, CPL, parcela de impressões, perdida por orçamento/classificação, status, motivos |
| `termos`, `temas` | cobertura de termos visíveis e a tabela por tema |
| `marca_fora_da_campanha_de_marca` | gasto de marca fora da campanha de marca |
| `negativas` | `conjuntos` (custo, conversões, zero-conversão, top termos) e `cenarios` (`tier1`, `tier1_mais_concorrentes`) |
| `locais` | custo, conversões e CPL dos termos por cidade |
| `concorrentes` | termos de concorrente com clique e sem conversão |
| `palavras`, `palavras_resumo` | palavras-chave com gasto; totais (ampla, pausadas) |
| `termos_ativos`, `palavras_nomes` | listas compactas (sem dado pessoal) para marcar "novo" × "já na conta" |
| `alertas` | achados automáticos (`bad`, `warn`, `info`) |
| `vendas` | `qualidade`, `crm`, `leads`, `segmentos` (campanha, grupo, anúncio, anúncio por grupo, palavra, cidade, status), `motivos`, `arvore`, `palavras`, `fracao_gasto` |

## plano.json (entrada de `gerar_plano.py`)

Modelo completo em `assets/plano.exemplo.json`. Todas as chaves são opcionais: a seção sem conteúdo some.

### Sintaxe de template

`{{caminho.no.dados|formato}}`: busca o valor no `dados.json`. Listas por nome: `campanhas[nome=Campanha Core].cpl` (compara o início do texto, sem maiúsculas). Formatos: `brl` (R$ 1.234,56), `brl0`, `pct` (já em %), `pct0`, `frac` (fração 0,24 → 24,0%), `frac0`, `n0`, `n1`, `raw`.

Extra do Semrush: `{{semrush.grupo[titulo=Cidades-alvo].soma|n0}}` (soma dos volumes das palavras do grupo curado).

Caminho inexistente = erro (o gerador sai com código 2 e lista os caminhos). Texto com HTML simples (`<b>`) é aceito.

### Chaves

| Chave | Conteúdo |
|---|---|
| `cabecalho` | `titulo`, `titulo_aba`, `subtitulo`, `logo_cliente`, `logo_agencia`, `voltar`, `rodape` |
| `rotulos_campanha` | nome da campanha → rótulo exibido |
| `conversao_rotulo`, `data` | rótulo da ação de conversão; data de publicação |
| `resumo` | `lead`, `callouts[]` (`tipo` ""/`warn`/`bad`, `titulo`, `texto`), `alavancas[]` (`nome`, `evidencia`, `efeito`, `confianca`), `nota_alavancas`, `ocultar_alertas_auto`, `sem_callout_decomposicao` |
| `diagnostico` | `lead`, `bullets[]`, `nota`, `vendas_bullets[]` |
| `termos` | `exemplos_tema{}`, `bullets[]`, `mapa_cidades{}` (nome exibido → cidade normalizada da planilha), `obs_cidades{}`, `nota_cidades`, `callouts_cidades[]` |
| `negativas` | `cartoes[]` (`conjunto`, `tier` 1/2, `titulo`, `tags[]`, `nota`, `max`), `onde[]`, `texto_tier1`, `texto_tier2` |
| `palavras_chave` | `decisoes{}` (nome → `decisao`, `cor` ok/warn/bad, `porque`), `minimo_leads`, `nota` |
| `novas_palavras` | `intro`, `callouts[]`, `grupos[]` (`titulo`, `palavras[]`, `titulo_kpi`, `sub_kpi`, `nota`) |
| `estrutura` | `lead`, `campanhas[]` (`nome`, `objetivo`, `resumo_grupos`, `correspondencia`, `orcamento_dia`, `grupos[]` com `nome`, `palavras[]`, `obs`), `bullets[]`, `regras_palavras[]`, `destinos{}` |
| `checagens` | lista de textos |
| `plano_teste` | `etapas[]` (`data`, `titulo`, `itens[]`), `metas[]` (`indicador`, `hoje`, `meta`, `trava`), `nota` |
| `limites` | lista de textos (somam-se aos automáticos) |

Cidades da planilha são normalizadas (minúsculas, sem acento): `CIDADE ALFA` vira `cidade alfa`.
