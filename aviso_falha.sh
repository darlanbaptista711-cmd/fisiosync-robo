#!/usr/bin/env bash
# Abre UMA issue por dia quando a rodada falha. A issue vira e-mail.
#
# Um por dia, nao um por tentativa: a corrente tem varios jobs e varias
# largadas, e sem este filtro um unico problema enche a caixa de entrada.
set -u

TITULO="O post de $(date -u +%F) falhou"

if gh issue list --state open --search "$TITULO in:title" \
     --json title --jq '.[].title' | grep -qxF "$TITULO"; then
  echo "Ja existe aviso aberto para hoje. Nao vou duplicar."
  exit 0
fi

gh issue create --title "$TITULO" --body "A rodada automatica nao publicou.

Log: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}

Causas mais comuns, em ordem:

1. Token do Instagram expirado. Gere outro no Business Manager e
   atualize o segredo IG_ACCESS_TOKEN.
2. Credito da OpenAI acabou. Veja em platform.openai.com.
3. O texto nao coube na arte ou citou numero sem fonte. Nesses casos o
   robo recusa publicar de proposito: a proxima largada escreve outro
   texto e resolve sozinho.
4. A Meta recusou a imagem ou esta fora do ar. Costuma passar na
   proxima rodada." || true
