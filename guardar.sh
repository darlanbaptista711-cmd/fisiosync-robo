#!/usr/bin/env bash
# Grava historico.json e pautas.json de volta no repositorio.
#
# A corrente de jobs depende disto: o job da tarde le o historico para
# saber que a manha ja publicou. Sem o push, ele publicaria de novo.
set -u

git config user.name "FisioSync Robo"
git config user.email "robo@users.noreply.github.com"

git add historico.json pautas.json || true
git diff --cached --quiet && { echo "Nada mudou."; exit 0; }

git commit -m "registro do post de $(date -u +%F-%H%M)"

# Outro job da corrente pode ter empurrado antes. Rebase e tenta de
# novo algumas vezes em vez de falhar a rodada inteira.
for tentativa in 1 2 3 4 5; do
  if git push; then
    echo "Historico salvo na tentativa $tentativa."
    exit 0
  fi
  echo "Push recusado. Rebaseando e tentando de novo..."
  git pull --rebase --autostash || true
  sleep $((tentativa * 3))
done

echo "Nao consegui salvar o historico depois de 5 tentativas."
exit 1
