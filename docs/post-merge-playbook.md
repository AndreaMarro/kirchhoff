# Playbook di integrazione e pubblicazione manuale

Aggiornamento 2026-10-15. La versione originale di questo documento è
conservata nel commit `bfa5e25c387ca8c36cebf0a64c4f708e3cbdfa6c`. Descriveva
un deploy al push e il ritiro del branch gh-pages: tali istruzioni sono
storiche e non sono la procedura attuale.

Il mandato corrente autorizza integrazioni ordinarie dopo i gate, ma non
un deploy di produzione, una release, la cancellazione di branch o modifiche
a protezioni e credenziali. Questo documento non è un'autorizzazione al deploy.

## 1. Candidato verificato prima del merge

Fissare commit, tree, parent, sorgenti e artifact effettivi. Conservare i
contributi parent e la provenienza; non equiparare un diff selettivo alla
chiusura di una PR intera. Sul candidato completo occorrono gate canonici,
CI del commit esatto, review avversaria e quorum formale della governance
adottata, oltre alle protezioni GitHub effettive. Una review Codex separata,
un badge CodeRabbit o il verde di una SHA precedente non sostituiscono il
secondo verdetto non-Codex richiesto per il merge. Il normale push del branch
candidato per ottenere CI rimane distinto dal merge in main.

Controlli read-only prima dell'integrazione:

```bash
gh pr view NUMERO --json state,isDraft,headRefOid,baseRefName,reviewDecision,statusCheckRollup
git ls-remote origin refs/heads/main refs/heads/gh-pages
```

Dopo un eventuale merge ordinario autorizzato dai gate, annotare la SHA reale
di main e verificarla. Non eseguire force-push, cancellazioni o bypass. Una
chiusura delle PR precedenti richiede prima prova del loro lavoro utile in main.

## 2. Stato corrente del canale Pages e confine deploy

Il workflow candidato `deploy-workbench.yml` è solo `workflow_dispatch`;
un push/merge non lo avvia. Il controllo GitHub del 2026-10-15 ha mostrato
Pages legacy con sorgente `gh-pages` alla radice, SHA nota
`f24e4a8b03b2de5c05368a4556a2454e8cf6196c`. Questo è un rilievo datato, non una
configurazione eterna. Prima di ogni pubblicazione va riletta la configurazione
corrente e ogni effetto noto dell'operazione proposta.

Un futuro deploy richiede una richiesta esplicita con target e commit concreti,
gate e artifact già pronti da esaminare. Il dispatch manuale non è stato eseguito
in questa integrazione. Non cambiare implicitamente la sorgente Pages o eliminare
gh-pages: resta un riferimento di recupero. Non promettere una pubblicazione
solo perché il workflow di test è verde.

## 3. Verifica contro un target esplicito

Da checkout atteso e pulito, costruire la build e conservarne SHA/manifest.
Questi comandi leggono il target; non lo pubblicano. Sostituire BASE_URL solo
con il target concreto da verificare:

```bash
npm run build --prefix web
node web/scripts/verify-artifacts.mjs BASE_URL web/dist
node web/scripts/smoke-public.mjs BASE_URL
```

Il verifier confronta byte interi di tutti i file della build locale attesa:
HTML esatto, asset diretti e lazy, worker PDF, lezioni, MCP, indice e tutte le
viste sessions. Non normalizza i nomi con hash. Gli indici devono corrispondere
ai corpi locali senza orfani; tutte le viste proof sono controllate per la
coerenza operativa minima. Non enumera file remoti extra non referenziati e non
prova la firma H3 o la correttezza matematica per sola uguaglianza dei byte.

Lo smoke richiede un URL esplicito, valida l'indice e legge ogni voce (oggi11,
non un numero hardcoded). Controlla ingresso/asset diretti, risposta/unità DC,
truth e diagnosi senza inventare risposte nei rifiuti. Confronta risposta e
diagnosi con quelle dichiarate nell’indice. Il profilo operativo accetta solo
chiusure DC e rifiuti onesti: ogni `failure`, anche col vero schema
`dove`/`messaggio`, è un guasto operativo e fa fallire il controllo. Questo
non modifica il contratto Failure del prodotto o il relativo messaggio UI. Non è la suite
browser o un nuovo verificatore del kernel. Nessuno dei due script esegue
richieste implicite al sito pubblico quando manca l'argomento.

## 4. Browser e ospite sul target verificato

```bash
KIRCHHOFF_PUBLIC_URL=BASE_URL npm run test:e2e --prefix web -- fumo-pubblico
KIRCHHOFF_WORKBENCH_URL=BASE_URL npm run test:e2e --prefix web -- site-host
```

Usare directory di output nuove per ogni run e conservare log/trace/immagini
prima di altri lanci. Leggere i risultati reali, inclusi skip e failure; i
conteggi di una versione precedente non sono attesi normativi. Il banco usa
`?view=proof`; l'ingresso predefinito rimane StudentApp. Verificare query/deep
link, tema, tastiera, viewport, trasporto e azioni dopo navigazione interna.
Il fullscreen nativo mantiene la cornice; link dedicato e fallback aprono il
link iniziale e devono dichiararlo. Il passo corrente si trasferisce con
«Copia link» del banco, senza ispezione del DOM figlio o nuovo IPC.

## 5. Collegamento dal sito e recupero

Il guscio è un dimostratore recuperato, non il sito personale già aggiornato.
Un collegamento reale è una futura operazione sul target specifico, subordinata
alla richiesta dell'utente e ai risultati sopra. Non dichiararlo pubblicato in
assenza di quella prova.

Se un artifact pubblico verificato risulta difettoso, interrompere la promozione,
conservare SHA, run e causa; preparare una correzione o un revert ordinario e
sottoporlo ai gate applicabili. Un revert/push non è un redeploy. Il ripristino
sull'hosting richiede un'operazione manuale autorizzata e la successiva verifica
degli artifact reali; non cancellare gh-pages come scorciatoia.

## Evidenza da conservare

Commit/tree/parent del candidato e di main, produttore dei JSON, closure e hash,
review effettive, protezioni osservate, CI checkout esatto distinto dal merge
sintetico, target/configurazione hosting datati, build/manifest e risultati di
verifier/smoke/browser/ospite. Segnalare ogni limite di preservazione senza
rigenerare un'immagine come se fosse una vecchia prova. Nessun lancio o pilot
umano si deduce da una sola suite verde.
