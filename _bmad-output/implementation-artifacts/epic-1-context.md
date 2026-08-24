# Epic 1 Context: La struttura di misura

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

L'epica costruisce l'apparato con cui il progetto misurerà la qualità del proprio motore per il
resto della sua vita: un insieme di circuiti a risposta nota che fa da oracolo, e un comando che
da quell'insieme produce VSR, SER, QPS e TTV più la ripartizione degli errori per tipo. Nessuna
riga di prodotto dipende da questa epica; ogni affermazione sulla qualità sì. È deliberatamente la
prima e la più autonoma: non richiede che il prodotto esista.

**Limite di copertura, dichiarato e accettato il 13 agosto 2026.** L'insieme di riferimento è
*strutturato* (generato da parametri), non fotografico. Misura la catena a valle dell'IR — solver,
Trasformazioni, Verifica — e **non** l'estrazione da immagine, dove nasce quasi tutto l'errore
silenzioso. SER resta la metrica bloccante ma è cieca proprio sul tratto più pericoloso. Ogni
rapporto prodotto dall'harness deve dichiarare questo limite, per iscritto, così che nessuna
lettura successiva scambi un SER parziale per un SER complessivo.

## Stories

- Story 1.1: Insieme di riferimento strutturato a risposta nota
- Story 1.2: Script di valutazione con metriche e matrice degli errori

## Requirements & Constraints

- **Quattro classi di dominio in scope**, e solo quelle: reti resistive in DC, transitori RL/RC/RLC,
  regime sinusoidale, trifase. I circuiti non lineari sono fuori scope per dodici mesi.
- **Ogni elemento dell'insieme porta tre cose**: l'IR del circuito, il risultato numerico corretto,
  e la sequenza di Trasformazioni di riferimento che vi conduce.
- **L'oracolo non si autocertifica.** Il risultato di un caso prodotto da un generatore va
  verificato per una via indipendente da quel generatore. Un oracolo che si dà ragione da solo non
  è un oracolo, è un test tautologico.
- **Split sviluppo/trattenuto, imposto dal codice.** La parte trattenuta vive separata e il flusso
  di sviluppo non la può leggere: il tentativo è un errore esplicito, non una convenzione. Leggerla
  durante lo sviluppo invalida ogni misura successiva.
- **Metriche riproducibili**: stessi input, stesse metriche, senza eccezioni.
- **Il rapporto dichiara la propria copertura parziale** (vedi Goal).
- **Aritmetica esatta.** L'oracolo usa razionali esatti, mai virgola mobile: la Verifica confronta
  due percorsi risolutivi entro tolleranza, e un oracolo che porta già errore di arrotondamento non
  permette di distinguere un bug del solver dal rumore numerico. Un residuo diverso da zero, dove
  l'aritmetica è esatta, è sempre un bug.
- **SER ha la precedenza** su QPS, TTV e VSR ogni volta che sono in conflitto. SER non deve mai
  salire.

## Technical Decisions

- **Ports-and-adapters con nucleo deterministico.** `domain/` non importa nulla del progetto fuori
  da `domain/` — in particolare né `adapters/` né `ports/`. Il controllo dei confini è
  automatizzato, non affidato alla disciplina di chi scrive.
- **L'IR è l'unico contratto fra stadi.** Nessuno stadio a valle dell'estrazione legge la sorgente
  originale.
- **Le Trasformazioni sono funzioni pure**: nessuna I/O, nessun orologio, nessuna casualità;
  catalogo chiuso. La casualità del generatore vive in `eval/`, non nel dominio, ed è sempre
  governata da un seme esplicito perché la generazione sia riproducibile.
- **L'harness gira sul codice di produzione attraverso gli stessi port**: nessun ramo `if testing`,
  nessuna scorciatoia riservata alla valutazione. Ciò che l'harness misura è ciò che l'utente
  riceve.
- **Nessun tipo associa una misura di rendimento a una persona.** Le metriche sono aggregate sul
  sistema, mai per soggetto identificato.
- **Nessuna soglia di copertura si abbassa** per far passare una storia: la copertura globale resta
  ≥ 95% e `domain/` resta al 100% su righe e rami.

## Cross-Story Dependencies

- Story 1.2 consuma ciò che Story 1.1 produce: senza insieme di riferimento non c'è nulla da
  misurare. 1.1 precede 1.2.
- Epic 2 non dipende da Epic 1 per funzionare, ma Story 2.11 (metriche del pipeline nell'harness)
  si innesta su ciò che questa epica costruisce: le classi di dominio coperte qui sono quelle su
  cui il motore verrà misurato.
- Nessuna dipendenza verso epiche successive.
