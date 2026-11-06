# Coleta de dados

Peça tudo de uma vez, com o período exato. Quanto mais completo o pacote, menos idas e vindas. Os nomes de menu do Google Ads mudam; o que importa são as **tabelas e as colunas** abaixo. Em cada tabela, defina o período, adicione as colunas e use o ícone de download em `.csv`.

## 1. Google Ads (obrigatório)

Período: o que será analisado (ex.: 01/10 a 19/10) e, se possível, o mês anterior inteiro **segmentado por mês** (Segmentar > Tempo > Mês) para a comparação.

| Relatório | Colunas mínimas | Para que serve |
|---|---|---|
| **Campanhas** | Status, Orçamento, Tipo de estratégia de lances, Custo, Cliques, Impr., Conversões, Custo/conv., Parcela de impressões da rede de pesquisa, Parcela de impr. perdida (orçamento), Parcela de impr. perdida (classificação), Motivos do status | Diagnóstico, orçamento limitando, anúncios reprovados |
| **Grupos de anúncios** | Status, Campanha, Custo, Cliques/Interações, Impr., Conversões | Peso de cada grupo e decisão de virar campanha |
| **Palavras-chave da rede de pesquisa** | Status, Tipo de correspondência, Campanha, Grupo, Custo, Cliques/Interações, Impr., Conversões, Índice de qualidade | Decisão por palavra-chave |
| **Termos de pesquisa** (todos, não só os adicionados) | Termo, Tipo de correspondência, Adicionada/excluída, Campanha, Grupo, Custo, Cliques, Impr., Conversões | Negativas e temas de busca |
| **Anúncios** | Status de aprovação, Política (motivo), Campanha, Grupo, Custo, Cliques, Conversões, Qualidade do anúncio | Reprovações e custo por anúncio |

Extras que mudam a qualidade da análise:
- **Palavras-chave negativas atuais** (conta, campanha, grupo e listas compartilhadas): evita duplicar o que já existe.
- **Ações de conversão**: qual é primária, quantas conversões cada uma gerou, **o que dispara** a ação (envio do formulário, clique no WhatsApp, ligação).
- **Locais** (por cidade/região): de onde vêm os cliques e as conversões.
- **Histórico de alterações** do período em que o CPL mudou: explica degraus de conversão e de CPC.
- **Estratégia de lances e orçamento** de cada campanha (já vem no relatório de campanhas, se a coluna for adicionada).

Confira na abertura: **a conta é do cliente certo** (nomes das campanhas e dos grupos) e o período é o pedido. O Google oculta termos de baixo volume: espere cobrir de 60% a 80% do gasto.

## 2. Planilha de leads (para custo por venda)

Uma linha por lead, com **data, telefone, status, cidade, bairro** e as UTMs: `utm_campaign`, `utm_medium` (grupo), `utm_content` (anúncio), `utm_term` (palavra-chave). O telefone é a chave do cruzamento.

- Leia por CSV exportado ou por Google Sheets com uma Service Account do Google Cloud com acesso de leitura à planilha (compartilhe a planilha com o e-mail da conta de serviço).
- Verifique **todos os formatos de data** da aba (a planilha pode mudar de formato no meio do período).
- Confira como as UTMs mapeiam para o Google Ads: `utm_campaign` = campanha, `utm_medium` = grupo de anúncios, `utm_content` = anúncio, `utm_term` = palavra-chave (não a pesquisa). Cada cliente nomeia diferente: monte o `mapa_campanhas` e o `mapa_grupos` no config.

## 3. Relatório de vendas do CRM

CSV com **telefone** e o **desfecho** de cada lead (venda, perdido, sem viabilidade, em andamento...), mais cidade/bairro, plano e status do contrato quando existirem. Nem sempre há data: tudo bem, o cruzamento ignora a data.

Defina com o usuário **o que é venda** (ex.: contrato ativo ou pré-contrato, sem as desistências) e escreva as regras de estado no config (`vendas.crm.estados`). Nunca infira pelo nome do estado.

Quando o CRM tem API (Kommo, Bitrix, RD Station, ou um ERP que exporte relatório em CSV), prefira exportar o mesmo recorte do período.

## 4. Referência de resultado

- **Planilha de acompanhamento mensal:** investimento, leads, vendas e CPL do mês anterior e do corrente, por canal. O CPL do painel deve bater com o dessa planilha; se não bater, descubra por quê antes de analisar.
- **Projeção/meta do mês**: leads, MQL e vendas esperados (break-even), se o cliente tiver.

## 5. Semrush

A chave vem da variável `SEMRUSH_API_KEY` ou de um arquivo de texto indicado em `--chave-arquivo` (apenas a chave de 32 caracteres, ou `Apikey <chave>`). Nunca imprima a chave. Confira o saldo de unidades antes (`semrush.py unidades`).

## Checklist de recebimento

- [ ] Arquivos do cliente certo e do período certo.
- [ ] Relatório de campanhas com colunas de parcela de impressões e motivos do status.
- [ ] Termos de pesquisa completos (não filtrados por "adicionados").
- [ ] Planilha de leads com telefone e UTMs; datas lidas por todos os formatos.
- [ ] Relatório do CRM com telefone e definição de venda confirmada.
- [ ] Planilha de acompanhamento do mês anterior para a comparação.
- [ ] Lista do que **não** veio (anúncios, negativas, locais, histórico) registrada em "Dados e limites".
