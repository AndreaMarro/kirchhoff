# Prossimo salto di prodotto — nota di decisione (non implementare)

Solo dopo gli obiettivi d'integrazione/lancio. Quattro candidati, cinque
criteri (1 = migliore, 4 = peggiore; il costo e' 1 = economico).

| Opzione | Valore studente | Costo ing. | Rischio verità semantica | Tempo a beta usabile | Valore marketing | Somma |
|---|---|---|---|---|---|---|
| A. solo integrazione sito | 2 | 1 | 1 | 1 | 2 | 7 |
| B. input parametrico controllato | 1 | 2 | 2 | 2 | 1 | 8 |
| C. input testo/netlist limitato | 3 | 3 | 3 | 3 | 3 | 15 |
| D. ingestione da foto | 4 | 4 | 4 | 4 | 4→1* | 17* |

\* D avrebbe il miglior marketing a breve («fotografa il circuito») ma e'
il peggiore su ogni altro asse: la classifica resta ultima.

## Lettura

- **A. solo integrazione sito** — E' questa sessione. Costo quasi zero,
  rischio nullo (nessuna inferenza nuova), subito usabile. Limite: lo
  studente consuma, non tocca: quattro esempi fissi saziano in fretta.
- **B. input parametrico controllato** — Lo studente cambia i valori (e
  solo i valori: stesse topologie DC, stesse famiglie) dentro sessioni
  ricalcolate dal kernel con aritmetica esatta. Valore studente massimo
  («e se R1 fosse doppia?»), rischio contenuto: il dominio resta chiuso,
  nessun parser, nessun occhio elettronico. E' il passo che conserva
  l'onesta' del rifiuto: fuori dai parametri supportati, stesso «non
  certificata».
- **C. input testo/netlist limitato** — Parser di un formato ristretto.
  Costo medio, ma ogni riga di parser e' una riga che puo' fraintendere un
  circuito: il difetto peggiore di questo prodotto e' la falsa accusa
  (dire sbagliato cio' che e' giusto, o certificare cio' che non lo e').
  Richiede grammatica chiusa, errori onesti, e un holdout di netlist
  adatte/inadatte prima di qualunque beta.
- **D. ingestione da foto** — Visione + interpretazione + soluzione: tre
  stadi incerti in cascata, costo altissimo, rischio semantico massimo
  (una foto letta male produce un numero sicuro e falso). Marketing
  immediato, fiducia distrutta al primo errore visibile. Ultima, a
  distanza.

## Raccomandazione

**B, poi sosta su A.** B e' l'unico salto che aumenta il valore senza
allargare il dominio elettrico: stessi solutori, stessi rifiuti, piu'
mani dello studente sopra. C solo con grammatica chiusa e suite di
rifiuti; D mai prima di una B consolidata e di una metrica di lettura
visiva con falsi positivi misurati.

Fuori ambito di questa sessione: nessuna implementazione di A–D qui.
