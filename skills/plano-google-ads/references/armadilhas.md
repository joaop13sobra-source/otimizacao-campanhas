# Armadilhas (erros que já aconteceram)

Cada item custou retrabalho em um caso real (provedor regional de internet, outubro/2026). Leia antes de começar.

## Dados

1. **A planilha de leads mudou o formato da data no meio do período.** Até 30/07 era `2026-04-18 11:42:57`; depois, `31/07/202609:05:19` (sem espaço). Um leitor que só entende o primeiro descarta todas as linhas novas **sem avisar**: faltaram 593 de 2.284 linhas e eu publiquei uma "queda de captura em 02/10" que não existia, "só 11 de 57 vendas rastreadas" (eram 49) e "93% dos leads de marca em setembro" (eram 62%).
   - Defesa: `cruzar_vendas.py` tenta vários formatos e devolve `qualidade.sem_data`; **sem_data deve ser 0**. Compare a contagem de linhas lidas com a contagem de linhas da aba.
   - Se uma conclusão forte aparece de repente ("o formulário parou", "as vendas sumiram"), duvide do parse antes de acreditar.
2. **Contar linhas não é contar telefones.** "72 de 200 sem registro" saiu de uma subtração em cima de linhas; o correto, por telefones únicos, eram 87. Sempre por telefone único e com a base do mesmo recorte.
3. **O STATUS da planilha não é cobertura nem falta de venda.** Um bairro/cidade vinha 100% "inválido" (0 de 463 leads) e 21% dos leads viraram venda; 14 de 48 vendas vieram de leads "inválidos". Nunca use o status para cortar geografia nem para calcular "custo por lead válido". Cobertura vem do CRM ("sem viabilidade") por bairro e confirmada com o cliente.
4. **`utm_term` é a palavra-chave, não a pesquisa.** A venda por termo de pesquisa não é mensurável com a planilha; por palavra-chave, sim.
5. **Arquivo de outro cliente na mesma pasta.** Exports do Google Ads de duas contas chegaram juntos em Downloads. Confira nomes de campanha e de grupo antes de usar.
6. **Janelas diferentes.** O export do Ads ia até 19/10 e o relatório do CRM até 17/10. Use a janela do CRM e **escale o gasto** (`fracao_gasto`), rotulando "estimado". Compare só números do mesmo recorte.
7. **O Google oculta termos.** A tabela de termos cobre 60% a 80% do gasto. Escreva a cobertura na página e não conclua sobre o que não vê.
8. **Cidades com caixa diferente** (`Cidade Alfa` e `CIDADE ALFA`): normalize antes de agrupar.
9. **Leads têm três contagens** (Google, planilha, CRM) e nenhuma é "a certa": 212, 221 e 138 no caso real. Documente cada uma e use a mesma em cada tabela.

## Análise

10. **CPL ordena errado o custo por venda.** A palavra de melhor CPL tinha um dos piores custos por venda; a de pior CPL vendia no nível da marca. Eu tinha recomendado pausar a de pior CPL e tive de reverter. Decida por custo por venda quando houver venda.
11. **Negativas rendem pouco.** O cenário mais amplo deu −2,7% no CPL. Não venda negativa como solução.
12. **Duas formas de calcular o custo por venda por palavra-chave** deram números diferentes (CPL ÷ taxa de venda × gasto ÷ vendas). Use uma só, a do script (gasto estimado ÷ vendas), em todos os lugares.
13. **Cidade barata pode não ser armadilha.** Eu chamei uma cidade de "armadilha" por 71% de linhas sem viabilidade no CRM; por lead, 19% viraram venda a custo abaixo da média. Cruze sempre com o lead→venda antes de rotular.
14. **Taxa com poucas vendas engana.** Um anúncio com 0 de 4 leads não é "o pior". Mostre o n e use "indicativo" abaixo de 15 leads / 5 vendas.

## Semrush

15. **Concorrentes locais disfarçados de termo** (nomes de provedores regionais voltam como "internet + nome"). Cure à mão.
16. **Marca local subestimada:** 10 buscas no Semrush para um termo com 23 conversões na conta.
17. **CPC de referência com valores absurdos** em termos de grandes concorrentes; use só para ordenar.
18. **Distrito sem cobertura virou "oportunidade".** O Semrush devolveu um termo de um distrito que a empresa não atende. Toda palavra de localidade nova passa por checagem de cobertura no CRM, por bairro.
19. **Não pague unidades à toa:** descobrir com poucas sementes, curar, e só então `volumes --plano`.

## Publicação e comunicação

20. **Número dito na conversa precisa bater com a página.** Quando corrigir a página, corrija e avise também o que foi dito antes.
21. **Não imprima a chave do Semrush** nem outras credenciais; os scripts nunca a imprimem. Cuidado com comandos de `grep` que mascaram a chave de forma incompleta.
22. **O hub não tem senha.** Avise antes de o link circular com o cliente (ver `publicacao.md`).
23. **Filtros de saída enganam.** Um `grep -v warn` apagou da tela os alertas do tipo "warn" e eu quase "consertei" um bug que não existia. Leia a saída inteira quando algo parecer faltar.
24. **Corrigiu um erro? Registre.** Atualize a memória/sub-playbook do cliente com o aprendizado, para a próxima conta não repetir.
