# Decisione — copertura globale senza regressioni e dominio al 100%

Data: 18 ottobre 2026. Stato: ADOTTATA SU DELEGA ESPLICITA DEL PROPRIETARIO.
Ambito: soglia e controllo di copertura; non è approvazione scientifica o gate di merge.

## Autorità e scelta

Alla domanda sulle due alternative di copertura il proprietario ha risposto:
«fai la cosa che reputi ingegneristicamente migliore». La decisione tecnica delegata è:

- minimo globale 95%, sommando righe e rami;
- nessuna regressione rispetto alla baseline versionata della suite completa;
- dominio al 100% di righe e rami, come prima;
- suite, confini, holdout, counter-metriche e review restano requisiti separati.

Il minimo globale 100% del processo legacy era già incoerente con la CI >=95% e la baseline
main 97,34% del dossier. L'obiettivo è proteggere il comportamento con test falsificanti,
senza incoraggiare test che ripetano l'implementazione per coprire ogni riga di I/O.
Il 95% non permette di spendere la copertura acquisita: vale anche la baseline più alta.

## Baseline e prova

`docs/quality/coverage-baseline.json` fissa 14.179 opportunità coperte su 14.516:
9.917/10.092 righe e 4.262/4.424 rami, **97,6784238082%**.
Fonte: suite Python 3.12 del candidato `c1cf22d1a8956552e9b07418a8382210d6af3a39`,
2.666 test passati, report coverage.py 7.15.4 generato il 18/10/2026.
La misura è locale macOS; CI sul nuovo candidato resta da eseguire prima del merge.
Differenze di ambiente vanno investigate, non compensate abbassando la baseline.

`scripts/check_domain_coverage.py`, già presente in CI, verifica la soglia globale dai
conteggi interi e il dominio separatamente. Il confronto usa prodotti interi, non percentuali
arrotondate. Report senza rami, conteggi incoerenti, baseline assente/invalida o dominio
assente falliscono. Una suite completa deve rigenerare coverage.json immediatamente prima
del gate: eseguirlo su un report vecchio non costituisce una nuova prova.

## Aggiornamento e rollback

I test non scrivono la baseline. Una nuova baseline richiede misura completa, provenienza,
review e decisione owner; abbassarla non è una normale riparazione del gate. Un incremento
confermato può diventare una nuova baseline attraverso lo stesso processo.

L'emendamento aggiorna soltanto il requisito di copertura in AGENTS fuori dal blocco gestito
e nella sezione di verifica del processo. Non attiva da solo il ritiro BMAD/Claude.
Rollback tramite revert del commit di questa unità; nessuna migrazione di dati.
