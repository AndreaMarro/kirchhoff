# Convergenza integrata, main verificato e chiusure tracciate

Data: 15 ottobre 2026. Main `edd29eac7511db379437c6b8a06426b46d1b0f5c`,
tree `65523b5dbf52d4c5e599614ecbbe39211f0cbae5`, parent `42861a7` e `f7d4994`.
La PR17 è stata integrata con merge ordinario: nessun admin, force push,
squash, rebase o cancellazione di branch. Il tree coincide con il candidato f7
approvato dalla review primaria e dal reviewer Codex avversario separato.
L'eccezione alla diversa famiglia del reviewer è autorizzata dal proprietario
soltanto per questa esecuzione; gli altri gate e le protezioni restano invariati.

## Verifiche sul main effettivo

- [CI Python 38708418331](https://github.com/AndreaMarro/kirchhoff/actions/runs/38708418331):
  checkout main esatto, 2523 PASS e 3 SKIP, coverage 97,32% con soglia 95%,
  dominio 100%.
- [CI web 38708418414](https://github.com/AndreaMarro/kirchhoff/actions/runs/38708418414):
  checkout main esatto, 191 unit test in 12 suite, 144 browser PASS e 54 SKIP.
- Build locale pulita: typecheck e bundle standalone/MCP PASS. Le dipendenze
  sono quelle congelate già verificate nelle unità integrate; questo build
  non viene presentato come una nuova installazione completa della toolchain.
- API locale riavviata su main, senza provider: i quattro solve del percorso
  reale riportano source_sha main, risposta `1/250 A` per `12/(1000+2000)` e
  `product_verified=false`.

Il fingerprint `lesson_build` è
`cd4299c19bcc98a2c1d56370451e945ecaf3897e288c1ed92aab7b9a5a5c1326`.
È un digest del codice, distinto dal Git SHA: il reviewer lo ha ricostruito
indipendentemente dai 108 sorgenti Python committed.

Il percorso DC è stato collaudato su desktop 1440×900 e mobile 390×844:
prima/dopo distinti; lettura incerta `not_assessable`; dopo chiarificazione,
primo errore al passaggio 2 (`4 A` dichiarati contro `1/250 A`); PDF reale,
quaderno v2 e riapertura in nuovi contesti browser con tentativo preservato
e diagnosi ricalcolata. Otto esecuzioni permanenti main PASS coprono i tre
casi capabilities/catalogo e il rifiuto senza risposta, su entrambi i viewport.

PDF desktop/mobile identici: 6 pagine, 49775 byte, SHA256
`1c1f393de1559113dbf5954575d10c4904f0b0f9cd28637e131e0c79be8b32b2`.
Quaderni identici: 677 byte, SHA256
`34b13e1a69e263352dea58fe5087e59c30299fa6becfb8ab4e78e77335dda94a`.
Il PDF contiene la lezione; il tentativo dello studente è nel quaderno.
Source SHA è nei metadata Subject, mentre il footer usa lesson_build.
Quattro schermate e tutte le sei pagine rasterizzate sono state ispezionate
dal writer e dal reviewer. Nessun taglio materiale osservato; overflow del
documento ed errori pagina nulli nei punti misurati. Due azioni Space/Enter
sono provate: non è una certificazione WCAG, PDF/UA o un pilot umano.

Il primo harness privato ha prodotto 1 PASS desktop e 1 FAIL mobile: cercava
l'indice laterale nascosto a larghezza mobile. CSS e snapshot mostrano i
pulsanti «Passaggio» disponibili. Corrette solo le due selezioni del harness,
il nuovo caso mobile passa in 42,9 secondi. Il fallimento resta conservato;
nessun prodotto, timeout permanente, skip, retry o expected è stato indebolito.
I due run finiti mobile/permanenti si sono brevemente sovrapposti: nessuna
misura di performance isolata viene attribuita loro. Anche l'assert iniziale
dell'estrattore PDF, che cercava il Git SHA nel testo anziché nei metadata,
è registrato come errore del collaudo, senza modifica del prodotto.

Review post-merge separata Codex, 15 ottobre: APPROVE nel perimetro
CI/build/provenienza/percorso DC e idoneità delle chiusure. Report SHA256
`a61e537428571ea464e2d109ae3f34cbe7162c9461033f218c3db4fc0c3d3aa0`.
Nessun nuovo P0/P1. L'identificativo esatto del modello runtime non è esposto;
non si attribuiscono indipendenza statistica o approvazioni GitHub impersonate.

## Esiti e conservazione

- [PR17](https://github.com/AndreaMarro/kirchhoff/pull/17): MERGED sul main sopra.
- [PR15](https://github.com/AndreaMarro/kirchhoff/pull/15): GitHub l'ha marcata
  MERGED dopo PR17; mergeCommit `71aa0cf6`, ora antenato main. Non è stato
  eseguito un secondo merge manuale della PR15.
- [PR16](https://github.com/AndreaMarro/kirchhoff/pull/16): CLOSED come
  recuperata via PR17, dopo prova di main. Head `0adc225` e parent senza PR
  `bfa5e25` sono antenati reali. Catalogo di 11 esempi proof DC, 9 chiusure e
  2 rifiuti, produttore pulito committed `4a93e24` e closure di 112 file;
  recuperati anche host, script e documenti con gli adattamenti verificati.
  Non sono 11 famiglie StudentApp.
- [Issue19](https://github.com/AndreaMarro/kirchhoff/issues/19): CLOSED/COMPLETED
  dopo i sei casi capabilities main. I precedenti live RMS e il run d11 da
  24 PASS restano attribuiti ai rispettivi predecessori; nessun nuovo RMS
  main viene inventato.
- PR7: CLOSED senza merge; il lavoro recuperabile non integrato resta nella
  [issue18](https://github.com/AndreaMarro/kirchhoff/issues/18).

L'inventario remoto iniziale è risolto con zero PR aperte alle 09:25 UTC.
Questo non completa tutti i requisiti del prodotto. Branch originali e parent
sono conservati; gh-pages resta
`f24e4a8b03b2de5c05368a4556a2454e8cf6196c`, anche dopo le chiusure.
Nessun deploy, release, acquisto, nuova credenziale o modifica di
costituzione, soglie e protezioni. Ardesia `22e5a8bc` resta soltanto locale
per istruzione del proprietario.

## Prosecuzione

Goal attivo. Prossima unità H5/K4: esporre il legame già autorevole
Claim → derivation_after → passo, senza inferire D1 dal numero di un passo
e senza un secondo solver. L'ispezione completa di residui e cross-check
resta aperta. Restano anche issue20 P3 sull'affidabilità locale, scroll host
349 px P3, le 21 famiglie complete, design/accessibilità, firma H3 e pilot.
La matrice privata distingue codice in main, campioni dei predecessori e
live realmente eseguiti; nessuna famiglia è promossa completa.

NEXT_ACTION: test RED del legame perso, proiezione minima, guardie,
navigazione e focus; produttore committed pulito e rigenerazione del catalogo;
verifiche, review, CI esatta, eventuale merge ordinario e prova del nuovo main.

## Archi

- [[00-INDICE]]
