# Régua do funil: MQL, SQL e Venda

A etapa muda em todo cliente, e às vezes de uma rodada para outra. **Confirme com o usuário, a cada rodada, a etapa exata de MQL, SQL e Venda.** Nunca infira pelo nome.

## Regra cumulativa e histórico

Quem passou de uma etapa continua contando nela:

| Métrica | Quem conta |
|---|---|
| MQL | Alcançou a etapa de MQL ou posterior alguma vez |
| SQL | Alcançou a etapa de SQL ou posterior alguma vez |
| Venda | Alcançou uma etapa de venda (podem ser mais de uma, ex.: Contrato assinado + Venda ganha) |

Compare pela **ordem real do funil** (`etapas.ordem` no config; no Kommo, o `sort` da etapa), nunca pelo número do id.

**A etapa de perda nunca entra na ordem.** No Kommo, Perdido tem `sort` maior que Venda só para ficar no fim do kanban. Se entrar, todo lead perdido vira MQL+ e até Venda+. Ela é lida só pela etapa atual. Sem histórico disponível, use a etapa atual e **declare no dashboard** que a qualificação pode estar subestimada (`leads.sem_historico: true`).

## Três baldes, sem sobreposição

Todo lead pago cai em exatamente um:

- **Qualificado:** alcançou MQL+. Se a etapa atual é Perdido, é "qualificado que não fechou": problema comercial, não de mídia.
- **Desqualificado:** etapa atual é Perdido e nunca alcançou MQL.
- **Em aberto:** o resto. Ainda não decidido.

## Coorte

- Lead entra pela **data de criação** dentro do período. O histórico vai até hoje: lead de setembro pode qualificar em outubro.
- **Não filtre pelo funil atual.** O time move lead para funis de recall, onboarding ou financeiro. Quem passou pelo funil-alvo continua na coorte, pelos eventos. Numa rodada real esse filtro perdeu quase metade dos leads.
- Coorte recente tem Venda baixa porque ainda não amadureceu. Em ciclo longo, Venda = 0 no período não é alerta: acompanhe a coorte nas rodadas seguintes.
- Mudou a régua entre rodadas? Avise: os números não são comparáveis com a rodada anterior.
- Recompra e carteira ficam fora da análise de mídia. Identifique pelo funil ou pelo nome do lead e tire da coorte.

## Campos "MQL = Sim" no CRM

Campos personalizados de MQL/SQL podem ser marcados em outra etapa e não ser a régua combinada. Numa rodada real, usá-los deu 18 MQL quando o certo eram 31. Use a etapa confirmada, a menos que o usuário diga o contrário.

## Quando a etapa do CRM não é confiável: régua pela conversa

Se o time não atualiza o CRM (reunião feita com o lead ainda em "Qualificação"), e o usuário pedir, classifique pela conversa:

1. Baixe as timelines (no Kommo, `/ajax/v3/leads/{id}/events_timeline?limit=100`, com o cookie de sessão que o usuário fornece. Vale poucos minutos: nunca salve em arquivo versionado).
2. Separe autores: bot de entrada, vendedor e lead. Atenção: em algumas contas o autor "Robot" é o **vendedor digitando pelo celular**, não automação.
3. Defina a régua com o usuário antes de classificar. Exemplo: MQL = conversou com o vendedor depois da automação, com interesse real; SQL = reunião combinada, ou proposta com quantidade; Venda = pedido fechado na conversa.
4. Leia um a um os leads com sinal forte (proposta, cadastro, amostra, pedido). O resto pode ir por regra.
5. Etapa final = o maior entre o CRM e a conversa. Liste os leads com etapa desatualizada para o comercial corrigir, **sem alterar o CRM**.

## Quando o CRM não tem etapa de MQL

Alguns ERPs só expõem o resultado. Nesse caso **Qualificado = Venda**, por acordo com o usuário. Troque os rótulos no dashboard e declare a régua no cabeçalho. "Qualificados que não fecharam" deixa de se aplicar.

## Projetado × realizado

- **Realizado** consolidado: planilha de acompanhamento do cliente (Growth Pack), aba mensal.
- **Projetado e meta**: planilha ou simulação do Break-even do cliente.
- Nunca use o CRM bruto como realizado consolidado do mês sem conferir: as contagens diferem por régua, janela e recompra.
- Compare ritmo com meta proporcional aos dias corridos do mês.
