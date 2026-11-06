# Publicação

## Vercel

```bash
cd deploy   # pasta só com index.html
vercel deploy --prod --yes --name otimizacao-campanhas-<cliente>
```

- Publicar cria um link público. Em cliente novo, **confirme antes de criar a URL**. Depois de combinado, atualizar a mesma URL é só rodar de novo, validando antes.
- A pasta `deploy/` só leva o `index.html`: nunca CSV, `leads_normalizados.json` ou config.
- Confira a URL real em `vercel inspect`: nomes longos são cortados no alias.
- A página não leva nome, telefone nem e-mail de lead, mas expõe investimento e funil do cliente. Se precisar restringir, use proteção de acesso do Vercel.

## Um link por cliente

Se o cliente já tem hub, o material novo entra como subpasta (`/otimizacao/`, `/plano/`), com um card na página inicial. É assim que este dashboard e o da `plano-google-ads` convivem no mesmo link. Depois do deploy, confira se cada URL responde 200.

## Conferência visual

`validar.py` confere que o JavaScript rodou até o fim. Antes de reportar pronto, abra a página ou tire um print e veja as três abas, abra uma campanha até o anúncio, teste uma ordenação e clique num motivo de perda.
