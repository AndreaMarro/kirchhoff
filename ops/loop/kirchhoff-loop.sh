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
# Il tetto per un passo che SCRIVE viene dal precedente del proprietario su
# Ardesia: BUDGET=25, alzato deliberatamente il 2026-08-15 («dovrebbero avere
# piu' tempo»). Un tetto piu' stretto non e' prudenza: e' un'iterazione tagliata
# a meta'. Misurato il 24/08 con --budget 4: l'implementatore aveva prodotto 977
# righe su 8 file quando e' stato interrotto, a lavoro incompleto.
# Le revisioni leggono e non scrivono: tetto separato e piu' basso.
BUDGET_SCRITTURA=25
# **15, non 8.** Il primo giro di prodotto e morto qui: il Blind Hunter ha colpito
# il tetto dopo 6m38s con «Exceeded USD budget (8)» e il giro e stato buttato dopo
# aver gia pagato l'implementazione. Le tornate manuali dello stesso revisore, sullo
# stesso modello e sullo stesso effort, giravano a 12 e completavano. Un tetto che
# uccide il passo incaricato di dire se il lavoro e buono non protegge: spreca il
# passo precedente.
BUDGET_REVISIONE=15
WATCHDOG=2700           # 45 minuti: oltre, si uccide
PAUSA=20                # respiro fra iterazioni
ITERAZIONI=1
PROVA=0
# La promozione su main NON e' automatica. Il proprietario ha stabilito che il
# loop diventa il motore normale di sviluppo solo DOPO evidenza positiva: fino
# ad allora ogni giro finisce su un ramo che una persona ispeziona. E resta la
# risposta al buco che il collaudo ha reso visibile — l'ultima revisione produce
# rilievi che nessun cancello deterministico sa giudicare, e un verdetto di
# modello non puo' aprire un merge.
PROMUOVI=0

while [ $# -gt 0 ]; do
  case "$1" in
    --iterazioni) shift; ITERAZIONI="${1:-1}" ;;
    --prova)      PROVA=1; ITERAZIONI=1 ;;
    --promuovi)   PROMUOVI=1 ;;
    --pausa)      shift; PAUSA="${1:-20}" ;;
    --watchdog)   shift; WATCHDOG="${1:-2700}" ;;
    --budget)     shift; BUDGET_SCRITTURA="${1:-25}" ;;
    --budget-revisione) shift; BUDGET_REVISIONE="${1:-8}" ;;
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
# Si SCRIVE in stato/ — che git ignora — e si INCIDE in giornale/ alla fine.
# Scrivere direttamente nell'albero tracciato blocca ogni cambio di ramo: git
# rifiuta il checkout con un file modificato non committato, e il loop resta
# appeso sul ramo dell'iterazione. Misurato al primo `run --prova`.
DIARIO="$STATO/corrente.log"
: > "$DIARIO"
INCISO="$GIORNALE/${avvio}-ITERAZIONE.log"
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$DIARIO"; }

# Il giornale si incide su OGNI uscita, non solo su quella felice: un giro che
# muore e' esattamente quello di cui serve la traccia. `trap` garantisce che
# valga anche per il watchdog e per un'interruzione manuale.
incidi_giornale() {
  local codice=$?
  [ -s "$DIARIO" ] || return 0
  mkdir -p "$GIORNALE"
  cp "$DIARIO" "$INCISO"
  if [ -n "$(git -C "$REPO" status --porcelain -- ops/loop/giornale 2>/dev/null)" ]; then
    git -C "$REPO" add ops/loop/giornale >/dev/null 2>&1
    git -C "$REPO" commit -q -m "loop: giornale $avvio (uscita $codice)" \
        -m "Append-only: un file per iterazione, mai riscritto." >/dev/null 2>&1 || true
  fi
}
trap incidi_giornale EXIT

log "kirchhoff-loop v3 — avvio"
log "repository=$REPO"
log "iterazioni=$ITERAZIONI prova=$PROVA promuovi=$PROMUOVI watchdog=${WATCHDOG}s scrittura=\$${BUDGET_SCRITTURA} revisione=\$${BUDGET_REVISIONE}"

  # **Il Mac non deve dormire durante un giro.** Un'iterazione R2 dura un'ora
  # abbondante e i passi sono processi figli: se la macchina si sospende, il
  # watchdog scade su un processo che non stava lavorando e il giro viene buttato
  # dopo aver gia' pagato. `-w $$` lega la veglia alla vita di QUESTO script, quindi
  # si spegne da sola quando il giro finisce — anche se finisce male.
  if command -v caffeinate >/dev/null 2>&1; then
    caffeinate -dimsu -w $$ &
    log "caffeinate: la macchina resta sveglia per la durata del giro"
  fi

# --- il watchdog --------------------------------------------------------------
# Ardesia: TERM, dieci secondi di grazia, poi KILL. Il segnale di stop deve
# venire da FUORI dall'agente: un agente che decide da solo quando fermarsi ha
# gia' dimostrato di predire oltre il 70% di fattibilita' dopo aver bruciato il
# 60% del budget.
con_watchdog() {
  local uscita="$1"; local ingresso="$2"; shift 2
  # **stderr in un file suo.** Con `2>&1` il messaggio «Exceeded USD budget» e
  # finito DENTRO `.rilievi.md`, cioe nel file che il passo di riparazione legge
  # come «rilievi da riparare»: un errore travestito da rilievo. Ora l'uscita del
  # modello e il suo rumore restano separati, e il rumore viene mostrato quando
  # serve — cioe quando il passo fallisce.
  "$@" < "$ingresso" > "$uscita" 2> "$uscita.err" &
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
  local modello="$1" effort="$2" prompt_file="$3" uscita="$4" tetto="$5"
  log "  → claude -p --model $modello --effort $effort --max-budget-usd \$$tetto"
  if [ "$PROVA" = "1" ]; then
    log "    [prova] nessun processo invocato"
    printf '(prova: nessuna invocazione)\n' > "$uscita"
    return 0
  fi
  # Il prompt arriva da STDIN, come in Ardesia (`cat ... | claude -p`). La prima
  # versione lo passava solo via --append-system-prompt e non dava nessun prompt
  # utente: `claude -p` sarebbe rimasto senza compito. Trovato prima di spendere,
  # non dopo.
  con_watchdog "$uscita" "$prompt_file" env -C "$REPO" claude -p \
      --model "$modello" \
      --effort "$effort" \
      --dangerously-skip-permissions \
      --disallowed-tools Workflow \
      --max-budget-usd "$tetto" \
      --setting-sources project,local
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

  # **Se la storia fissata e' gia' su main, avanza.** Senza questo il loop rifa'
  # all'infinito la stessa storia: `prossima-storia.txt` veniva scritto da
  # `dry-run` e non piu' toccato, quindi dopo la promozione di 1.1 il giro
  # successivo avrebbe reimplementato 1.1.
  #
  # «Gia' fatta» si deriva da cio' che esiste davvero: l'artefatto di
  # implementazione della storia, con la sua chiave INTERA. Il prefisso da solo non
  # basta — `spec-1-2-script-di-valutazione` e' una storia della v1 e collidere
  # con la 1.2 della v2 sarebbe precisamente l'errore che il ledger disallineato
  # gia' commette.
  if python3 "$QUI/catena.py" --fatta "$storia" 2>/dev/null; then
    prossima="$(python3 "$QUI/catena.py" --dopo "$storia" 2>/dev/null)"
    if [ -n "$prossima" ]; then
      log "storia $storia gia' su main: avanzo a $prossima"
      printf '%s\n' "$prossima" > "$STATO/prossima-storia.txt"
      storia="$prossima"
    else
      log "catena esaurita: nessuna storia dopo $storia"
      exit 0
    fi
  fi
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
          # **La Story, non solo la sua chiave.** L'implementatore riceveva chiave e
          # classe e nient'altro: avrebbe dovuto sapere da se' che `epics.md` esiste,
          # che la chiave vi corrisponde a un'intestazione, e andarsela a cercare.
          # La Story 1.1 pretende per esempio che «il test negativo sia VISTO rosso
          # rimuovendo la guardia», con l'output della mutazione come evidenza: un
          # criterio che nessuno soddisfa senza leggerlo.
          #
          # La sorgente e' la stessa da cui viene la chiave: nessuna seconda verita'.
          printf '\n## La storia di questo giro\n\nChiave: `%s`\nClasse di rischio: %s\n\n' "$storia" "$classe"
          printf 'Il testo che segue e la Story cosi come vive in `epics.md`, che e\n'
          printf 'l artefatto BMAD che la possiede. I criteri di accettazione sono\n'
          printf 'quelli, non una loro parafrasi.\n\n'
          python3 "$QUI/chiave.py" --corpo "$storia" 2>/dev/null || printf '(Story non trovata in epics.md)\n'

          # **Il vault, non solo la Story.** La Story dice cosa costruire; non dice
          # quali decisioni sono gia' prese, quali sono APERTE, e cosa i giri
          # precedenti hanno imparato a proprie spese. Quel sapere vive nel vault e
          # nessuno lo passava a chi implementa — che percio' poteva chiudere per
          # inerzia una questione che il proprietario aveva lasciato aperta.
          printf '\n'
          python3 "$QUI/contesto.py" --storia "$storia" 2>/dev/null || true
          if [ "$tipo" = "ripara" ] && [ -f "$STATO/.rilievi.md" ]; then
            printf '\n## Rilievi da riparare\n\nUn revisore in processo separato ha prodotto questi rilievi.\n'
            printf 'Verificali prima di accettarli: un rilievo plausibile e falso costa piu di uno mancato.\n'
            printf 'Riporta esplicitamente quali confermi e quali refuti, con la prova.\n\n'
            cat "$STATO/.rilievi.md"
          fi
        } > "$prompt"
        passo_modello "$modello" "$effort" "$prompt" "$STATO/.uscita-$i.txt" "$BUDGET_SCRITTURA"
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
        passo_modello "$modello" "$effort" "$pacchetto" "$STATO/.rilievi.md" "$BUDGET_REVISIONE"
        e=$?
        log "  revisione exit $e"
        cat "$STATO/.rilievi.md" >> "$DIARIO"
        if [ "$e" != "0" ]; then
          log "  revisore non ha concluso"
          # Il PERCHE, non solo il fatto. La prima corsa diceva «non ha concluso» e
          # basta: la causa — un tetto di budget — stava in un file che nessuno apriva.
          [ -s "$STATO/.rilievi.md.err" ] && log "  causa: $(tail -1 "$STATO/.rilievi.md.err")"
          fallito=1; break
        fi
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
  if [ "$PROVA" = "1" ] || [ "$PROMUOVI" != "1" ]; then
    git -C "$REPO" checkout -q "$base"
    if [ "$PROVA" = "1" ]; then
      log "prova: nessuna promozione. Ramo $ramo lasciato in piedi."
    else
      log "giro verde, NON promosso: manca --promuovi."
      log "Ispeziona il ramo, poi decidi:"
      log "  promuovere: git merge --no-ff $ramo"
      log "  scartare:   git branch -D $ramo"
      log "I rilievi dell'ultima revisione sono nel giornale: nessun cancello"
      log "deterministico sa giudicarli, e un verdetto di modello non apre un merge."
    fi
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
log "fine dopo $n iterazione/i. Giornale: $INCISO"
exit 0
