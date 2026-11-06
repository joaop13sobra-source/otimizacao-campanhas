# Armadilhas (já aconteceram em rodadas reais)

Vale a mesma regra para todas: **achou uma estranheza, relate. Não corrija em silêncio nem descarte lead.**

## Investimento

| Sintoma | Causa | O que fazer |
|---|---|---|
| Google inflado ~6× | Linhas "Total:" somadas, às vezes fora da primeira coluna | `comum.tabela` já descarta. Confira com `conferir_total` |
| Valor 100× errado | Meta em formato US e Google em BR no mesmo script | `formato_numero` por arquivo |
| Export de outro cliente | Conta compartilhada; nome do arquivo não identifica | Confira os nomes de campanha |
| Gasto sumiu num período | Campanha pausada ou conta sem veicular | Não é bug: declare. Plataforma vazia mostra estado vazio |

Campanhas com outro objetivo (recrutamento, por exemplo) saem do investimento e dos leads pelo `excluir.campanhas_regex`. Não são lacuna de rastreio.

## UTM e cruzamento

- **Canal errado:** classifique pelo nome real da campanha, não por padrão de texto. A origem só desempata. `utm_source` pode ser o posicionamento (`Instagram_Feed`).
- **`{{campaign.name}}` literal** é macro do Meta que não resolveu; chave simples (`{campaignid}`) é ValueTrack do Google. Vai para nó sintético, sem descartar. Numa conta, 47% dos leads do Meta estavam assim.
- **Slug genérico:** campanhas diferentes com o mesmo `utm_campaign`. Resolva por palavra-chave, se for única (o script já tenta), por `apelidos_campanha`, pela data em que cada campanha rodou ou com `agrupar_campanhas`.
- **Isso não é "erro do cliente".** Dois anúncios com o mesmo `utm_medium` podem ser intencionais (mesmo criativo reaproveitado). Descreva como ambiguidade e confirme antes de recomendar mudança.
- **Hífen, espaço e `+`** são equivalentes na comparação (`norm`). Rode a checagem de slug ambíguo **antes** de qualquer fuzzy match: fuzzy resolve por acidente o que deveria ficar ambíguo.
- **Campanha renomeada** no meio do período: leads gravam o nome antigo. Use `apelidos_campanha`.
- **Anúncio ou conjunto excluído da conta:** a UTM não aparece no export. Vira nó sintético com investimento 0, sem rateio inventado.
- **`utm_medium = paid_social`** é valor fixo gravado quando o parâmetro dinâmico não resolve. Vai para nó sintético dentro da campanha certa.
- **Formulário sem repasse de UTM:** gap de rastreio real. Lead que se cadastrou duas vezes pode perder a origem. Cruze com a planilha bruta de envios por telefone e horário (diferença de 1 a 2 segundos).
- **Telefone inválido na planilha** (`#ERROR!`): caia para o e-mail.
- **Planilha com linhas duplicadas** (mesmo telefone e minuto): pegue a linha mais próxima do `criado_em`.
- **Cobertura baixa:** quando a maioria dos qualificados chega por WhatsApp ou ligação, sem UTM, o custo/MQL fica superestimado. Mostre a cobertura e diga.

## Árvore e agregação

- **Motivo de perda:** some só nas folhas. Somar por todos os níveis conta cada lead 3×.
- **Nó sintético** tem custo 0 e pareceria a melhor campanha: fica fora do ranking de custo (`invest > 0`) e das médias.
- **Nó sem drill-down:** a soma dos filhos tem que bater com o pai. O `montar_dados.py` confere.
- **Leads de teste** escondidos no CRM, às vezes já perdidos e sem chamar atenção: `leads_teste_regex`, e leia a lista antes de fechar.

## Leitura

- **Taxa alta de "Sem resposta"** é SLA comercial, não mídia. Reporte separado da leitura de campanha.
- **Muitos leads parados na primeira etapa ou no SDR IA** é vazamento operacional, não de público.
- **Motivo estranho depois de qualificar** ("Sem perfil" depois de MQL): reporte como está, pode ser engano do comercial.
- **Volume baixo:** menos de 3 MQL fica fora do ranking de custo; menos de 8 leads, fora dos rankings de taxa. Continua nas tabelas.
- **Rankings são candidatos, não sentença.** Marca tem volume com teto: escalar verba de termo de marca não traz mais leads.

## Validação

- Rode o `validar.py`. Um `const` usado antes de declarado já derrubou um dashboard inteiro sem erro aparente; ler o código não pegou.
- O texto de `notas` é escrito à mão: confira cada número contra o `dados.json` antes de publicar.
