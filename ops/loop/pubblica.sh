#!/usr/bin/env bash
# Porta su GitHub cio' che e' gia' su main, e lo VERIFICA.
#
# **Non promuove e non decide.** Un push non e' un giudizio: e' il trasporto di
# uno stato che qualcuno ha gia' accettato. Se questo script potesse promuovere,
# un giro verde arriverebbe su origin senza che nessuno abbia guardato il diff —
# ed e' precisamente cio' che lo scheduler si rifiuta di fare quando dice «un
# verdetto di modello non apre un merge».
#
# Verifica dopo, non prima: il conteggio dei commit remoti deve coincidere con
# quello locale. Un push che fallisce a meta' e non viene riletto e' un
# «pubblicato» che non e' vero.
set -euo pipefail

REPO="${KIRCHHOFF_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$REPO"

ramo="$(git rev-parse --abbrev-ref HEAD)"
if [ "$ramo" != "main" ]; then
  printf 'RAMO_NON_MAIN: sei su %s. Si pubblica cio che e stato accettato.\n' "$ramo" >&2
  exit 65
fi
if [ -n "$(git status --porcelain)" ]; then
  printf 'ALBERO_SPORCO: committa o scarta prima di pubblicare.\n' >&2
  exit 65
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  printf 'NESSUN_ORIGIN\n' >&2
  exit 66
fi

locali="$(git rev-list --count main)"
git push origin main --quiet
git fetch origin --quiet
remoti="$(git rev-list --count origin/main)"

if [ "$locali" != "$remoti" ]; then
  printf 'PUBBLICAZIONE_INCOMPLETA: locali=%s remoti=%s\n' "$locali" "$remoti" >&2
  exit 70
fi
printf 'pubblicati %s commit su %s\n' "$remoti" "$(git remote get-url origin)"
