# Sprint Growth: diagnóstico no Doc de comitê e tasks

Saída opcional. O dashboard responde por campanha; o Doc é o insumo do comitê, comparável semana a semana, com decisão por anúncio.

## Antes de escrever

1. Leia o Doc pela Docs API (`documents().get(includeTabsContent=True)`) e ache a aba-alvo pelo **título e pelo pai**. O link recebido pode abrir na aba de outra pessoa ou na aba modelo. A aba tem que estar vazia; se não estiver, pergunte.
2. Use a aba da **semana anterior** do mesmo cliente como modelo e como base de comparação.
3. Confira se as recomendações da semana anterior foram executadas, olhando o gasto por anúncio dos últimos 7 dias. Diga quando não foram (ex.: "proposto na semana 42 e não feito, gastou R$ X de 20 a 26/10").

## Estrutura, nesta ordem

- **Título** Heading 2 com o nome do cliente.
- **Resumo:** (negrito) período e % do mês, investimento por canal, leads, MQL, SQL, vendas e **a decisão de verba já no texto**, com os itens-chave em negrito.
- **Dashboard:** link do HTML publicado + uma linha do que tem nele.
- Parágrafo em itálico com **como foi feito o cruzamento**: fontes e datas dos exports, chaves de match e % casado, régua de MQL/SQL/venda e regra do histórico, ligação UTM × mídia, origem do investimento e o que ficou de fora.

| Seção | Conteúdo |
|---|---|
| `1. Funil completo` | Semana anterior × atual; taxas entre etapas; ritmo × meta do mês (Break-even); qualificado × desqualificado × em aberto |
| `2. Funil no CRM e gargalo` | Etapa atual dos leads do período com tempo na etapa; bullets do gargalo |
| `3. Por canal` | Meta × Google: invest., leads, MQL, SQL, vendas, CPL, custo/MQL, Lead → MQL, CAC |
| `4. Leads de campanha sem UTM` | Por tipo: vazio, macro sem resolver, sem match no CRM |
| `5. Ranking de campanhas` | Meta campanha / conjunto / anúncio (anúncio com "Gasto últimos 7 dias"); Google campanha / anúncio / palavra-chave; bullets de melhor e pior, e "custo por MQL não é tudo" |
| `6. Onde investir mais, menos e o que desativar` | Tabelas "Investir mais", "Manter sem escalar", "Investir menos ou pausar" (Item · Nível · Números · Ação) e "Anúncios para desativar" (com gasto dos últimos 7 dias), fechando com **Pra onde vai a verba** |
| `Demografia` (opcional) | Idade, gênero e posicionamento, quando o comitê pedir |
| `7. UTMs e contas` | Situação de cada conexão e export |
| `Próximos passos` | Bullets com o foco em negrito |
| `Planos de ação (5W1H)` | O quê · Por quê · Como · Quem · Quando · Onde/métrica. Responsáveis e prazos são **proposta** para o comitê |

Termina com uma linha divisória.

**Não escale só por custo por MQL:** MQL barato com poucos SQL é sinal de manter e reavaliar. Decida olhando até onde a campanha chega no funil.

## Formatação

Fonte Inter. Heading 2 17pt negrito, Heading 3 13pt negrito, corpo 14pt com 12pt antes e depois. Tabelas com borda cinza 0.6 de 0.5pt, padding 5, cabeçalho em negrito centralizado, larguras fixas em pt (aba pageless aceita tabela mais larga que a página).

**Nunca nomes de leads nem de vendedores:** o Doc costuma ser editável por link.

## Como escrever

```bash
cd assets/docs-diagnostico
python3 -I exemplo-conteudo.py <dados.json> <contexto.json> --saida elementos.json   # adapte ao cliente
export GOOGLE_SERVICE_ACCOUNT_JSON=~/.config/google/service-account.json
python3 -I build_doc.py <documentId> <tabId> "<título exato da aba>" elementos.json
```

- Requisitos: `google-api-python-client` e `google-auth`, conta de serviço com **Google Docs API ativada no projeto dela** e Doc compartilhado com ela, ou editável por link.
- O montador usa `requiredRevisionId` em cada envio, insere a tabela no `\n` do parágrafo anterior (senão a API cria um parágrafo vazio antes) e apaga os vazios no fim.
- Depois de escrever, exporte a aba em PDF (escopo `drive.readonly`, `export?format=pdf&tab=<tabId>`) e olhe as páginas. No PDF de aba pageless, rótulo depois de tabela larga aparece centralizado: é efeito do export, não do Doc.
- A API não insere régua horizontal: use borda inferior num parágrafo vazio. A edição fica no histórico com o nome da conta de serviço.

## Tasks no Ekyte a partir da reunião

Sempre que for criar tasks de uma reunião de Sprint Growth:

- Toda task leva duas tags: **`SPRINT GROWTH`** e **`SEMANA <N>`**, onde N é a semana **do ano** da data da reunião (não da data de hoje).
- O id da tag `SEMANA <N>` muda toda semana: busque pelo nome exato em `list_tags` e, se não existir, crie com `create_tag`.
- `update_task_tags` **substitui** a lista: leia as tags atuais em `get_detailed_task` e envie a união.
- O MCP exige `ctcTaskId` (mesmo valor de `taskId`) como parâmetro de topo, embora não apareça no schema.
- Toda task precisa de data de executar e de concluir explícitas.
