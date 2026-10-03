# Oracolo esterno per lezione Laplace — preregistrazione

Stato: **CHECKER E CRITERI CONGELATI; RISPOSTE DEL BACKEND NON ANCORA LETTE**.
Modello: `inherited/unknown`. `INDEX_SYNC_DEFERRED`.

Il corpus additivo contiene cinque reti con due condensatori, due induttori,
sette resistori e due sorgenti indipendenti. La rete contiene ponti tra nodi
interni: la riduzione per sole serie/parallelo non basta. Le varianti coprono
stati misti a 0−, inversione coerente di C2/L1 e dei relativi stati, scambio degli
stati, risposta libera e sorgenti impulsive di area esplicita.

Sono casi **additivi, creati dopo l'apertura del kernel**, congelati prima di
leggere la nuova lezione servita. Non sono gli 80 casi del precedente holdout.
Gli hash di `../laplace-independent/{oracle.py,cases.json,expected.json}` vengono
ricontrollati prima di ogni operazione e quei file non sono stati modificati.

## Criteri e indipendenza

Il vecchio oracolo usa un tableau di correnti di tutti i rami e tensioni di nodo,
Gauss–Jordan con numeri complessi della libreria standard. Il prodotto usa MNA e
funzioni razionali esatte. Il checker non importa moduli del prodotto.

Per ogni equazione in `steps[].math`, il checker interpreta l'AST senza `eval`,
lega i simboli alla soluzione indipendente e verifica i due membri in sei punti
complessi di s. I simboli di stato iniziale sono legati ai valori del **netlist
originale**, non a quelli restituiti dal backend. Il risultato richiesto è
confrontato negli stessi sei punti. Errore scalato ammesso: `3e-8`.

Vengono confrontati anche inventario e valori degli stati a 0−, unità V/A,
inventario delle sorgenti, gradino o impulso, ampiezza o area con unità esplicita,
trasformata, unità V*s/A*s e verso passivo della risposta. Le trasformate delle
sorgenti sono confrontate esattamente per moltiplicazione incrociata di polinomi
razionali, quindi `0/s` e `0/1` sono equivalenti. Ogni stato deve comparire nelle
equazioni mostrate. Un AST sconosciuto, un simbolo sconosciuto o metadata mancanti
producono un errore.

Dopo una risposta reale accettata si generano copie mutate: `+1` al membro destro
di un'equazione intermedia e inversione del segno di uno stato iniziale non nullo.
Nel caso impulsivo viene inoltre rimossa la dimensione temporale dall'unità
dell'area. Tutte devono essere respinte. Le copie non modificano il prodotto né
i dati originali. Il self-test del checker usa una soluzione RC analitica
esplicita, distinta da una risposta reale del backend.

## Freeze

- Criteri: `8b9faefe89e3ba2bce0f34a59eca87793c77d681935a2ec8d63847631bd63f3a`
- Checker: `ee5cf15f714428be0d5f93ffb5079bccdc7c373c5b6a9442b4e9eace2adb5827`
- Runner: `f132e337a85d4d2f61d9b14cdeb7a229077a283ad556dd73925a3cee83bec601`
- Corpus additivo: `12562faa8f6ee7972a0459fef1521e1444f2536ba6c6e370219706e1200c879f`
- Momento: `2026-10-03T09:41:05.245982+00:00`

Self-check: 390 residui fisici di ramo, metamorfismo di orientamento, sensibilità
allo scambio degli stati e mutazioni AST/metadata passati.

## Esecuzione dopo il freeze del backend

Dalla directory di questo documento, con il runtime Python già presente:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 run_product.py \
  --port 8273 \
  --repo /Users/andreamarro/MATJOURNEY/kirchhoff-takeover-20261002 \
  --output result.json
```

Il runner chiama soltanto `127.0.0.1`, `/api/solve`, metodo `auto`. Salva i byte
originali delle risposte in `result.responses.jsonl`, hash dei file sorgente
prima/dopo, errori ed esiti delle mutazioni. Rifiuta di sovrascrivere evidenze.
Si possono ricontrollare risposte archiviate con `--responses <file.jsonl>` al
posto di `--port`. Non cambia mai expected o criteri dopo una risposta.

## Limiti dichiarati

Campionare sei punti può falsificare una formula errata, ma non prova un'identità
simbolica per ogni s. Le equazioni con coefficienti numerici SI non tipizzati non
consentono una prova dimensionale completa: il controllo copre le unità esplicite
degli ingressi, delle equazioni e dell'uscita. Non viene effettuata inversione di
Laplace, confronto temporale, controllo SVG/PDF o prova di tutte le 21 famiglie.
Il risultato deve mantenere `product_verified=false` e nessuna promozione di
`canonical_proof` viene accettata.

Receipt esterno gestito secondo `persistent-capability-evolution`; aggiornamento
del registro e del receipt complessivo resta coordinato dal root, senza scritture
remote o modifiche ai gate del prodotto.
