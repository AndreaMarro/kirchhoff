# Impedenza AC: oracolo indipendente congelato

Modello esecutore: `inherited/unknown`. Tutti i file sono fuori dai repository.
Nessun dato privato, pacchetto nuovo, servizio remoto o modifica al prodotto.
Questi circuiti sono costruiti per l'audit, non spacciati per esercizi pubblicati.

## Congelamento prima del confronto

`oracle.py freeze` crea una sola volta `cases.json` e `expected.json`. Rifiuta
di sovrascriverli. Il secondo contiene seed, data UTC, hash dei casi e del
codice dell'oracolo. `oracle.py check` controlla hash, rigenerazione dal seed e
risultati numerici. Il prodotto non viene importato da questo script.

Seed: **2026100311**. Dieci reti di base: due con formule manuali esatte e otto
maglie con sei nodi, nove bipoli passivi e sorgente di tensione flottante.
Sei varianti per rete: base, porta invertita, ordine dei componenti invertito,
ampiezze di picco, valori/fasi delle sorgenti modificati e polarità delle
sorgenti invertite. Sono **60 casi finiti richiesti**, più **11 degeneri**.

## Metodo e indipendenza

L'oracolo legge soltanto la sintassi limitata dei casi congelati. Spegne le
sorgenti indipendenti: apre le correnti e mantiene i vincoli di tensione a
zero, compresi quelli flottanti. Inietta 1 A da q verso p e calcola
`Z = (Vp−Vq)/1 A`. Il nodo q è il riferimento; il nome `0` non è speciale se
la porta scelta ha due morsetti differenti da `0`.

La matrice complessa è costruita direttamente e risolta con riduzione di
Gauss-Jordan e pivot massimo, usando esclusivamente la libreria standard.
Il controllo del rango distingue circuito aperto, risonanza e gradi di
libertà interni che non influenzano la tensione di porta. Ogni risultato
finito passa anche un controllo del residuo nelle equazioni originali.

Due controlli manuali con coppie di `Fraction`, privi di stamping e solver:

- **Ponte:** a tensione di porta unitaria, Cramer su due nodi interni;
  inversione della somma delle due correnti d'ingresso.
- **Sorgente flottante:** spegnere V(a,b) unisce a e b, quindi
  `Z = ((3 || j4) + (5 || −j6)) || 7`.

I risultati razionali esatti sono salvati accanto ai risultati numerici.
L'oracolo non importa `analyze_ac_port`, `solve_ac`, `independent_phasor`,
`Cyc12` o il parser di Kirchhoff.

## Runner del prodotto, da eseguire solo dopo via libera del root

Usare il Python già disponibile nella `.venv` di Kirchhoff:

```sh
python oracle.py check
python run_product.py --repo /percorso/kirchhoff --output /percorso/receipt.json
```

Il runner verifica il congelamento **prima** di importare `create_lesson`.
Legge la rappresentazione `complex_impedance` proposta, decodifica i quattro
coefficienti in modo autonomo e richiede `product_verified=false`.
Ogni rifiuto di un caso finito ordinario è un fallimento di capacità.
Per i degeneri un rifiuto esplicito e senza risposta numerica viene
registrato come limite conservativo; una risposta finita sbagliata fallisce.
Vincoli ideali ridondanti, sorgenti originali incompatibili e un'isola
flottante sono tenuti distinti, anche se l'impedenza soppressa è definita.

## Limiti della prova

L'oracolo numerico usa precisione IEEE 754 e una soglia di pivot dichiarata;
i valori congelati sono moderati. Non certifica casi arbitrariamente mal
condizionati, tutte le topologie possibili, le 21 famiglie, grafica o PDF.
Le due formule manuali esatte riducono il rischio di errore correlato ma
non costituiscono una dimostrazione universale. Dopo il primo confronto con
il prodotto, questa suite è una regressione conosciuta, non un nuovo holdout.

## Esito del primo confronto reale

`result.json` conserva l'esito grezzo del runner; `result.lessons.jsonl`
conserva le 68 risposte restituite, con hash dei byte di ciascuna riga.
I tre errori di parsing sono registrati separatamente nel risultato.
Il manifest di 103 file Python/config del package è rimasto invariato.

- **60/60 casi finiti ordinari corretti**, oltre ai due corti degeneri.
  Errore massimo scalato rispetto all'oracolo: **1,4407683523752932e−15**.
- Sei rifiuti conservativi espliciti: risonanza parallela, porta disconnessa,
  sola sorgente di corrente, vincoli di tensione ridondanti, sorgenti originali
  incompatibili, isola flottante irrilevante. Negli ultimi tre casi l'oracolo
  distingue un'impedenza definita dalla libertà interna; il prodotto resta
  conservativo e non fornisce un risultato.
- Tre input invalidi producono `ValueError` dalla libreria, come previsto dal
  parser: morsetto sconosciuto, morsetti uguali, resistore nullo. Il runner
  iniziale li marca `failed` perché assumeva un envelope `refusal` anche per
  gli errori di input. **Il risultato grezzo con exit 1 resta conservato**;
  gli attesi matematici non sono stati modificati. Il confine HTTP cattura
  queste eccezioni e prevede 422; qui il tentativo di chiamata reale è stato
  bloccato dal sandbox prima della connessione, quindi non è un test HTTP verde.

Successivamente il root ha eseguito le stesse tre richieste sul servizio reale
`127.0.0.1:43921`: **3/3 risposte HTTP 422**, ognuna con messaggio esplicito e
senza risultato numerico. La ricevuta è `transport_checks.json`, con hash dei
byte delle risposte. Questo chiude il controllo del confine HTTP; restano
conservati sia il tentativo locale bloccato sia l'esito grezzo del runner Python.

`additional_checks.json` contiene i controlli dichiaratamente successivi
all'apertura: **62/62** lezioni risolte hanno riferimento di porta coerente,
impedenza esatta in Q(j), campi rettangolari/AST coerenti, decimali corretti
a otto cifre significative e `product_verified=false`.

`transport_checks.py --port 8273 --output transport_checks.json` è pronto
per un processo autorizzato alla connessione locale; usa soltanto i tre
input invalidi già congelati e non sovrascrive ricevute esistenti.
