# Tensione da Ohm nel procedimento dello studente

Il passo strutturato `ohm-tensione` estende `student-trace.v1` senza cambiare
campi o introdurre un secondo IR. Dichiara precisamente:

`V(first) = I(first) × R(second)`

`first` è il resistore della tensione cercata; `second` è il resistore il cui
valore viene usato nel prodotto; `claimed_value` è la tensione scritta in volt.
Corrente e tensione usano i morsetti originali, dal primo al secondo nodo.
La corrente del prodotto è verificata sul circuito originale con i due percorsi
DC esatti esistenti. Se lo studente ha scritto una corrente, la si controlla
con un precedente passo `corrente`. Il testo libero non viene interpretato.

Per 12 V, R1=1000 ohm e R2=2000 ohm, I(R2)=1/250 A:

- `first=R2, second=R2, claimed_value=8`: valido fin qui;
- `first=R2, second=R1, claimed_value=4`: `reference`, prima dell'aritmetica;
- `first=R2, second=R2, claimed_value=4`: `algebra`.

Una sostituzione con resistenza di valore identico è un'uguaglianza valida,
anche con un altro identificatore: non si impone la sequenza del motore.
A corrente nulla, fattori diversi danno lo stesso prodotto e non provano un
errore di riferimento: il passo resta non valutabile, chiedendo chiarimento.
Riferimenti sconosciuti, modelli diversi, letture incerte e prove indipendenti
indisponibili restano non valutabili. Nessun nuovo stato `Verified` è concesso.

Il quaderno v2 conserva i campi del passo senza sostituire la diagnosi o una
risposta salvata al ricalcolo. I reader precedenti che non conoscono l'operazione
la rifiutano, senza convertirla silenziosamente in un altro passo.

Prove: `test_student_trace_ohm.py`, `session-bundle.test.ts` e
`student-ohm-live.spec.ts`. Il browser live richiede il server reale e la
variabile `KIRCHHOFF_LIVE_BASE_URL`, come le lane live esistenti.
