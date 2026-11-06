# Estrutura de campanhas (playbook)

Esqueleto de Search para contas de geração de lead com área de atuação limitada (provedor, clínica, escola, serviço local). Foi desenhado para um provedor regional de internet; adapte o que não valer para o negócio do cliente, mas mantenha a lógica: **cada campanha tem uma intenção, um orçamento e uma regra de correspondência próprios**.

## 1. As quatro campanhas

| Campanha | Intenção | Palavras | Correspondência | Orçamento inicial |
|---|---|---|---|---|
| **Marca** | Quem já procura o cliente | marca pura, marca + contato (whatsapp/telefone), marca + cidade | Exata e frase; negativas de suporte | Gasto atual da marca + vazamento da campanha de genéricos + impressões perdidas por verba |
| **Local** | Quem busca o serviço nas cidades atendidas | Um grupo por cidade (ou região), termos "serviço + cidade" | Frase; exata nos de 100+ buscas | Pequeno: a demanda local costuma ser pequena |
| **Intenção alta** (substitui a de genéricos) | Quem compara ou checa disponibilidade | Disponibilidade e "perto de mim"; planos e preço; produto (o que a empresa vende); genéricos que já convertem | Frase e exata, **sem ampla** | O que sobrar, movido por custo por venda |
| **Conquista** (opcional) | Quem busca concorrente | Nomes de concorrentes | Exata | Teste pequeno, **só se o CRM mostrar venda desses termos** |

Para negócio sem recorte geográfico forte, troque **Local** por **Serviço/produto principal** (um grupo por linha de produto) e mantenha o resto.

Regras que valem para todas:
- **Marca só na campanha de marca.** As demais recebem negativa de marca exata.
- **Orçamento total mantido** no primeiro ciclo, para o CPL ser comparável antes e depois.
- Orçamento inicial é **hipótese**: a regra de ajuste é mover verba de quem tem custo por venda mais alto para quem tem o mais baixo, a cada 14 dias.
- **Sem correspondência ampla** nas campanhas genéricas enquanto o índice de qualidade for baixo e houver termos soltos entrando.

## 2. Grupos de anúncios que viram campanha

Promova um grupo a campanha quando ele (a) pesa mais de ~30% do gasto da campanha, (b) divide o teto de orçamento com outro grupo, ou (c) tem um custo por venda que justifica orçamento próprio. A promoção permite cortar palavras fracas e escalar as fortes sem mexer no vizinho. Preencha `estrutura.destinos` com o destino de cada grupo atual (migrar, virar campanha, manter).

## 3. Lance

1. **Comece manual** (ou maximizar cliques com teto de CPC).
2. Só ligue **maximizar conversões com CPA alvo** quando: a ação de conversão estiver validada (o que dispara, conta o que deve) **e** a campanha tiver 30 ou mais conversões por mês.
3. Não mexa em lance na primeira semana da estrutura nova (aprendizado).
4. Lance inteligente aprende com a conversão que o Google vê. Se o número do Google, da planilha e do CRM divergem muito, **entenda a divergência antes**.

## 4. Geografia

- Presença nos municípios atendidos (não "interesse").
- Exclusão de áreas sem viabilidade **por bairro**, a partir do CRM (relatório de "sem viabilidade"), e confirmada com o cliente. Teste segmentação por CEP quando o cliente tiver a lista de cobertura.
- Nunca corte uma cidade pelo STATUS da planilha de leads nem por CPL baixo/alto: confira taxa de venda e custo por venda.

## 5. Anúncios, extensões e páginas

- **Anúncios:** pelo menos um anúncio responsivo por grupo, com a cidade/serviço no título; corrija os reprovados **antes** de qualquer migração. Compare anúncios dentro do mesmo grupo (o melhor muda de grupo para grupo); descubra o que muda no texto e replique.
- **Extensões:** links de site (planos, consultar disponibilidade, WhatsApp), chamada/WhatsApp, local, frases de destaque (diferenciais comprovados do cliente, nada que o cliente não possa sustentar).
- **Páginas:** uma LP por campanha; o grupo de disponibilidade precisa de "consultar disponibilidade". Respeite decisões do cliente sobre o formulário (ex.: campo de bairro aberto).
- **Rastreio:** documente o que dispara a ação de conversão e o que chega ao CRM.

## 6. Quando a demanda de busca não comporta a verba

Some os volumes mensais (Semrush) de marca, locais e intenção alta. Se a soma local for pequena e a campanha de genéricos já aparecer como "limitada pelo volume de pesquisas", **a verba planejada não cabe só em Search**. Diga isso no resumo e leve a decisão (outros canais, expansão de área, retomada de outros canais) ao check-in. Escalar lance para "gastar" verba só encarece o clique.

## 7. Plano de teste

| Quando | O quê |
|---|---|
| Semana 0 | Checagens (anúncios, conversão, captura de leads) e higiene (negativas Tier 1, pausar o que não converte) |
| Check-in | Decisões com o cliente: cobertura por bairro, canais, verba oficial |
| Semana 1 | Criar a estrutura nova; negativas de marca nas demais; orçamento total mantido; sem mexer em lance |
| Semana 3 | Leitura de 14 dias: leads × vendas do CRM por campanha; negativas Tier 2; mover verba pelo menor custo por venda |

**Metas e travas** (sempre em par):
- CPL: meta = efeito calculado dos cenários (higiene + realocação), nunca promessa; trava = não subir além do valor atual.
- Custo por venda: manter ou reduzir; trava = não passar de +10%.
- Leads por dia: manter; trava = não cair abaixo de 85% do atual.
- Anúncios aprovados: 100%.

## 8. Checagens antes de mexer (sempre)

1. Anúncios reprovados (relatório de anúncios, motivo de política).
2. Conversão por clique: a LP ou o formulário mudou? O que dispara a ação "Lead"?
3. Leads sem registro no CRM: quantos telefones da planilha não aparecem no relatório comercial.
4. Locais: de onde vêm os cliques de palavras com escopo largo (estado, "RJ", "SP").
5. Estratégia de lances atual.
