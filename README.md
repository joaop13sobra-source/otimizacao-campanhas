# Otimização de campanhas (Meta + Google × CRM)

Skill para o [Claude Code](https://claude.com/claude-code) que cruza o investimento de mídia com os leads do seu CRM, por UTM, e gera um dashboard para decidir **onde investir mais, onde investir menos e o que pausar**. Funciona para qualquer projeto: você usa o seu CRM e as suas contas.

O repositório traz tudo o que a skill usa:

| Skill | O que responde |
|---|---|
| `otimizacao-campanhas` | Qual campanha, público, anúncio e palavra-chave gera MQL, SQL e venda, e a que custo |
| `plano-google-ads` | Por que o CPL subiu, o que negativar, quais palavras vendem e como estruturar as campanhas |

## O dashboard

Um HTML com três abas, sempre no mesmo formato:

- **Geral:** qualificado × desqualificado × em aberto em cada campanha, e onde tem lead parado.
- **Qualificação:** funil MQL, SQL e Venda com custo por etapa, delta contra a média do nível e "Investir mais / menos".
- **Desqualificação:** taxa por campanha e ranking de motivo de perda, com filtro por motivo.

As árvores abrem como no gerenciador: campanha → público ou grupo → anúncio.

## Instalação

```bash
git clone https://github.com/joaop13sobra-source/otimizacao-campanhas.git
cd otimizacao-campanhas
./install.sh
```

Copia as duas skills para `~/.claude/skills/` e instala as dependências. No Claude Code, chame `/otimizacao-campanhas` e responda as perguntas: projeto, CRM, período e etapa de MQL.

## Teste em 1 minuto, sem nenhum acesso

Dados fictícios incluídos:

```bash
cd ~/.claude/skills/otimizacao-campanhas/assets/demo
python3 -I ../../scripts/montar_dados.py config.json --saida dados.json
python3 -I ../../scripts/gerar_html.py dados.json --saida /tmp/demo/index.html
python3 -I ../../scripts/validar.py /tmp/demo/index.html
open /tmp/demo/index.html
```

## Do que você precisa

Só Python 3.9+ e os exports já bastam. O resto abre caminhos:

| Item | Obrigatório? | Para quê |
|---|---|---|
| Export de Meta Ads (nível de anúncio) e Google Ads (anúncios + palavras-chave) | Sim, salvo se usar o NEKT | Investimento |
| Leads do CRM: token do Kommo **ou** planilha com etapa e UTM | Sim | Funil. Com histórico de etapas o resultado é mais fiel |
| Google Chrome | Recomendado | `validar.py` executa a página antes de publicar |
| CLI do Vercel | Opcional | Publicar o link |
| MCP do Cockpit/Flow (NEKT) | Opcional | Puxar mídia sem CSV |
| Conta de serviço Google com Docs API | Opcional | Lançar o diagnóstico no Doc de comitê |
| Chave do Semrush | Opcional | Palavras novas no `plano-google-ads` |

Com Kommo, deixe as credenciais só no ambiente:

```bash
export KOMMO_SUBDOMAIN=sua-conta
export KOMMO_TOKEN=seu-token
```

Outro CRM funciona por planilha ou arquivo normalizado: `references/crm-e-fontes.md`.

## Como funciona

```
leads do CRM ──► puxar_kommo.py ─┐
planilha de leads ───────────────┼─► montar_dados.py ─► dados.json ─► gerar_html.py ─► index.html ─► validar.py
exports de Meta e Google ────────┘   (cruza e reconcilia)
                                                dados.json ─► docs-diagnostico/ ─► Doc de comitê (opcional)
```

O que não muda de um projeto para outro:

- **Qualificado é histórico:** o lead conta se alcançou a etapa de MQL alguma vez, mesmo que tenha sido perdido depois.
- **A etapa de MQL é sempre confirmada** a cada rodada. Nunca é inferida pelo nome.
- **Decisão por custo por MQL**, nunca por CPL isolado, e com volume mínimo.
- **Nenhum lead some:** sem UTM ou sem match fica declarado, e a soma dos filhos sempre bate com o pai.

## Onde está cada coisa

```
skills/otimizacao-campanhas/
  SKILL.md                   protocolo completo
  scripts/                   puxar_kommo, montar_dados, gerar_html, validar
  assets/                    motor do dashboard, config de exemplo, demo, Doc de comitê
  references/
    regua-do-funil.md        MQL, SQL, Venda, coorte, régua pela conversa
    crm-e-fontes.md          Kommo, Bitrix, planilha, exports, NEKT
    config.md                todos os campos do config
    sprint-growth.md         Doc de comitê, seções, tags no Ekyte, 5W1H
    armadilhas.md            erros que já aconteceram e como evitar
    publicacao.md            Vercel e link por cliente
    sub-playbook-modelo.md   modelo opcional para calibrar seu projeto
skills/plano-google-ads/     plano de Google Ads
```

## Dados e segurança

- Nenhum dado de cliente vem neste repositório. O que está em `assets/demo/` é fictício.
- O acesso ao CRM é só leitura, e o token nunca é impresso nem gravado.
- `leads_normalizados.json` tem nome de lead: mantenha fora de repositório e de deploy. O dashboard publicado não leva nome, telefone nem e-mail.
