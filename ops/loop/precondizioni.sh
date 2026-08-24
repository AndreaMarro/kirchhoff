#!/usr/bin/env bash
#
# precondizioni.sh — i cancelli che stanno PRIMA di qualunque spesa di token.
#
# Principio, preso dal loop Ardesia e verificato in 381 iterazioni:
# nessun token si spende su uno stato non capito. Se qualcosa non e'
# verificabile, NON si lavora. Non "si prova lo stesso".
#
# Esce 0 solo se ogni cancello passa. Ogni altro codice identifica il cancello
# che ha fermato la corsa, cosi' che un rilancio muoia sullo stesso punto a
# costo zero invece di ripartire alla cieca.
#
# CODICI
#   0   tutto verificato
#   10  non e' un repository git
#   11  uv assente
#   12  FERMO presente: serve una persona
#   13  helper runtime BMAD assenti o derivati (drift)
#   15  la guardia sul holdout non e' in vigore
#   16  sprint-status.yaml non valido
#   17  albero di lavoro sporco in modo non compreso
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
STATO="$QUI/stato"
FERMO="$STATO/FERMO-SERVE-ANDREA.txt"
PIN="$REPO/_bmad/scripts.pin.json"

silenzioso=0
[ "${1:-}" = "--silenzioso" ] && silenzioso=1
dire() { [ "$silenzioso" = "1" ] || printf '%s\n' "$*"; }
ko()   { printf 'PRECONDIZIONE FALLITA: %s\n' "$*" >&2; }

# --- 1. FERMO. Va per primo: se serve una persona, tutto il resto e' rumore. --
# Ardesia: «FERMO gia' presente: il rilancio muore qui, a costo zero.»
if [ -f "$FERMO" ]; then
  ko "FERMO presente. Serve una persona."
  [ "$silenzioso" = "1" ] || sed 's/^/  | /' "$FERMO"
  exit 12
fi
dire "  [ok]  nessun FERMO"

# --- 2. repository git ---------------------------------------------------------
# Lo stato canonico si ricostruisce da git. Senza git non c'e' stato canonico.
if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ko "$REPO non e' un repository git."
  exit 10
fi
dire "  [ok]  repository git: $(git -C "$REPO" rev-parse --short HEAD)"

# --- 3. uv --------------------------------------------------------------------
# Ogni skill BMAD parte con `uv run`. Senza uv la Fase 4 non nasce.
if ! command -v uv >/dev/null 2>&1; then
  ko "uv non e' sul PATH. Le skill BMAD lo invocano per ogni script."
  exit 11
fi
dire "  [ok]  uv: $(uv --version 2>/dev/null)"

# --- 4. helper runtime BMAD: presenti E conformi al pin -----------------------
# Non basta che ci siano. Il vincolo dell'owner e' `locale == upstream`, mai
# `upstream + nostre correzioni`. Un formatter, un edit accidentale o un hook
# che riscrive i .py violano il vincolo in silenzio: qui smette di essere
# silenzioso.
if [ ! -f "$PIN" ]; then
  ko "manca $PIN: nessuna baseline contro cui verificare gli helper."
  exit 13
fi
drift=0
while IFS='|' read -r nome atteso; do
  [ -z "$nome" ] && continue
  f="$REPO/_bmad/scripts/$nome"
  if [ ! -f "$f" ]; then
    ko "helper runtime assente: _bmad/scripts/$nome"; drift=1; continue
  fi
  ottenuto="$(shasum -a 256 "$f" | cut -d' ' -f1)"
  if [ "$ottenuto" != "$atteso" ]; then
    ko "DRIFT su _bmad/scripts/$nome"
    ko "  atteso   $atteso"
    ko "  ottenuto $ottenuto"
    drift=1
  fi
done <<< "$(python3 -c "
import json,sys
d=json.load(open('$PIN'))
for n,v in d['files'].items():
    print(n+'|'+v['sha256'])
" 2>/dev/null)"
if [ "$drift" != "0" ]; then
  ko "gli helper BMAD non corrispondono al pin. Ripristinali dall'upstream v$(python3 -c "import json;print(json.load(open('$PIN'))['declared_version'])" 2>/dev/null) prima di lavorare."
  exit 13
fi
dire "  [ok]  helper runtime BMAD conformi al pin (5/5)"

# --- 5. guardia sul holdout ---------------------------------------------------
# Leggere reference-set/holdout/ invalida ogni misura successiva. Il divieto
# deve essere ESEGUIBILE, non solo scritto: qui si verifica che la regola deny
# sia in vigore, non che qualcuno si ricordi di rispettarla.
if [ -d "$REPO/reference-set/holdout" ]; then
  if ! grep -q 'reference-set/holdout' "$REPO/.claude/settings.json" 2>/dev/null; then
    ko "esiste reference-set/holdout/ ma .claude/settings.json non lo nega."
    exit 15
  fi
  dire "  [ok]  holdout protetto da regola deny"
else
  dire "  [--]  nessun holdout su disco"
fi

# --- 6. sprint-status leggibile e valido --------------------------------------
LEDGER="$REPO/_bmad-output/implementation-artifacts/sprint-status.yaml"
if [ -f "$LEDGER" ]; then
  if ! python3 -c "
import sys
try:
    import yaml
except ImportError:
    sys.exit(0)   # senza pyyaml non si giudica: non e' un fallimento del ledger
d = yaml.safe_load(open('$LEDGER'))
sys.exit(0 if isinstance(d, dict) else 1)
" 2>/dev/null; then
    ko "$LEDGER non e' un mapping YAML valido."
    exit 16
  fi
  dire "  [ok]  sprint-status.yaml leggibile"
else
  dire "  [--]  sprint-status.yaml assente"
fi

# --- 7. albero di lavoro ------------------------------------------------------
# Ardesia si e' fermata proprio qui: «il prodotto ha 4 file non committati
# (erano 0)». Non e' pedanteria: un albero sporco all'AVVIO significa che il
# giro precedente ha lasciato residuo, e il revisore giudicherebbe lavoro che
# nessuno ha dichiarato. Lo stato del loop e' escluso: lo possiede il loop.
sporchi="$(git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$sporchi" != "0" ]; then
  ko "albero di lavoro sporco: $sporchi file non committati all'avvio."
  [ "$silenzioso" = "1" ] || git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato' | sed 's/^/  | /'
  ko "Committa o scarta prima di partire: il revisore deve giudicare lavoro dichiarato."
  exit 17
fi
dire "  [ok]  albero di lavoro pulito"

exit 0
