# Dal Claim alla derivazione e al passo che la produce

Data: 15 ottobre 2026. Verifiche locali e review dei contenuti concluse;
questa receipt fotografa il punto prima del commit degli artefatti. Pin esatto,
CI remota e main sono i passi successivi, non risultati anticipati.

Requisito H5/K4 già differito in `deferred-work.md`: seguire un'evidenza del
Claim fino al passo analitico reale, senza dedurlo dal numero nell'ID. La
`ProofSession` conserva già il legame autorevole; la proiezione lo perdeva.

## Modifica e compatibilità

Il nuovo `StepView.derivation_ref` copia direttamente
`AnalyticalProofStep.derivation_after`; vale `null` sulle trasformazioni.
Gli IR `evidence_refs` restano distinti e immutati. Produttore, parser web e
controllo operativo CLI esigono un mapping completo, unico e nello stesso
ordine degli `evidence_ids` del Claim. Il controllo CLI richiede inoltre
passi non vuoti: non certifica più un legacy senza alcun passo.

L'estensione additiva mantiene `student-session.v0.1`. Un legacy sano omette
il campo in tutti i passi: rimane leggibile e dichiara che il collegamento
non è esposto. Un campo soltanto presente, tutto-null, duplicato, pendente
o riordinato non viene scambiato per legacy. Gli ID restano opachi.
Rimuovere tutti i campi può degradare a legacy: non è autenticazione H3.

«Perché fidarsi» mostra ID, azione e passo. L'attivazione seleziona il passo
e mette a fuoco il suo dettaglio, anche se già corrente. Una nuova vista
annulla la richiesta del contesto precedente, anche se riusa lo stesso ID.
La selezione usa un solo callback esistente e lascia ad App normalizzare il
fotogramma. Rifiuto e guasto restano privi di risposta/evidenza positiva.
Token e temi esistenti, pulsanti da almeno 44px e testo adattabile.

## Controprove conservate

Prima della fonte: proiezione 3 FAIL; confini web/CLI 31 FAIL e 33 PASS;
duplicati contemporanei nel mapping e nel Claim 2 FAIL aggiuntivi. Quattro
callback realApp su due viewport danno 8 FAIL per collegamento/messaggio
assenti e mapping tutto-null accettato. Due estensioni avversarie — ID
opachi e nuova sessione già al target — danno 4 FAIL per link assente.
Il caso opaco desktop esaurisce anche il proprio budget di 30 secondi:
non viene promosso a run senza problemi di runtime.

Il primo harness componente aveva charset mancante: 2 PASS di lifecycle
e 2 casi focus NOT_TESTED per mojibake nel selettore. Conservato; corretto
solo UTF-8 del harness, il nuovo run dà 2 PASS e 2 FAIL per link mancante.
Il lifecycle era già sano: non si inventa un precedente bug degli hook.

Dopo l'aggiunta del solo campo, 14 mutanti backend falliscono e 4 controlli
passano; dopo le guardie, 87 test di presentazione passano. Un ulteriore
test scambia soltanto due trasformazioni, mantenendo il vettore analitico:
il canonico lo respinge e una copia privata senza la sola guardia d'ordine
lo accetta. Il primo probe aveva un errore di namespace della classe del
controllo sano; è preservato e distinto dal probe corretto discriminante.

## Produttore e cataloghi

Checkpoint preparatorio locale reale
`8a580e9658098b6f91fb16febe5396502c46c268`, tree
`6046471ea27bc8b1035ece13dd25ce48092d81cf`, parent main `edd29eac`.
La fonte di 18 file è stata revisionata separatamente prima del checkpoint;
quel verdetto preparatorio non era approvazione della futura unità.

Proof catalog: generatore canonico reale da Csrc pulito, 112 file di closure
di cui 108 Python; import fresco nel checkout e nessun resource override.
11 viste, 9 chiusure e 2 rifiuti, più indice. Tutti i campi vecchi restano
identici rimuovendo solo `derivation_ref` e normalizzando solo source_sha;
indice byte-identico. Scala con tre riduzioni: D1→indice3 e D2→indice4;
ponte D3→indice2/KCL. I JSON non sono stati scritti a mano.

Il primo full Python dà **1 FAIL e 2543 PASS**, coverage 97,37% con soglia
95% invariata: il test stretto del catalogo StudentApp rileva correttamente
il fingerprint globale aggiornato dei 108 Python. Nessun test o fingerprint
è stato indebolito. Anche le lezioni devono essere rigenerate.

La CLI esistente `scripts/serve_student.py --export`, senza opzione out,
è stata eseguita dal medesimo Csrc pulito dopo aver preservato e ripristinato
temporaneamente soltanto gli artefatti proof di questa unità. Scrive nella
sua destinazione canonica: 18 JSON, 18 PDF e indice, 4 esercizi. Closure di
113 file con launcher, sorgenti identici prima/dopo; il checkout diventa
legittimamente sporco per gli output. I nuovi proof e il loro audit vengono
poi ripristinati byte per byte. Nessun generator o solver modificato.

Nuovo lesson_build:
`f92d7d032ab63389e32de3572fc90f2c096ec2716dc13377b25c90664c93cbbc`.
Tutti i 18 JSON vecchi sono ricostruiti byte per byte sostituendo soltanto
source_sha e lesson_build; gli indici coincidono senza normalizzazione.
Il vero renderer riproduce esattamente tutti i 18 PDF vecchi e nuovi; il
nuovo JSON con i due header normalizzati produce esattamente il vecchio PDF.
Poppler conferma pagine, Subject e testo su tutte le 18 coppie, 105 pagine:
sola variazione del prefisso esatto del footer di revisione. Cover e ultimo
passo del PDF corrente-paralleli-auto ispezionati visivamente, due pagine;
non si dichiara di aver ispezionato visivamente tutte le 105 pagine.

I due manifesti in `docs/evidence/2026-10-15-h5-*-catalog-producer.json`
fissano Csrc/tree, closure e hash. Le vecchie receipt restano storiche e
non vengono riscritte. Due errori del solo audit privato — chiave title
anziché action e directory padre assente — sono conservati; CLI proof già
terminata con successo e nessuna rigenerazione ripetuta per correggerli.

## Gate e review

Gate locale completo: 2544 Python PASS in 251,00 secondi, copertura97,37%
con soglia95% invariata; dominio100%, confini exit0. Il primo run fallito
resta conservato come tale. Il test strict del catalogo invariato passa
da solo dopo rigenerazione. 227 unit web/13 suite, typecheck e build
standalone/MCP PASS. 16 nuove esecuzioni browser mirate PASS senza skip,
retry o flaky: 10 sul vero App/catalogo, 6 sul vero componente montato nel
harness privato in memoria. Config/output unici e assenza verificata prima
di ogni lancio. Nessun nuovo ingresso harness nel prodotto pubblico.

Suite browser completa: 160 PASS, 54 SKIP del profilo opzionale già previsto,
zero FAIL e zero flaky in 331,089 secondi; un worker, retries 0 e timeout
canonici. Il pin di tutti i contenuti sotto verifica è invariato prima/dopo.
Questi 160 includono i 16 nuovi casi, eseguiti anche nel run mirato distinto.

Verifica HTTP locale successiva alla rigenerazione StudentApp: 923 file
serviti byte-identici alla build, zero differenze. Il fumo sui 11 proof
è PASS. Sono verifiche operative, non un secondo certificatore elettrico.

Quattro PNG reali desktop/mobile ispezionati dal writer. Mostrano il
dettaglio selezionato e le nuove derivazioni; screenshot mobile di viewport
scrollato, non tutta la pagina. Il KCL lungo resta scorrevole dentro il
riquadro: il DOM è confrontato all'equazione del produttore, non si sostiene
che la riga completa sia visibile nel PNG. Overflow orizzontale del documento
asserito nullo nella navigazione canonica; nessuna dichiarazione globale
di assenza di pageerror per callback che non li raccolgono.

Interoperabilità locale con Ardesia `22e5a8bc`, sorgenti invariati e checkout
pulito: le 18 lezioni reali rigenerate sono accettate dal vero adapter,
preservano sourceSha/lessonBuild e attraversano il roundtrip dello stato
serializzato. Gli oggetti letti sono identici ai precedenti salvo i due
header; tre mutanti (ProductVerified true, build invalido, netlist richiesta
estranea) sono respinti. È un probe dei moduli reali trasformati in memoria,
con TypeScript già installato in Kirchhoff/web; l'espressione import.meta.env
del trasporto non invocato è adattata per caricarli in CommonJS. Non è una
nuova prova browser, IndexedDB, durabilità, stato corrente o fullgate Ardesia.
Il primo avvio del probe aveva il percorso del compilatore errato e non
aveva caricato alcun modulo prodotto: NOT_TESTED conservato, senza installare
dipendenze o modificare Ardesia per correggere il collaudo.

Review primaria del writer, 15 ottobre: APPROVE dei contenuti, esplicitamente
non indipendente dall’implementazione. Report SHA256 `85140ef0604e6c86c86f3e6ef7feb782ae44f2df9f6aebe733907f7a37d09463`.
Review avversaria Codex separata, 15 ottobre: APPROVE_TESTED_UNIT_CONTENT,
zero P0/P1 e nessun nuovo blocker. Report SHA256 `650b545100afcfcf5183f9fb0a9bf7d7854177eecf449377e921155b10619be2`.
Include falsificazioni proprie su parser/helper reali: tre controlli sani e
otto mutanti, oltre ai confronti di producer e PDF. Modello runtime esatto
non esposto. I due report sono riferiti al contenuto congelato prima del ledger.
Il normale commit degli artefatti e il relativo tree non esistono ancora al
momento di questa receipt. Le due successive review del pin e la CI esatta
saranno registrate nel gate della PR. Non è ancora AI_REVIEW_GATE_PASSED.

L'eccezione del proprietario consente il reviewer Codex avversario separato
solo per questa esecuzione, mantenendo gli altri gate e protezioni; nessuna
modifica permanente della policy o approvazione GitHub impersonata.

## Limiti e prosecuzione

Affrontato il collegamento di navigazione H5/K4. Ispezione completa di
residui, cross-check, terminal mapping, autenticazione H3 e provenienza
completa restano aperti. Nessuna nuova famiglia matematica, modifica a
Verified/solver/soglie/privacy o pilot umano. Design e accessibilità globale
restano parziali; issue20/runtime e scroll host349 mantengono destinazione.
Ardesia resta soltanto locale per istruzione del proprietario.

NEXT_ACTION: verificare receipt/deferred/indice e pin del normale commit
locale; dopo controllo degli effetti automatici, push del solo branch
Kirchhoff e draft PR su main, CI push/PR esatta e gate completo; eventuale
merge ordinario consentito, poi verifica del nuovo main. Nessun deploy
o cancellazione di branch.

## Archi

- [[00-INDICE]]
