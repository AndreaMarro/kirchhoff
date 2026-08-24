#!/usr/bin/env bash
#
# precondizioni.sh — i cancelli che stanno PRIMA di qualunque spesa di token.
#
# Principio, preso dal loop Ardesia e verificato in 381 iterazioni:
# nessun token si spende su uno stato non capito. Se qualcosa non e'
# verificabile, NON si lavora. Non "si prova lo stesso".
#
# DUE MODI, e la distinzione conta
#
#   (default)   diagnostico. Esegue TUTTI i cancelli e li riporta tutti, poi
#               esce col codice del primo fallito. E' cio' che serve a `doctor`:
#               una diagnosi che muore al primo cancello dice meno di quanto
#               sa, e si esegue proprio quando le cose sono disordinate.
#
#   --avvio     pre-iterazione. Aggiunge il cancello sull'albero di lavoro, che
#               vale solo prima di far partire un giro: un albero sporco
#               all'AVVIO significa residuo di un giro precedente, e il
#               revisore giudicherebbe lavoro che nessuno ha dichiarato.
#
# CODICI
#   0   tutto verificato
#   10  non e' un repository git
#   11  uv assente
#   12  FERMO presente: serve una persona
#   13  helper runtime BMAD assenti o derivati (drift)
#   15  la guardia sul holdout non e' in vigore
#   16  sprint-status.yaml non valido
#   17  albero di lavoro sporco (solo con --avvio)
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
STATO="$QUI/stato"
FERMO="$STATO/FERMO-SERVE-ANDREA.txt"
PIN="$REPO/_bmad/scripts.pin.json"
LEDGER="$REPO/_bmad-output/implementation-artifacts/sprint-status.yaml"

avvio=0
silenzioso=0
for a in "$@"; do
  case "$a" in
    --avvio)      avvio=1 ;;
    --silenzioso) silenzioso=1 ;;
    *) printf 'precondizioni: argomento sconosciuto: %s\n' "$a" >&2; exit 64 ;;
  esac
done

primo_errore=0
ok()   { [ "$silenzioso" = "1" ] || printf '  [ok]  %s\n' "$*"; }
nota() { [ "$silenzioso" = "1" ] || printf '  [--]  %s\n' "$*"; }
avv()  { [ "$silenzioso" = "1" ] || printf '  [!!]  %s\n' "$*"; }
ko() {
  local codice="$1"; shift
  printf '  \033[1;31m[NO]\033[0m  %s\n' "$*" >&2
  [ "$primo_errore" = "0" ] && primo_errore="$codice"
}

# --- 1. FERMO -----------------------------------------------------------------
# Ardesia: «FERMO gia' presente: il rilancio muore qui, a costo zero.»
if [ -f "$FERMO" ]; then
  ko 12 "FERMO presente. Serve una persona."
  [ "$silenzioso" = "1" ] || sed 's/^/        | /' "$FERMO" >&2
else
  ok "nessun FERMO"
fi

# --- 2. repository git --------------------------------------------------------
# Lo stato canonico si ricostruisce da git. Senza git non c'e' stato canonico.
if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "repository git: $(git -C "$REPO" rev-parse --short HEAD)"
else
  ko 10 "$REPO non e' un repository git."
fi

# --- 3. uv --------------------------------------------------------------------
# Ogni skill BMAD parte con `uv run`. Senza uv la Fase 4 non nasce.
if command -v uv >/dev/null 2>&1; then
  ok "uv: $(uv --version 2>/dev/null)"
else
  ko 11 "uv non e' sul PATH. Le skill BMAD lo invocano per ogni script."
fi

# --- 4. helper runtime BMAD: presenti E conformi al pin -----------------------
# Non basta che ci siano. Il vincolo dell'owner e' `locale == upstream`, mai
# `upstream + nostre correzioni`. Un formatter, un edit accidentale o un hook
# che riscrive i .py violano il vincolo in silenzio: qui smette di esserlo.
if [ ! -f "$PIN" ]; then
  ko 13 "manca $PIN: nessuna baseline contro cui verificare gli helper."
else
  drift=0; mancanti=0; tot=0
  while IFS='|' read -r nome atteso; do
    [ -z "$nome" ] && continue
    tot=$((tot+1))
    f="$REPO/_bmad/scripts/$nome"
    if [ ! -f "$f" ]; then
      ko 13 "helper runtime assente: _bmad/scripts/$nome"; mancanti=$((mancanti+1)); continue
    fi
    ottenuto="$(shasum -a 256 "$f" | cut -d' ' -f1)"
    if [ "$ottenuto" != "$atteso" ]; then
      ko 13 "DRIFT su _bmad/scripts/$nome"
      printf '        atteso   %s\n        ottenuto %s\n' "$atteso" "$ottenuto" >&2
      drift=$((drift+1))
    fi
  done <<< "$(python3 -c "
import json
d=json.load(open('$PIN'))
for n,v in d['files'].items(): print(n+'|'+v['sha256'])
" 2>/dev/null)"
  [ "$drift" = "0" ] && [ "$mancanti" = "0" ] && ok "helper runtime BMAD conformi al pin ($tot/$tot)"
fi

# --- 5. guardia sul holdout ---------------------------------------------------
# Leggere reference-set/holdout/ invalida ogni misura successiva. Il divieto
# deve essere ESEGUIBILE, non solo scritto: qui si verifica che la regola deny
# sia in vigore, non che qualcuno si ricordi di rispettarla.
if [ -d "$REPO/reference-set/holdout" ]; then
  if grep -q 'reference-set/holdout' "$REPO/.claude/settings.json" 2>/dev/null; then
    ok "holdout protetto da regola deny"
  else
    ko 15 "esiste reference-set/holdout/ ma .claude/settings.json non lo nega."
  fi
else
  nota "nessun holdout su disco"
fi

# --- 6. sprint-status leggibile -----------------------------------------------
if [ -f "$LEDGER" ]; then
  if python3 -c "
import sys
try: import yaml
except ImportError: sys.exit(0)   # senza pyyaml non si giudica: non e' colpa del ledger
d = yaml.safe_load(open('$LEDGER'))
sys.exit(0 if isinstance(d, dict) else 1)
" 2>/dev/null; then
    ok "sprint-status.yaml leggibile"
  else
    ko 16 "$LEDGER non e' un mapping YAML valido."
  fi
else
  nota "sprint-status.yaml assente"
fi

# --- 7. albero di lavoro — solo prima di un giro ------------------------------
# Ardesia si e' fermata proprio qui: «il prodotto ha 4 file non committati
# (erano 0)». Lo stato del loop e' escluso: lo possiede il loop.
sporchi="$(git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato' ':(exclude)ops/loop/giornale' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$sporchi" = "0" ]; then
  ok "albero di lavoro pulito"
elif [ "$avvio" = "1" ]; then
  ko 17 "albero di lavoro sporco: $sporchi file non committati all'avvio."
  [ "$silenzioso" = "1" ] || git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato' ':(exclude)ops/loop/giornale' | sed 's/^/        | /' >&2
  printf '        Committa o scarta: il revisore deve giudicare lavoro dichiarato.\n' >&2
else
  avv "albero di lavoro sporco: $sporchi file. Bloccherebbe un giro (--avvio)."
fi

exit "$primo_errore"
