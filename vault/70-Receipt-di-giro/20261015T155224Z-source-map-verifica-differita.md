---
storia: source-map-verifica-differita
istante: 20261015T155224Z
sha: 648ee34971e46f173c4517769d9a594becb86d1d
ramo: codex/k4-boundary-inspection-20261015
esito: differito
tipo: receipt-di-giro
---

# Giro 20261015T155224Z — source-map-verifica-differita

> Questa nota registra MISURE, non giudizi. Un giudizio di modello che
> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha
> verificato.

## Misure agli oracoli

| grandezza | valore |
|---|---|
| `test_passati` | 2544 Python;235 unit web;167 browser nel primo run |
| `test_falliti` | 0 Python;0 unit web;1 timeout browser nel primo run |
| `copertura` | 97.37% Python |
| `recinti` | PASS |
| `dominio` | 100% |
| `verde` | False |

## Esito: differito

## Revisioni

- Codex separato avversario: DEFER dell’unita, NO_CONTENT_APPROVE; APPROVE soltanto preservazione privata. Rapporto SHA256917a9cd7acd04ad15847e6a7b8be2d40db1ef5a10b44e0a7c56897ed8af71e44.

## Archi

- [[00-INDICE]]

## Ambito e identita

Main di riferimento verificato e2c0a40d6f5358d8623dce091251f0c2c9a317b8. Il commit648 dichiarato in testa contiene solo la precedente receipt main22 e il suo indice. L'aggiornamento source-map non ha un commit candidato: tre file non committati restano identificati separatamente e conservati nel checkout originale. Questa receipt documenta il differimento, non integra la patch o i suoi artifact.

Vite7.3.6 → PostCSS8.5.28 → source-map-js: risoluzione nativa locale1.2.1→1.2.2, soltanto version/resolved/integrity di una voce lock. Manifest, range e workflow invariati. Hash SHA256 dei tre file locali: lock8bc996e399ac1ccf1310a8ebe5ed14d59bb4e661fe85770ec41d7072163b8718; test230501ba0f4689d64a94a5a237c1a419383f6ce56d28ad29a6ca37b8ef664bb6; docf8c44531fae54d95cfba5af54734bba929cdc7d6b1530c0d347d1cc5056fdd74.

## Esecuzioni distinte

Il primo probe8FAIL conteneva sei mancate guardie e due controlli sani con API inadatta. Corretti soltanto i sani attraverso SourceNode, conservando posizione/contenuto/riapertura e aggiungendo uguaglianza del codice. RED qualificato6FAIL2PASS sul vecchio lock; medesimo test GREEN8PASS sul nuovo. Sei input invalidi restano constructor-only, senza serializzare offset enormi o tentare esaurimento di risorse. Il percorso legacy fromSourceMap/sourceRoot non e corretto da questa patch e resta da triagiare.

Nuovo npm ci,18 file installati uguali al pacchetto verificato,235 unit web/14suite, typecheck e build standalone/MCP PASS. Setup reference canonico prima di pytest:2544PASS0FAIL0SKIP/748.10s,97.37% (soglia95 invariata), domain100 e boundaries/diff PASS. Nessuna lettura holdout.923 percorsi HTTP MATCH0DIFF; rispetto alla build main22,922hash invariati e il solo manifest MCP cambia per il binding del digest lock. Bundle MCP e asset entry invariati. Non e un nuovo percorso matematico live.

Primo browser completo:222 risultati singoli,167PASS54skip opzionali con identita invariate,1timeout/0flaky/retry0. Il caso provenance-inspection desktop57 si ferma nella fixture page prima del callback. Risultato SHA256d5bf2e07812a71ce0db90b81c8e615d394dcbc668a426e05e399eac5fdd4fb3d, trace021414cd2af90253ea8674409bf774a06c3236b54e967e6cc7f4a7bac86cc6de. Il medesimo caso isolato passa in6437ms con30s/worker1/retry0 invariati: non riproduzione, non prova causale o sostituto del gate.

Una conferma completa invariata, con sola strumentazione dichiarata, e fermata in modo controllato sotto pressione osservata del sistema. Conteggi effettivi:5PASS,3timedOut,1interrupted,213senza risultato; zero record skipped. Il riepilogo214skipped NON e una misura di skip opzionali eseguiti. Risultato SHA256ae89bbe857f51b2b17156c47bd7b16c231d38326d767e14f4213cdcf7fd67d2c. Due timeout sono nel page setup; un terzo raggiunge UI/expect prima del timeout complessivo. Nessuna causa individuale dei ritardi e dimostrata. Il collector full-run rifiuta i casi senza risultato; finalizzazione separata mantiene tale errore e distingue i non eseguiti. Tutti i run precedenti restano conservati, nessun test/budget/skip indebolito.

## Disposizione

Gate browser non soddisfatto, unita DIFFERITA. Nessun contenuto approvato come pronto, nessun commit candidato/push/PR/CI/merge o remediation di main. La review separata approva soltanto una copia privata verificata dei tre file/diff e del commit receipt648; il bundle richiede main e2c0, non e un clone autosufficiente. Checkout originale mantenuto, server/browser/helper propri fermati; processi estranei non modificati.

L'audit locale resta exit1 con mocker/tinypool/vitest. Source-map assente nel solo audit del nuovo lock non integrato; advisory e raggiungibilita end-to-end restano nel triage WEB-DEPENDENCY-TRIAGE-2026-10-15. H3, K4 completo,21famiglie, design/pilot, issue20 e scroll349 restano aperti. Ardesia soltanto locale: ultima verifica4237 alle11:55 storica, nuove letture HEAD15s senza risultato; stato corrente non attestato. Nessuna nuova credenziale, spesa, deploy o release.

Prossimo passo: conservare i pin e riprendere la qualificazione canonica in un nuovo giro dichiarato quando le condizioni lo consentono, senza terza replica automatica di questo giro. Intanto prosegue soltanto intake/preflight K4 separata, senza dichiarare approvato un nuovo contratto o un prodotto completo.
