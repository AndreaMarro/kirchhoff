#!/usr/bin/env bash
#
# verifica.sh — l'oracolo deterministico. Costo in token: zero.
#
# Qui si applica la terza regola inviolabile: IL MODELLO PROPONE, IL SISTEMA
# CERTIFICA. Nessun passo del loop si chiude su un'affermazione di un modello.
# Si chiude qui, o non si chiude.
#
# Compone gli oracoli che il progetto ha gia' — non ne inventa di nuovi:
#   scripts/check_boundaries.py       i recinti di dipendenza (AD-21)
#   scripts/check_domain_coverage.py  la copertura del dominio
#   pytest                            con --cov-fail-under gia' in addopts
#
# Emette su stdout un JSON di metriche, che il ratchet confronta. Il testo
# leggibile va su stderr, cosi' che `verifica.sh > metriche.json` resti pulito.
#
# ATTENZIONE, difetto gia' pagato una volta su questo repository: `$?` dopo una
# PIPE non e' il codice del comando che interessa. Qui ogni esito si raccoglie
# redirigendo su file e leggendo `$?` sulla riga successiva, mai dopo un `|`.
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$REPO" || { printf 'verifica: %s irraggiungibile\n' "$REPO" >&2; exit 70; }

dire() { printf '%s\n' "$*" >&2; }

esito_globale=0

# --- 1. i test, con la soglia di copertura gia' in addopts --------------------
dire "  test..."
uv run --with pytest --with pytest-cov python -m pytest tests > "$TMP/pytest.out" 2>&1
esito_test=$?

# I punti sono i test passati. `-q` non stampa un totale leggibile a macchina.
# Contarli su TUTTO il file darebbe un numero gonfiato: la tabella di copertura
# e' piena di punti. Misurato: 258 invece di 245. Si contano solo le righe di
# AVANZAMENTO, quelle che finiscono con la percentuale fra parentesi quadre.
passati="$(grep -E '^[.sxXFE]+ +\[ *[0-9]+%\]$' "$TMP/pytest.out" | tr -cd '.' | wc -c | tr -d ' ')"
# `grep -c` senza corrispondenze stampa "0" E esce 1: con `|| echo 0` il
# risultato era la stringa "0\n0", che int() rifiuta. Misurato.
falliti="$(grep -c '^FAILED' "$TMP/pytest.out" 2>/dev/null)"
falliti="${falliti:-0}"

if [ "$esito_test" != "0" ]; then
  dire "  [NO]  test: exit $esito_test"
  tail -25 "$TMP/pytest.out" >&2
  esito_globale=1
else
  dire "  [ok]  test: $passati passati"
fi

# --- 2. copertura, letta dall'artefatto e non dal riassunto -------------------
# Difetto gia' pagato: un gate che leggeva un coverage.json stantio dichiarava
# 100% su file che non aveva mai visto. Qui si legge l'artefatto appena scritto
# dalla corsa qui sopra, e se non esiste si dice, invece di dedurlo.
copertura="null"
if [ -f "$REPO/coverage.json" ]; then
  copertura="$(python3 -c "
import json
d = json.load(open('$REPO/coverage.json'))
print(round(d['totals']['percent_covered'], 2))
" 2>/dev/null || echo null)"
  dire "  [ok]  copertura: $copertura%"
else
  dire "  [!!]  coverage.json assente: copertura non misurata"
fi

# --- 3. i recinti di dipendenza ----------------------------------------------
recinti="null"
if [ -f "$REPO/scripts/check_boundaries.py" ]; then
  uv run python "$REPO/scripts/check_boundaries.py" > "$TMP/recinti.out" 2>&1
  esito_recinti=$?
  if [ "$esito_recinti" = "0" ]; then
    recinti="true"; dire "  [ok]  recinti di dipendenza"
  else
    recinti="false"; esito_globale=1
    dire "  [NO]  recinti: exit $esito_recinti"
    tail -15 "$TMP/recinti.out" >&2
  fi
else
  dire "  [--]  check_boundaries.py assente"
fi

# --- 4. copertura del dominio -------------------------------------------------
dominio="null"
if [ -f "$REPO/scripts/check_domain_coverage.py" ]; then
  uv run python "$REPO/scripts/check_domain_coverage.py" > "$TMP/dominio.out" 2>&1
  esito_dominio=$?
  if [ "$esito_dominio" = "0" ]; then
    dominio="true"; dire "  [ok]  copertura del dominio"
  else
    dominio="false"; esito_globale=1
    dire "  [NO]  copertura del dominio: exit $esito_dominio"
    tail -15 "$TMP/dominio.out" >&2
  fi
else
  dire "  [--]  check_domain_coverage.py assente"
fi

# --- 5. le metriche, per il ratchet ------------------------------------------
# `true`/`false` NON sono letterali Python: la prima versione di questo blocco
# li interpolava cosi' e moriva con SyntaxError, in silenzio, lasciando stdout
# vuoto mentre l'exit restava 0. Un emettitore di metriche che fallisce zitto e'
# peggio di uno che non c'e'. Ora i valori passano come argomenti e la
# conversione avviene in Python, e se fallisce l'exit lo dice.
verde=$([ "$esito_globale" = "0" ] && echo 1 || echo 0)
if ! python3 - "$passati" "$falliti" "$copertura" "$recinti" "$dominio" "$verde" <<'PYFINE'
import json, sys
def tri(v):
    return None if v == 'null' else (v == 'true')
def num(v):
    return None if v == 'null' else float(v)
_, passati, falliti, cop, rec, dom, verde = sys.argv
print(json.dumps({
    'test_passati': int(passati),
    'test_falliti': int(falliti),
    'copertura': num(cop),
    'recinti': tri(rec),
    'dominio': tri(dom),
    'verde': verde == '1',
}, ensure_ascii=False, sort_keys=True))
PYFINE
then
  printf 'verifica: emissione delle metriche FALLITA\n' >&2
  exit 70
fi

exit "$esito_globale"
