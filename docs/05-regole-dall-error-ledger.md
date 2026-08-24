---
title: 'Regole ereditate dall AGENT-ERROR-LEDGER di Ardesia'
created: '2026-08-24'
fonte: '~/ARDESIA-KNOWLEDGE/40-Capability-Evolution/AGENT-ERROR-LEDGER.md (65 voci, letto integralmente)'
---

# Perche' questo file esiste qui

Il ledger vive in Ardesia e Kirchhoff non lo legge. La sua stessa lezione piu' dura dice
che questo e' il problema: *«un ledger letto dopo aver sbagliato non ha impedito niente»*
(E-46), e *«catalogare un pattern non protegge dal pattern»* (E-58, commesso mentre si
scriveva la nota che spiegava gli altri cinque della stessa famiglia).

Quindi qui non c'e' un riassunto: c'e' l'elenco delle regole **con lo stato del controllo
eseguibile che le rende vere**. Una regola senza controllo e' prosa.

# La famiglia dominante: l'errore travestito da misura

Nove occorrenze consecutive nel ledger (E-15, E-53, E-60, E-61 e parenti). Forma:
un comando fallisce, l'errore viene soppresso o mangiato da una pipe, e il risultato
vuoto si presenta come una misura.

| Regola | Controllo eseguibile | Stato in Kirchhoff |
|---|---|---|
| Mai `cmd \| tail; echo $?` — l'exit e' quello dell'ultimo elemento della pipe | hook `measurement-gate` | ✅ **attivo** (mi ha fermato due volte il 24/08) |
| `2>/dev/null` non e' igiene, e' soppressione di prove | — | ❌ nessun controllo |
| Un `0` da un comando fallito non e' un'assenza | — | ❌ nessun controllo |
| Un gate puntato sull'oggetto sbagliato dichiara tutto pulito | `check_boundaries.py` solleva su radice inesistente; `--cov-report=json` negli addopts | ✅ **entrambi attivi** |
| La parte di un gate che decide cosa NON controllare va calcolata con lo stesso predicato del gate (E-62) | — | ❌ da applicare quando nascera' un ratchet |

Il difetto trovato il 24/08 — `check_domain_coverage.py` che leggeva un `coverage.json`
dell'11 agosto e dichiarava «domain/ al 100%» su file mai visti — e' esattamente questa
famiglia, ed e' stato cablato nella stessa iterazione che l'ha scoperto (regola §7 del
loop, `50-Lezioni-loop/Il gate scritto e non installato.md`).

# Regole sugli oracoli

- **Un test che non e' stato visto fallire non e' un test** (E-47, E-49). Ogni guardia nuova
  va falsificata contro l'implementazione che dovrebbe bocciare.
- **Un oracolo deve stabilire le sue precondizioni, non osservarle** (E-47): verde per
  inerzia se le trova gia' soddisfatte da altro.
- **Un oracolo va verificato nella sua raggiungibilita'**: un ramo che nessuno scenario
  raggiunge e' verde per costruzione e *sembra copertura*.
- **Un oracolo negativo — «non c'e'» — vale solo se dichiari dove hai guardato** (E-43, E-44).
- **Prima di dichiarare che qualcosa manca, esegui cio' di cui neghi l'esistenza** (E-58, E-64).
- **Congelare l'oracolo prima di iterare** (E-07); dopo due tentativi senza nuovo segnale,
  fermarsi e classificare invece di ritentare (E-20).

# Regole sulle misure

- Ogni claim determinante ha **un comando che lo produce**, e il comando deve produrre
  *quel* claim, alla *sua* granularita', sul *suo* referente (E-52 → E-54 → E-55).
- Un conteggio si legge dalla **struttura** che lo definisce, mai da `grep -c` su
  un'etichetta che compare anche in prosa (E-50).
- **Il punto cieco non e' il numero difficile: e' il numero che serve a giustificare
  qualcosa che hai gia' deciso** (E-56, E-57 trovati da un revisore *dopo* il commit;
  E-54, E-55 intercettati da soli *mentre* si cercava di falsificarsi).
- **Lo strato documentale non eredita l'affidabilita' dello strato eseguibile** e va
  verificato separatamente.
- Mai dedurre «riproducibile» da N < 10 (E-03); usare intervalli, non un campione (E-22).

# Regole che toccano direttamente CircuitCheck

Queste sono le voci che valgono per il prodotto, non per il processo.

1. **«Non compila» non e' «fallisce»** (Sessione 08-01, E-55). Un file che non compila
   *somiglia* a un test rosso e non lo e'. Trasposto: **un passaggio dello studente che non
   riusciamo a leggere non e' un passaggio sbagliato.** E' la distinzione ⚠️ *ambiguo* /
   ❌ *errato* che il prodotto deve mantenere, ed e' la difesa contro la falsa accusa.
2. **`grep` di una frase su testo a capo automatico** (Sessione 08-01, E-57): dieci ricerche,
   dieci zeri, **quattro falsi**, perche' il testo andava a capo dentro la frase. Trasposto:
   l'allineamento fra trascrizione OCR e testo di riferimento non puo' essere fatto su
   stringhe grezze — va normalizzato, o si producono assenze inventate.
3. **Riparare imponendo un formato che nessuno ha chiesto** (Sessione 08-01, E-59): un
   default a una cifra decimale ha trasformato `0.0153` in `0.0`. Trasposto: la
   formattazione dei numeri nella timeline e nel PDF si dichiara **al punto di chiamata**,
   mai per default globale. Vicino ad AD-4: il renderer sostituisce, non arrotonda.
4. **Separare produttore e discriminatore, conservando entrambi gli exit** (E-13): un
   discriminatore in pipe ha dichiarato fallita una lettura valida. Trasposto al confronto
   fra procedimento dello studente e soluzione verificata: chi produce il candidato e chi
   lo giudica non condividono canale.
5. **Uno script che muta lo stato deve terminare verificando lo stato atteso, non
   asserendolo** (E-65). Trasposto: `transform()` non dichiara il proprio `TransformResult`
   valido — lo fa verificare a `domain/transform/check`. E' gia' AD-22.

# Meta

Il ledger si dichiara `ACTIVE_APPEND_ONLY` e **fra il 27 luglio e il 2 agosto nessuno lo ha
alimentato**: sei difetti del 31 luglio non ci sono mai arrivati. Il posto dove le classi
«devono atterrare per non essere riscoperte» esisteva e non veniva scritto. E' la stessa
causa del «era gia' scritto e non e' stato letto».
