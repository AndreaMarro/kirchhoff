# Algebra AC e formule PDF — checkpoint del 3 ottobre 2026

Le lezioni AC RLC con sorgenti V/I indipendenti mostrano ora sostituzioni nelle KCL, raccolta dei coefficienti, vincoli delle sorgenti flottanti, eliminazione esatta con fattori e razionalizzazione, incognite isolate e recupero ai morsetti richiesti. La potenza conserva il contratto RMS/picco e i controlli precedenti.

## Contratto e controllo

- `steps[].math` contiene equazioni strutturate; numeri sulla base esatta `1,zeta12,zeta12²,zeta12³`, simboli, somme, prodotti e divisioni. `equations` è la proiezione testuale leggibile dello stesso albero.
- `answer.math` e `answer.display_exact` sono additivi. `answer.exact`, `phasor` e `complex_power` restano compatibili.
- `algebra.schema = ac-algebra.v1`, `status = EXACT_OPERATIONS_CHECKED`, `canonical_proof = false`. Le tuple di verifica elettrica non cambiano e `product_verified` resta `false`.
- Il verificatore ricostruisce le equazioni dall'incidenza, dalle impedenze e dalle fasi. Usa coppie rettangolari di razionali in Q(sqrt(3)), senza importare il builder, Cyc12 o un solver. Controlla ogni scambio, fattore, eliminazione, coniugato e recupero di ramo, inclusi riferimenti e unità delle righe.
- Il PDF compone frazioni vettoriali, radicali e pedici dall'AST; porta testo accessibile `ActualText`, titolo, autore e revisione/input nei metadati. Non ricalcola il circuito. `source_sha` identifica la base Git; `lesson_build` identifica i contenuti del checkpoint.

## Misure

Comando locale eseguito dalla radice Kirchhoff:

```sh
.venv/bin/python -m pytest tests/test_ac_algebra.py tests/test_ac_lesson.py tests/test_ac_power_lesson.py tests/test_lesson_svg_reactive.py tests/test_lesson_math_pdf.py --no-cov -k 'not http'
```

151 PASS; 5 test HTTP esclusi perché questa sessione non può aprire socket. Dopo l'ultima rifinitura della proiezione dei segni: 44 PASS su `test_ac_algebra.py` e `test_lesson_math_pdf.py`. Il processo root ha inoltre riportato 2349 PASS e copertura 96,92% sulla suite completa precedente a quella sola rifinitura; la sua ricevuta registra HTTP e browser.

Review indipendente: 48 supernodi flottanti, 12 fasi e inversioni di V/I; errore numerico massimo 1,79e-15 rispetto alle equazioni manuali. Nove mutazioni respinte, inclusa la sostituzione reale del coniugato con l'identità. I test permanenti respingono anche omissioni, coefficienti, segni, riferimenti e passi alterati.

## Artefatti

Directory locale esterna a Git: `/Users/andreamarro/MATJOURNEY/kirchhoff-ac-algebra-evidence-20261003/`.

- `series.json/pdf`: lezione RLC, 14 passi, 17 pagine.
- `floating.json/pdf`: sorgente flottante e potenza di picco, 17 passi, 25 pagine.
- `targeted-tests.log`, `final-projection-tests.log`, `audit-*`, `receipt.json` e `receipt.sha256`.
- Revisione di questi artefatti: `2157f374ff4d7c00b9a1f8522f823fa551a1a8e9bdf44a4d51a33dc9f7e42cad`.

Il caso autorizzato 11.17 è separato nel corpus privato: `eserciziario-11-17-algebra-lesson.json/pdf` e `eserciziario-11-17-algebra-receipt.json`. Quattordici passi, 18 pagine ispezionate, risultato esatto `700/29 + j 300/29 V RMS` conforme alla KCL manuale. La ricevuta conserva il legame con la precedente evidenza RMS; i vecchi artefatti restano intatti. Conferma umana e revisione docente sono `false`. Nessun nuovo browser privato viene rivendicato da questa ricevuta.

## Limiti e seguito

Il mandato complessivo resta PARTIAL. Il nuovo controllo non completa la lineage canonica del ProofGraph e non estende le famiglie servite. L'eliminazione generale può produrre documenti lunghi; coefficienti esatti eccezionalmente grandi richiedono adattamento della larghezza. Il prossimo lavoro assegnato riguarda l'identità del processo: un server avviato prima di una modifica ai sorgenti deve rifiutare nuovi risultati fino al riavvio, invece di attribuire al vecchio codice l'hash dei file aggiornati.
