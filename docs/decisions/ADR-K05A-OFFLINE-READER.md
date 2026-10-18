# K05a — Consultazione dei quaderni senza server

Stato: DRAFT, candidato locale. Nessuna approvazione docente o promozione di readiness.

Il quaderno v3 conserva già circuito, tentativi, fonte e scena della lavagna. La
riapertura richiedeva sempre il server: senza rete quei materiali non erano consultabili.

Il campo opzionale `savedLesson`, con schema interno `kirchhoff-saved-lesson.v1`,
conserva anche schema originale, passaggi, formule e risultato. Il digest SHA-256 lega
questa vista a circuito, metodo richiesto, risposta esatta e revisione del motore.
È un controllo di integrità, non una firma: chi modifica il file può ricalcolarlo.
La copia non contiene badge di verifica e ammette solo lo stato editoriale DRAFT.

Con il server, la riapertura ricalcola soluzione e diagnosi come prima. Senza rete o
con capability di calcolo assente, il lettore offre la copia in sola lettura. Non
produce nuovi giudizi, mostra i testi dei tentativi come da ricontrollare e mantiene
esportabile il quaderno. Gli errori HTTP del server restano errori; un HTTP 404 delle
capability, oppure la pagina HTML restituita dal fallback statico con HTTP 200,
indica l'installazione statica. Chiudere la copia invalida le richieste pendenti.

Il service worker conserva la pagina e gli asset compilati dopo il primo accesso
online in un browser con supporto service worker e contesto sicuro. I file pubblici
vengono conservati quando consultati. Le API e i quaderni non sono inseriti nella cache.
Versione e pulizia della cache sono circoscritte allo scope; la revisione include i
byte degli asset pubblici. Il lettore usa la stessa sanitizzazione SVG e MathML
della superficie studente. Il file rimane materiale non fidato.

Gli output API/MCP e ogni pagina PDF distinguono esplicitamente il testo DRAFT dai
controlli elettrici. La definizione di Verified e le soglie scientifiche non cambiano.

Limiti: i quaderni precedenti senza copia richiedono il server; la scena libera
resta esportabile ma non viene resa come lavagna nel lettore offline. Nessuna prova
su Pencil, iPad o Safari è implicita nelle verifiche Chromium desktop/mobile. Il
solo recupero offline non chiude FLOW_DONE, approvazione contenuti o migrazione governance.
