#!/usr/bin/env bash
#
# OWNER-LOCKED: questo file decide che cosa atterra. Se un'iterazione potesse
# modificarlo, potrebbe disarmare il watchdog, il ratchet o il FERMO — cioe'
# ogni meccanismo che la limita. Per questo `iterazione.md` vieta di toccare
# ops/loop/, e per questo il divieto sta anche qui.
#
# kirchhoff-loop.sh — lo scheduler seriale.
#
# UNA iterazione, UN ramo, UN verdetto. Nessun parallelismo a questo livello.
# Il parallelismo, dove serve, sta dentro l'iterazione ed e' limitato ai
# revisori: mai due scrittori sullo stesso albero.
#
# I CINQUE MECCANISMI, presi da Ardesia e verificati la' in 381 iterazioni
#   1. PRECONDIZIONI  nessun token su uno stato non capito
#   2. WATCHDOG       un'iterazione che non finisce viene uccisa, non attesa
#   3. RATCHET        le metriche non regrediscono; misurato su una COPIA
#   4. GIORNALE       append-only: un file per iterazione, mai riscritto
#   5. FERMO          l'arresto che richiede una persona
#
# CIO' CHE NON SI COPIA DA ARDESIA
#   Ardesia gira incondizionatamente a --model claude-opus-5 --effort max
#   (ardesia-loop.sh:594-595). Qui il modello e il livello vengono dal router,
#   che li deriva dalla classe di rischio della storia.
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$QUI/../.." && pwd)"
STATO="$QUI/stato"
GIORNALE="$QUI/giornale"
BASELINE="$STATO/ratchet.json"

# Tetti duri. Non sono stime: sono il punto oltre il quale si smette, comunque.
BUDGET_PASSO=8          # dollari per singola invocazione di claude
WATCHDOG=2700           # 45 minuti: oltre, si uccide
PAUSA=20                # respiro fra iterazioni
ITERAZIONI=1
PROVA=0

while [ $# -gt 0 ]; do
  case "$1" in
    --iterazioni) shift; ITERAZIONI="${1:-1}" ;;
    --prova)      PROVA=1; ITERAZIONI=1 ;;
    --pausa)      shift; PAUSA="${1:-20}" ;;
    --watchdog)   shift; WATCHDOG="${1:-2700}" ;;
    --budget)     shift; BUDGET_PASSO="${1:-8}" ;;
    *) printf 'kirchhoff-loop.sh: argomento sconosciuto: %s\n' "$1" >&2; exit 64 ;;
  esac
  shift
done

mkdir -p "$STATO" "$GIORNALE"

# --- il giornale --------------------------------------------------------------
# Append-only, un file nuovo per iterazione. Due aggiunte non si sovrappongono;
# una riscrittura si'. Il file si apre PRIMA di qualunque spesa, cosi' che anche
# un giro che muore sul primo cancello lasci traccia del perche'.
avvio="$(date -u +%Y%m%dT%H%M%SZ)"
DIARIO="$GIORNALE/${avvio}-ITERAZIONE.log"
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$DIARIO"; }

log "kirchhoff-loop v3 — avvio"
log "repository=$REPO"
log "iterazioni=$ITERAZIONI prova=$PROVA watchdog=${WATCHDOG}s budget/passo=\$${BUDGET_PASSO}"

# --- il watchdog --------------------------------------------------------------
# Ardesia: TERM, dieci secondi di grazia, poi KILL. Il segnale di stop deve
# venire da FUORI dall'agente: un agente che decide da solo quando fermarsi ha
# gia' dimostrato di predire oltre il 70% di fattibilita' dopo aver bruciato il
# 60% del budget.
con_watchdog() {
  local uscita="$1"; shift
  "$@" > "$uscita" 2>&1 &
  local pid=$!
  ( sleep "$WATCHDOG"
    kill -0 "$pid" 2>/dev/null && {
      kill -TERM "$pid" 2>/dev/null; sleep 10; kill -KILL "$pid" 2>/dev/null; }
  ) &
  local cane=$!
  wait "$pid"; local esito=$?
  kill "$cane" 2>/dev/null; wait "$cane" 2>/dev/null
  return "$esito"
}

# --- un passo di modello ------------------------------------------------------
# Ogni passo e' un PROCESSO NUOVO. E' cosi' che si garantisce che il revisore
# non veda il ragionamento dell'implementatore: non per buona volonta' del
# modello, ma perche' quel contesto non esiste nel suo processo.
passo_modello() {
  local modello="$1" effort="$2" prompt_file="$3" uscita="$4"
  log "  → claude -p --model $modello --effort $effort"
  if [ "$PROVA" = "1" ]; then
    log "    [prova] nessun processo invocato"
    printf '(prova: nessuna invocazione)\n' > "$uscita"
    return 0
  fi
  con_watchdog "$uscita" env -C "$REPO" claude -p \
      --model "$modello" \
      --effort "$effort" \
      --dangerously-skip-permissions \
      --disallowed-tools Workflow \
      --max-budget-usd "$BUDGET_PASSO" \
      --setting-sources project,local \
      --append-system-prompt "$(cat "$prompt_file")"
}

# =============================================================================
n=0
while [ "$n" -lt "$ITERAZIONI" ]; do
  n=$((n+1))
  log ""
  log "--- iterazione $n di $ITERAZIONI ---"

  # 1. PRECONDIZIONI ----------------------------------------------------------
  bash "$QUI/precondizioni.sh" --avvio >> "$DIARIO" 2>&1
  pre=$?
  if [ "$pre" != "0" ]; then
    log "precondizioni exit $pre. Nessun token speso. Il giro muore qui."
    exit "$pre"
  fi
  log "precondizioni: tutte verdi"

  # 2. LA STORIA --------------------------------------------------------------
  if [ ! -f "$STATO/prossima-storia.txt" ]; then
    log "nessuna storia fissata. Esegui prima: kirchhoff-loop dry-run <chiave>"
    exit 64
  fi
  storia="$(head -1 "$STATO/prossima-storia.txt")"
  log "storia: $storia"

  # 3. IL ROUTER --------------------------------------------------------------
  piano_json="$STATO/.piano.json"
  python3 "$QUI/router.py" --storia "$storia" --json > "$piano_json" 2>>"$DIARIO"
  if [ $? != 0 ]; then
    log "router fallito."
    bash "$QUI/fermo.sh" UNRECOVERABLE_INFRA_FAILURE "il router non ha saputo instradare $storia"
    exit 12
  fi
  classe="$(python3 -c "import json;print(json.load(open('$piano_json'))['classe'])")"
  log "classe di rischio: $classe"

  if [ "$classe" = "MANUALE" ]; then
    log "storia non instradabile: e infrastruttura del loop."
    bash "$QUI/fermo.sh" OWNER_DECISION \
      "la storia $storia appartiene all'Epic 0: il loop non costruisce la propria infrastruttura"
    exit 12
  fi

  # 4. IL RAMO ----------------------------------------------------------------
  # Un ramo per iterazione. Se qualcosa va storto, il lavoro resta ispezionabile
  # invece di sparire, e main non vede mai un verdetto non emesso.
  base="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
  ramo="loop/iter-${avvio}-${storia}"
  ramo="$(printf '%s' "$ramo" | cut -c1-90)"
  git -C "$REPO" checkout -q -b "$ramo" 2>>"$DIARIO" || {
    log "impossibile creare il ramo $ramo"
    bash "$QUI/fermo.sh" REPO_INTEGRITY_RISK "creazione del ramo $ramo fallita"
    exit 12
  }
  log "ramo: $ramo (da $base)"

  # 5. IL RATCHET, SU UNA COPIA ----------------------------------------------
  # ratchet.py AGGIORNA il metro quando passa. Misurare contro l'originale
  # significherebbe misurare contro se stessi: il candidato passerebbe sempre.
  copia_metro="$STATO/.ratchet-candidato.json"
  cp "$BASELINE" "$copia_metro" 2>/dev/null || printf '{}\n' > "$copia_metro"

  # 6. I PASSI DEL PIANO ------------------------------------------------------
  passi="$(python3 -c "
import json
p = json.load(open('$piano_json'))['piano']
for i, s in enumerate(p):
    print('|'.join([s['passo'], s['modello'] or '-', s['effort'] or '-', s.get('ruolo','-')]))
")"

  fallito=0
  i=0
  while IFS='|' read -r tipo modello effort ruolo; do
    [ -z "$tipo" ] && continue
    i=$((i+1))
    log ""
    log "passo $i: $tipo${ruolo:+ [$ruolo]}"

    case "$tipo" in

      implementa|ripara)
        prompt="$STATO/.prompt-$i.md"
        { cat "$QUI/iterazione.md"
          printf '\n## La storia di questo giro\n\nChiave: `%s`\nClasse di rischio: %s\n' "$storia" "$classe"
          if [ "$tipo" = "ripara" ] && [ -f "$STATO/.rilievi.md" ]; then
            printf '\n## Rilievi da riparare\n\nUn revisore in processo separato ha prodotto questi rilievi.\n'
            printf 'Verificali prima di accettarli: un rilievo plausibile e falso costa piu di uno mancato.\n'
            printf 'Riporta esplicitamente quali confermi e quali refuti, con la prova.\n\n'
            cat "$STATO/.rilievi.md"
          fi
        } > "$prompt"
        passo_modello "$modello" "$effort" "$prompt" "$STATO/.uscita-$i.txt"
        e=$?
        cat "$STATO/.uscita-$i.txt" >> "$DIARIO"
        if [ "$e" != "0" ]; then
          log "  passo exit $e (watchdog o errore)"; fallito=1; break
        fi
        cp "$STATO/.uscita-$i.txt" "$STATO/.rapporto.md"
        ;;

      verifica)
        # Zero token. E' l'oracolo che chiude il passo, non un'affermazione.
        bash "$QUI/verifica.sh" > "$STATO/.metriche.json" 2>>"$DIARIO"
        e=$?
        log "  oracolo exit $e — $(cat "$STATO/.metriche.json" 2>/dev/null)"
        if [ "$e" != "0" ]; then log "  verifica rossa"; fallito=1; break; fi
        ;;

      revisiona)
        # Il revisore riceve il DIFF e il rapporto. Non il ragionamento.
        pacchetto="$STATO/.revisione-$i.md"
        { printf 'Sei un revisore avversario in un processo separato. Non hai partecipato\n'
          printf 'allimplementazione e non vedrai mai il ragionamento di chi lha fatta.\n'
          printf 'Cerca cio che MANCA, non solo cio che e sbagliato.\n\n'
          printf 'REGOLA: tu non ripari. Chi trova un rilievo non lo corregge.\n\n'
          printf '## Storia\n\n%s (classe %s)\n\n' "$storia" "$classe"
          printf '## Rapporto dellimplementatore\n\n'
          tail -120 "$STATO/.rapporto.md" 2>/dev/null || printf '(assente)\n'
          printf '\n## Diff\n\n```diff\n'
          git -C "$REPO" diff "$base"..HEAD 2>/dev/null | head -3000
          printf '\n```\n\n'
          printf '## Metriche degli oracoli\n\n%s\n\n' "$(cat "$STATO/.metriche.json" 2>/dev/null)"
          printf 'Elenco Markdown di soli rilievi. Niente severita, niente classifica.\n'
          printf 'Se non hai rilievi, ricontrolla e continua a pensare: non fermarti su una lista vuota.\n'
        } > "$pacchetto"
        passo_modello "$modello" "$effort" "$pacchetto" "$STATO/.rilievi.md"
        e=$?
        log "  revisione exit $e"
        cat "$STATO/.rilievi.md" >> "$DIARIO"
        if [ "$e" != "0" ]; then log "  revisore non ha concluso"; fallito=1; break; fi
        ;;

      analizza|confronta)
        log "  classe R3: la decisione appartiene al proprietario."
        bash "$QUI/fermo.sh" OWNER_DECISION \
          "la storia $storia e di classe R3: due analisi indipendenti e un confronto, poi decidi tu"
        fallito=1; break
        ;;

      *)
        log "  passo sconosciuto: $tipo"; fallito=1; break ;;
    esac
  done <<< "$passi"

  # 7. IL VERDETTO ------------------------------------------------------------
  if [ "$fallito" != "0" ]; then
    log ""
    log "iterazione $n NON promossa. Il ramo $ramo resta per l'ispezione."
    git -C "$REPO" add -A -- . ':(exclude)ops/loop/stato' >/dev/null 2>&1
    git -C "$REPO" commit -q -m "loop: iterazione $n non promossa ($storia)" \
        -m "Committato sul ramo perche cio che non e committato non e ispezionabile." \
        -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" >/dev/null 2>&1 || true
    git -C "$REPO" checkout -q "$base"
    exit 1
  fi

  # Residuo non committato: entra nel ramo PRIMA del ratchet. Cio che il
  # sistema non vede non esiste, e una riparazione intera si e gia persa cosi.
  if [ -n "$(git -C "$REPO" status --porcelain -- . ':(exclude)ops/loop/stato')" ]; then
    git -C "$REPO" add -A -- . ':(exclude)ops/loop/stato' >/dev/null 2>&1
    git -C "$REPO" commit -q -m "loop: iterazione $n — $storia" \
        -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" >/dev/null 2>&1 || true
  fi

  python3 "$QUI/ratchet.py" --metriche "$STATO/.metriche.json" --baseline "$copia_metro" >>"$DIARIO" 2>&1
  r=$?
  if [ "$r" != "0" ]; then
    log "RATCHET rosso: regressione. Non si promuove."
    git -C "$REPO" checkout -q "$base"
    bash "$QUI/fermo.sh" PRODUCT_KILL_CRITERION "ratchet rosso sull'iterazione $n ($storia). Ramo: $ramo"
    exit 12
  fi
  log "ratchet: verde"

  # 8. PROMOZIONE -------------------------------------------------------------
  if [ "$PROVA" = "1" ]; then
    log "prova: nessuna promozione. Ramo $ramo lasciato in piedi."
    git -C "$REPO" checkout -q "$base"
  else
    git -C "$REPO" checkout -q "$base"
    git -C "$REPO" merge -q --no-ff "$ramo" -m "loop: promozione iterazione $n — $storia" >>"$DIARIO" 2>&1
    m=$?
    if [ "$m" != "0" ]; then
      log "merge fallito."
      bash "$QUI/fermo.sh" REPO_INTEGRITY_RISK "merge del ramo $ramo su $base fallito"
      exit 12
    fi
    python3 "$QUI/ratchet.py" --metriche "$STATO/.metriche.json" --baseline "$BASELINE" --applica >>"$DIARIO" 2>&1
    log "promossa su $base; baseline aggiornata"
  fi

  log "pausa ${PAUSA}s"
  sleep "$PAUSA"
done

log ""
log "fine dopo $n iterazione/i. Giornale: $DIARIO"
exit 0
