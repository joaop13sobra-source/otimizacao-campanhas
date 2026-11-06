#!/usr/bin/env bash
# Instala as duas skills em ~/.claude/skills. Não sobrescreve sub-playbooks de cliente que você já tenha na pasta.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$DEST"
for s in otimizacao-campanhas plano-google-ads; do
  mkdir -p "$DEST/$s"
  # sem --delete: arquivos que só existem no destino continuam lá
  rsync -a --exclude '__pycache__' "$AQUI/skills/$s/" "$DEST/$s/"
  echo "instalada: $DEST/$s"
done
python3 -m pip install --quiet -r "$AQUI/requirements.txt" || echo "Aviso: instale as dependências manualmente: pip install -r requirements.txt"
echo "Pronto. No Claude Code: /otimizacao-campanhas e /plano-google-ads"
