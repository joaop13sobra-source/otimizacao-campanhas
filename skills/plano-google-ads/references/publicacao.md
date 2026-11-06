# Publicação e validação

A skill gera um arquivo estático (`index.html`). Publique onde fizer sentido para o seu time: Vercel, Netlify, GitHub Pages, um bucket ou um servidor interno. O roteiro abaixo usa o **Vercel com um projeto por cliente** (um "hub" com uma página inicial e um caminho por material), que funcionou bem na prática.

## Um link só por cliente (hub)

```
<cliente>-deploy/
├── index.html            página inicial (um card por material)
├── assets/               logos usados pela página inicial e por /plano/
├── plano/index.html      saída desta skill (usa ../assets/ e ../ para voltar)
├── <outros materiais>/   check-ins, relatórios, retrospectivas
└── vercel.json           cabeçalhos (sem cache, noindex)
```

Regras:
- **Caminhos relativos** (`../assets/...`, `../`): funcionam em qualquer caminho do hub.
- **Não apague** versões antigas ao reorganizar; copie e mantenha as antigas no ar.
- Cabeçalhos no `vercel.json`:
  ```json
  {"headers":[{"source":"/(.*)","headers":[
    {"key":"Cache-Control","value":"no-cache, no-store, must-revalidate"},
    {"key":"X-Robots-Tag","value":"noindex, nofollow"}]}]}
  ```
  As páginas geradas também levam `<meta name="robots" content="noindex,nofollow">`.

### Aviso de exposição
Um hub sem senha **abre tudo para quem tiver o endereço**. Rotule o que é interno na página inicial e avise quem vai compartilhar o link com o cliente. Se for compartilhar, proteja as páginas internas com senha (criptografia no cliente, por exemplo AES-GCM com a senha derivada por PBKDF2) e deixe abertas só as apresentações.

### Comandos
```bash
cd <pasta do hub>
vercel deploy --prod --yes --scope <seu-escopo>
```
Depois do deploy, confira **cada URL** (HTTP 200), os assets e o `x-robots-tag`:
```bash
B=https://<projeto>.vercel.app
for p in "" plano/ assets/<logo>.png; do printf "%-40s %s\n" "/$p" "$(curl -s -o /dev/null -w '%{http_code}' $B/$p)"; done
curl -sI $B/ | grep -i x-robots-tag
```

## Validação visual (antes de dizer que está pronto)

Tire um print real da página e **leia a imagem**. Com o Chrome instalado:

```bash
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # macOS; ajuste no Linux/Windows
"$CH" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,2400 --screenshot=/caminho/shot.png "file:///caminho/index.html"
```
- Página muito longa: gere cópias que mostram uma seção por vez (CSS `section{display:none}section#estr{display:block}`) e leia cada uma.
- Imagens relativas (`../assets/`) só aparecem no deploy ou servindo a pasta (`python3 -m http.server`); o print de arquivo avulso mostra o ícone quebrado, e tudo bem.
- Confira: tabelas sem estourar, números com vírgula, selos de cor corretos, "novo" × "já na conta" nas listas, nenhum `[[?` no texto.

Rode também o portão de qualidade: `python3 -I scripts/validar_pagina.py index.html` (erro se houver template não resolvido, `NaN`, telefone/e-mail/CPF no texto).

## Depois do deploy
Se algum número dito ao cliente ou ao time em conversa mudou na página final, avise.
