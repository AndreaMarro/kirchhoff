# Correzioni del procedimento e della dichiarazione del quaderno

Data: 15 ottobre 2026. Base701a8e6b859665c6daa97b477f9661fbc47881f6,
treeb19c8623319f5b92b113dcbc17379422aecc5edf. Questa receipt registra una
correzione locale; commit futuro, CI e integrazione in main sono ancora pendenti.

## Requisito, controesempi e modifica

La review avversariale consolidata contro main42861a7 ha individuato due P2:
C701-1, modificare un passaggio mentre il controllo è pendente invalida la
richiesta ma lascia busy per sempre; C701-2, il README nega la foto nel JSON,
mentre il quaderno v2 conserva originale, nome e immagine preparata.
Il report REQUEST_CHANGES701 è conservato, SHA256
688964d6a90675fafeefdfb41640f86d0dba821412f42b8af76c57d798531453.

Controprova browser preliminare: due controlli sani PASS, due race FAIL.
I due nuovi callback permanenti, eseguiti desktop/mobile sulla fonte precedente,
producono quattro FAIL pertinenti: pulsante bloccato e descrizione accessibile
assente. I quattro callback originali restano prefisso byte-identico; nessun
expected, timeout, soglia, esclusione o skip è cambiato.

StudentTrace ora chiude il busy quando l'input viene sostituito; tutte le guardie
di generazione su successo, errore e finally restano. Una risposta vecchia non
chiude il controllo nuovo e non ripristina una diagnosi superata.
StudentApp annuncia vicino a Salva quaderno i contenuti condivisi, incluso il
file originale con nome e l'immagine, quando appartenenti alla lezione attuale.
Il medesimo predicato di ownership governa il serializer. Non sono stati cambiati
schema, byte esportati, conferma della fonte, privacy del server o credenziali.
README distingue v1/v2, riapertura, fonti conservate e limiti DC/AC/Laplace.
I vecchi documenti current-state datati rimangono fotografie storiche.

## Misure e limiti delle verifiche

191 unit web PASS/12suite, typecheck PASS, build standalone/MCP PASS.
Student-session completo12PASS desktop/mobile: vecchia risposta durante nuova
richiesta, controllo successivo funzionante, avviso prima del download e byte
della fonte invariati; anche i quattro callback precedenti passano.

La suite browser completa termina con140PASS/4FAIL/54SKIP in21minuti.
Quattro timeout osservati sono conservati: rail/beforeEach, host/setup pagina,
workbench/beforeEach e validation con chiusura della sessione del protocollo.
Non sono un gate verde e la causa non è dimostrata. Il Mac mostra memoria
compressa e swap elevati; tre anteprime di tranche concluse sono state fermate
dopo verifica di PID/comando/cwd, senza toccare processi estranei o dati.
Una singola riesecuzione mirata dei quattro casi passa4/4 in40secondi, con
identiche assert, timeout e retry0; non sostituisce il run completo fallito.
Il gate completo richiede la CI del nuovo SHA; la CI701 verde
non viene attribuita a queste quattro nuove fonti.

Foto/PDF live con server reale:3PASS/1FAIL in2.3minuti. Nel PDF desktop la
finestra resta occupata oltre l'assert da5000ms: trace mostra source200/1686ms,
confirm200/174ms e solve200/5890.991ms. Il body solve non è catturato: nessun
risultato gli viene attribuito. PDF mobile e foto desktop/mobile passano già.
Una sola replica invariata del PDF desktop passa1/1, test27.6s/run1.2minuti,
verificando anche originale, pagina2, ritaglio e byte del quaderno. Il3/1 resta
una misura distinta; non si riscrive come4/0. Nessun timeout, retry o prodotto
modificato. Compressione/swap non sono dichiarati causa dimostrata di ogni ritardo.

Quattro PNG nuovi desktop/mobile sono stati letti dal writer e dal reviewer:
avviso e procedimento, overflow orizzontale0 ed errori pagina0. PNG1x1 e diagnosi
sono fixture esplicite, non OCR, prova matematica o pilot umano. Su mobile il
paragrafo continua sotto la viewport iniziale; non si afferma visibilità integrale
in una sola schermata o conformità completa con screenreader.

Il reviewer separato ha eseguito sei probe del vero TSX per busy/supersession e
sette confronti ownership/disclosure/serializer, inclusi PDF, fonte estranea,
prepared-only e lavagna: conformi. Report preliminare PENDING_GATES,
SHA256255ff130aa5c17fe552f821ed70dfee85f43455efb5850ade2eed84af50bd3f1.
La review tecnica draft dei quattro hash approva il checkpoint, mantenendo il
gate main pendente: SHA256c44a91ddf58ce7b60bec67243678900b1effc13f642af18e2b1126de561443dd.
Pin, classificazioni finali e receipt AI_REVIEW_GATE sul candidato esatto saranno
registrati nella PR17 prima di qualunque merge; nessun quorum anticipato.

## Autorità e prosecuzione

Il proprietario ha autorizzato per questa sola esecuzione un secondo reviewer
Codex in contesto separato al posto del requisito della diversa famiglia/tool.
La decisione di governance adottata non è modificata: rimangono exact-SHA CI,
review avversariale, zero P0/P1 aperti, destinazioni P2/P3 e protezioni GitHub.
L'eccezione non attribuisce indipendenza statistica a due sessioni dello stesso
modello e non è un'approvazione GitHub impersonata. Ardesia resta soltanto locale.

C701-1/C701-2 e il disallineamento README C701-3 sono affrontati in questa fonte
locale; integrazione da provare. H5/K4 navigazione delle evidenze resta P2 con
destinazione prima unità prodotto H5/K4. Scroll host349 resta P3 con destinazione
unità isolata UX scroll host/frame. Le21famiglie, design completo, pilot e firmaH3
non sono dichiarati conclusi. La perdita dei sei PNG storici e i due metadataCI
locali illeggibili restano limiti documentati, non riparazioni inventate.

NEXT_ACTION: finire diagnosi/gate browser; pin fonte/ledger e review separata;
commit, CI esatta, review consolidata e protezioni; retarget17→main e merge ordinario
solo se consentito, verifica main, poi chiusure motivate15/16/19. Nessun deploy,
release, eliminazione branch, force-push o cambiamento di costituzione/soglie.

## Archi

- [[00-INDICE]]
