#!/usr/bin/env bash
#
# stato.sh — che cosa sa il sistema di se stesso, ricostruito da disco e da git.
#
# Nessuna riga di questo file interroga un modello, e nessuna legge una memoria
# di sessione. Se un'informazione non e' su disco o in git, qui non compare:
# e' il senso della regola «lo stato si ricostruisce, non si ricorda».
#
# Sola lettura. Non scrive niente, mai.
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
STATO="$QUI/stato"
GIORNALE="$QUI/giornale"
FERMO="$STATO/FERMO-SERVE-ANDREA.txt"
PIN="$REPO/_bmad/scripts.pin.json"
LEDGER="$REPO/_bmad-output/implementation-artifacts/sprint-status.yaml"

titolo() { printf '\n\033[1m%s\033[0m\n' "$*"; }
riga()   { printf '  %-22s %s\n' "$1" "$2"; }

# --- 1. il cancello che conta di piu' -----------------------------------------
if [ -f "$FERMO" ]; then
  printf '\n\033[1;31m  FERMO — SERVE UNA PERSONA\033[0m\n\n'
  sed 's/^/  /' "$FERMO"
  printf '\n  Nessun rilancio spendera un token finche questo file esiste.\n'
  printf '  Risolvi la causa, poi rimuovilo:\n    rm %s\n' "$FERMO"
else
  printf '\n\033[1;32m  operativo\033[0m — nessun FERMO\n'
fi

# --- 2. git: la prova storica -------------------------------------------------
titolo "Repository"
riga "ramo"    "$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '—')"
riga "HEAD"    "$(git -C "$REPO" log --oneline -1 2>/dev/null || echo '—')"
sporchi="$(git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato' ':(exclude)ops/loop/giornale' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$sporchi" = "0" ]; then riga "albero" "pulito"; else riga "albero" "$sporchi file non committati"; fi

# --- 3. runtime BMAD ----------------------------------------------------------
titolo "Runtime BMAD"
if [ -f "$PIN" ]; then
  riga "versione dichiarata" "$(python3 -c "import json;print(json.load(open('$PIN'))['declared_version'])" 2>/dev/null || echo '—')"
  drift=0; mancanti=0
  while IFS='|' read -r nome atteso; do
    [ -z "$nome" ] && continue
    f="$REPO/_bmad/scripts/$nome"
    if [ ! -f "$f" ]; then mancanti=$((mancanti+1)); continue; fi
    [ "$(shasum -a 256 "$f" | cut -d' ' -f1)" = "$atteso" ] || drift=$((drift+1))
  done <<< "$(python3 -c "
import json
d=json.load(open('$PIN'))
for n,v in d['files'].items(): print(n+'|'+v['sha256'])
" 2>/dev/null)"
  tot="$(python3 -c "import json;print(len(json.load(open('$PIN'))['files']))" 2>/dev/null || echo 0)"
  if [ "$mancanti" = "0" ] && [ "$drift" = "0" ]; then
    riga "helper" "$tot/$tot conformi al pin"
  else
    riga "helper" "DRIFT: $drift derivati, $mancanti assenti su $tot"
  fi
else
  riga "pin" "assente"
fi

# --- 4. il ledger BMAD --------------------------------------------------------
titolo "Ledger"
if [ -f "$LEDGER" ]; then
  python3 - "$LEDGER" <<'PY' 2>/dev/null || printf '  %-22s %s\n' "sprint-status" "illeggibile"
import sys
try:
    import yaml
except ImportError:
    print('  %-22s %s' % ('sprint-status', 'presente (pyyaml assente: nessun conteggio)')); raise SystemExit(0)
d = yaml.safe_load(open(sys.argv[1])) or {}
# Solo il vocabolario legale degli stati. Senza questo filtro i metadati in
# testa al file (project, generated, tracking_system) verrebbero contati come
# se fossero stati di storie: un conteggio plausibile e falso.
LEGALI = {'backlog', 'in-progress', 'done', 'optional', 'review',
          'blocked', 'drafted', 'contexted', 'ready'}
ds = d.get('development_status') or {}
c = {}
for k, v in ds.items():
    if isinstance(v, str) and v in LEGALI:
        c[v] = c.get(v, 0) + 1
print('  %-22s %s' % ('aggiornato', d.get('last_updated', '—')))
print('  %-22s %s' % ('stati', ', '.join(f'{k}: {n}' for k, n in sorted(c.items())) or '—'))
PY
else
  riga "sprint-status" "assente"
fi

# --- 5. il giornale: append-only, un file per iterazione ----------------------
titolo "Giornale"
n="$(ls "$GIORNALE" 2>/dev/null | wc -l | tr -d ' ')"
riga "iterazioni incise" "$n"
if [ "$n" != "0" ]; then
  for f in $(ls -t "$GIORNALE" 2>/dev/null | head -3); do
    riga "" "$f"
  done
fi

# --- 6. il ratchet: le metriche che non possono regredire --------------------
titolo "Ratchet"
if [ -f "$STATO/ratchet.json" ]; then
  python3 -c "
import json
d = json.load(open('$STATO/ratchet.json'))
if not d: print('  %-22s %s' % ('', 'vuoto'))
for k, v in sorted(d.items()): print('  %-22s %s' % (k, v))
" 2>/dev/null || riga "" "illeggibile"
else
  riga "" "nessuna baseline ancora incisa"
fi

# --- 7. che cosa farebbe il prossimo giro ------------------------------------
titolo "Prossimo giro"
if [ -f "$STATO/prossima-storia.txt" ]; then
  s="$(head -1 "$STATO/prossima-storia.txt")"
  riga "storia" "$s"
  python3 "$QUI/router.py" --storia "$s" 2>/dev/null | sed -n '2,3p' | sed 's/^/  /'
else
  riga "storia" "non fissata — usa: kirchhoff-loop dry-run <chiave-storia>"
fi
printf '\n'
