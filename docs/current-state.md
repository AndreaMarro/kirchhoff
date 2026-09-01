# Stato corrente

## Certificato

- P0 fino a P1-I sono certificati sul baseline
  `231c95355336bc983ec14ca5422baaf88f936244`.
- La CI del baseline e' verde nella run GitHub Actions 33437415864.

## Candidato P1-J

Il ramo `work/p1-j-gpt` introduce il contratto di osservazione della Request per
le trasformazioni certificate `serie` e `parallelo`: `identity`, `retarget` e
`blocked`, con lineage verificabile. Il motore delle trasformazioni resta
strutturale; non sono stati aggiunti replan automatici, CAS o dipendenze runtime.

P1-J non e' dichiarato certificato finche' i gate locali e la CI GitHub sullo SHA
finale non sono verdi. Il ramo canonico
`work/student-vertical-slice-0.1-phase1` non viene avanzato da questo checkpoint.

## Futuro

- Oracoli esterni per test e sviluppo, non per la verita' del prodotto.
- Estensione di Observation/ProtectedEntities oltre corrente e tensione.
- Punteggio e ricerca di strategie multi-passo, soltanto con un contratto dedicato.
- Adapter di percezione con validazione e conferma utente.
- Percorsi di prodotto AC e transitori.
