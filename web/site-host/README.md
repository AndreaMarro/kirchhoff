# Guscio dimostrativo del catalogo Proof Workbench

Aggiornamento 2026-10-15. Questo guscio statico mostra il catalogo proof DC,
non sostituisce l'ingresso StudentApp o la direzione UX di prodotto. Il
contratto rimane URL-only: iframe indipendente, nessun solver nel sito,
nessuna lettura del DOM figlio e nessun nuovo protocollo di sincronizzazione.
Il codice originale e le misure precedenti restano nel parent bfa.

## Avvio locale esplicito

Dalla radice del repository:

```bash
npm run build --prefix web
npm run preview --prefix web -- --port 4173 --strictPort
python3 -m http.server 4183 --directory web/site-host
```

Aprire il guscio con un URL del banco completo e codificato, per esempio:

`http://127.0.0.1:4183/?workbench=http%3A%2F%2F127.0.0.1%3A4173%2F%3Fview%3Dproof%23exercise%3Dpartitore-d1%26step%3D-1%26frame%3Dbefore`

Il parametro workbench accetta URL assoluti http(s). Il guscio imposta
`view=proof` con URL API conservando gli altri parametri e il deep link;
un input illeggibile usa il canonico. Senza parametro usa
`https://andreamarro.github.io/kirchhoff/?view=proof`, con esempio iniziale.
Il canonico è un indirizzo configurato, non prova che questa build sia deployata.

## Azioni e continuità effettiva

Il fullscreen nativo mantiene lo stesso iframe e il passo corrente. Il link
«Apri il link iniziale in una pagina» e l'alternativa quando fullscreen manca,
solleva sincronicamente o rigetta la Promise aprono l'URL iniziale configurato.
La nota in pagina lo dichiara; non promettono di conoscere l'hash corrente del
figlio. Per trasferire il passo corrente usare «Copia link» nel banco. L'apertura
dell'alternativa è soggetta ai normali controlli del browser sulle nuove finestre;
il link iniziale rimane disponibile come azione esplicita.

## Ambito e misure

Undici esempi proof: nove chiusure e due rifiuti; non undici famiglie StudentApp.
Nessun input libero o lezione AC/Laplace in questo dimostratore statico. Non è
una dichiarazione generale sui metodi del server o sulle altre superfici.

Le dimensioni 1168×720desktop,780×700tablet e360pxmobile del testo originario
sono misure storiche della build bfa: non una nuova attestazione dopo il recupero.
Nel guscio fino a 480px l’intestazione scorre con la pagina: la barra
superiore del banco deve restare azionabile dopo lo scroll alla cornice.
Questa correzione non elimina il possibile scroll iniziale del contenuto.
I test `site-host.spec.ts` misurano nuovamente trabocco/bersagli/tastiera/trasporto,
query e continuità delle azioni sulla build finale. Registrare SHA, viewport,
risultati e immagini effettivi nella ricevuta del nuovo run; finché mancanti
restano PENDING. Nessuna misura automatica equivale a un pilot umano o al rispetto
integrale del design autorevole. H5/K4 resta aperto.

## File e uso sul target

`index.html` e `host.css` sono il guscio; `copy-it.md` contiene la copia del
solo catalogo statico. `site-host.spec.ts` prova il guscio con la build reale;
`fumo-pubblico.spec.ts` richiede il target HTTP esplicito e apre proof. Seguire
`docs/post-merge-playbook.md` aggiornato per distinguere verifica, merge e deploy.
