#!/usr/bin/env bash
#
# fermo.sh — incide l'arresto che richiede una persona.
#
# E' la caratteristica migliore del loop Ardesia, e la ragione e' misurabile:
# osservato il 24/08/2026, il loop Ardesia era fermo dal 22 e ogni rilancio
# moriva sul FERMO in millisecondi, a costo zero, incidendo la ragione invece
# di ripartire alla cieca.
#
# Un loop senza questo meccanismo, davanti a una condizione che non sa
# risolvere, riprova. E riprovare su uno stato non capito e' esattamente il
# modo di bruciare un budget senza avvicinarsi a niente.
#
#   fermo.sh <CAUSA> "<spiegazione>"          incide
#   fermo.sh --stato                          dice se c'e'
#   fermo.sh --sciogli                        rimuove (atto deliberato)
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
STATO="$QUI/stato"
FERMO="$STATO/FERMO-SERVE-ANDREA.txt"

# Le otto cause, decise dal proprietario. Un elenco CHIUSO: una causa fuori
# elenco significa che il loop ha incontrato qualcosa che nessuno ha previsto,
# e quella e' essa stessa una ragione per fermarsi e chiamare una persona.
CAUSE="OWNER_DECISION ARCHITECTURE_CONFLICT BREAKING_CONTRACT READINESS_FAILURE
REPO_INTEGRITY_RISK HOLDOUT_OR_SECRET_RISK PRODUCT_KILL_CRITERION UNRECOVERABLE_INFRA_FAILURE"

case "${1:-}" in
  --stato)
    if [ -f "$FERMO" ]; then cat "$FERMO"; exit 12; fi
    printf 'nessun FERMO.\n'; exit 0 ;;
  --sciogli)
    if [ ! -f "$FERMO" ]; then printf 'nessun FERMO da sciogliere.\n'; exit 0; fi
    mkdir -p "$STATO/fermi-sciolti"
    dest="$STATO/fermi-sciolti/$(date -u +%Y%m%dT%H%M%SZ).txt"
    mv "$FERMO" "$dest"
    printf 'FERMO sciolto. Conservato in %s\n' "$dest"
    printf 'Lo scioglimento e un atto deliberato ed e inciso: non sparisce senza traccia.\n'
    exit 0 ;;
  "")
    printf 'uso: fermo.sh <CAUSA> "<spiegazione>"  |  --stato  |  --sciogli\n' >&2
    printf 'cause ammesse:\n' >&2
    for c in $CAUSE; do printf '  %s\n' "$c" >&2; done
    exit 64 ;;
esac

causa="$1"; shift
spiegazione="${*:-nessuna spiegazione fornita}"

ammessa=0
for c in $CAUSE; do [ "$c" = "$causa" ] && ammessa=1; done
if [ "$ammessa" != "1" ]; then
  printf 'fermo: causa fuori elenco: %s\n' "$causa" >&2
  exit 64
fi

mkdir -p "$STATO"
{
  printf 'FERMO — SERVE UNA PERSONA\n\n'
  printf 'causa:      %s\n' "$causa"
  printf 'spiegazione: %s\n' "$spiegazione"
  printf 'quando:     %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'repository: %s\n' "$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo '—')"
  printf 'ramo:       %s\n' "$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '—')"
  printf '\nOgni rilancio muore qui, a costo zero, finche questo file esiste.\n'
  printf 'Per scioglierlo dopo aver risolto la causa:\n  ops/loop/fermo.sh --sciogli\n'
  printf '\nIl giornale completo e in %s\n' "$QUI/giornale"
} > "$FERMO"

printf 'FERMO inciso: %s\n' "$causa" >&2
exit 12
