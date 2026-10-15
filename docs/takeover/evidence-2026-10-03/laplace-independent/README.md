# Laplace RLC: corpus e oracolo indipendenti

Modello: **inherited/unknown**. Seed: **2026100317**.
Questa unità prepara prove eseguibili fuori dai repository. Nessuna sorgente
privata, dipendenza nuova o implementazione Laplace di Kirchhoff è stata letta
prima del congelamento. È stata concordata soltanto l'ABI matematica.

## Corpus congelato

**80 casi**, di cui **70 richiesti risolvibili**, valutati in sei punti complessi
con parte reale positiva. I dati astratti separano topologia, trasformate delle
sorgenti e condizioni iniziali. Non dipendono da un parser ancora da realizzare.

- RC e RL: risposta forzata e libera, condizioni iniziali positive e negative.
- RLC: smorzamento inferiore, uguale e superiore al critico; LC senza perdite.
- Quattro reti a ponte/maglie, con controlli su ogni corrente di ramo e su ogni
  tensione di ramo/nodo. Una sorgente ideale con resistenza d'ingresso evita di
  imporre inconsapevolmente la tensione iniziale di un condensatore.
- Sorgenti con trasformate esplicite: gradino, impulso, esponenziale e sinusoide.
- Versi invertiti con IC e trasformate coerentemente negati; riordino; valori
  topologici delle sorgenti alterati senza cambiare la trasformata; tempo scalato;
  risposta libera più risposta forzata.
- Due risposte impulsive valide: induttore aperto con corrente iniziale e
  condensatore forzato da una sorgente ideale con tensione iniziale differente.
- Dieci casi non risolvibili o invalidi: vincoli ideali ridondanti/incompatibili,
  isola flottante, valori non ammessi, mappe IC/sorgenti incomplete, denominatore
  nullo e identificatori duplicati. Una verifica separata riguarda i poli LC.

Il congelamento ha verificato **336 relazioni metamorfìche**. Il massimo residuo
del tableau è **7,105427357601002e−15**. Cinque alterazioni intenzionali sono
rilevate: segno dell'IC capacitiva, segno dell'IC induttiva, IC omesse, fattore s
in più sulle IC, gradino interpretato come impulso. Sono mutazioni dell'oracolo
per misurarne la sensibilità, non mutazioni del codice produttivo.

## Convenzioni e metodo indipendente

Le condizioni sono a **t=0−**. Per un ramo p→q:

```
v = Vp − Vq
i > 0 da p verso q
R: v − R i = 0
L: v − s L i = −L i(0−)
C: s C v − i = C v(0−)
```

L'oracolo costruisce un **tableau di tensioni nodali e correnti di tutti i rami**.
Non usa la MNA, la classe RationalFunction o altri risolutori di Kirchhoff.
La riduzione di Gauss-Jordan usa `complex` della libreria standard e controlla
il residuo nelle equazioni originali. Le formule RC/RL/RLC sono derivate
direttamente dalle leggi di ramo e salvate con coefficienti `Fraction`.

Esempio serie RLC, sorgente A/s, corrente iniziale i₀ e tensione iniziale v₀:

```
I(s) = [i₀ s + (A−v₀)/L] / [s² + (R/L)s + 1/(LC)]
```

Il riferimento numerico prova tutti gli osservabili; le formule manuali
consentono inoltre un confronto razionale esatto mediante prodotti incrociati
di polinomi, indipendente dalla cancellazione dei fattori nel prodotto.

## File e avvio

`cases.json` contiene i casi; `expected.json` contiene risultati, hash e
ricevuta del congelamento. `oracle.py freeze` rifiuta di sovrascriverli.

```sh
python3 oracle.py check
```

`run_product.py` è pronto per un adattatore sottile, dopo il via libera del root:

```sh
python run_product.py --repo /percorso/kirchhoff \
  --staging-dir /percorso/laplace-staging \
  --adapter-file /percorso/adapter.py --output result.json
```

L'adattatore deve esporre `solve_case(case)` e restituire:

```
{outcome: "solved", observations: {
  "V(a)": RF, "V[C1]": RF, "I[C1]": RF, ...
}}
```

oppure `{outcome: "refusal", cause: ...}`. `RF` è
`{numerator: [stringhe Fraction], denominator: [stringhe Fraction]}` in ordine
**crescente** di potenza. Le frazioni devono essere ridotte, il denominatore
monico e lo zero rappresentato come 0/1. L'adattatore deve proiettare gli
osservabili calcolati dal kernel, senza ricostruire risultati mancanti.

Il runner controlla hash prima dell'import del prodotto, tutti gli osservabili,
identità analitiche, forma canonica e poli; conserva risposte e hash sorgente.
Gli errori tipizzati dei casi invalidi sono distinti dai fallimenti numerici.
Controlla anche tre mutazioni delle risposte, dichiarandone il limite.

## Limiti

I campioni numerici non dimostrano identità razionali universali: il confronto
esatto è limitato alle formule analitiche presenti. Non è una certificazione
delle 21 famiglie, dell'inversione nel tempo, di una lezione, del PDF o della UI.
Non viene attribuito `VERIFIED` al prodotto. Dopo il primo confronto questa
suite diventa una regressione conosciuta; gli attesi restano immutabili.

## Primo confronto autorizzato sul kernel congelato

**80/80 esiti coerenti, exit 0:** 70 risposte risolte, tre rifiuti di sistemi
singolari e sette errori tipizzati per input invalidi. Tutti gli osservabili
sono confrontati nei **420 campioni risolti**; errore massimo scalato
**1,7763568394002505e−15**. Passano anche **104 identità analitiche esatte**,
cinque controlli dei poli LC e la forma canonica delle frazioni.

`adapter.py` converte soltanto tipi e osservabili. Le risposte complete, inclusa
la matrice del kernel, sono in `result.responses.jsonl`; risultati, errori e
hash sono in `result.json`. I tre hash del corpus/oracolo/attesi sono invariati.
I sorgenti del package e dello staging sono invariati durante il confronto.

- SHA-256 `laplace.py`: `f1fe3a43c8e778e690bb49200782d64f9dbf4ea09167672db76cc96db79c6c5e`.
- SHA-256 `laplace_rational.py`: `e9ebdb4a9b31a8975be58877514db957a34454c62fca97ae2d4b6d623729ea6f`.
- SHA-256 delle risposte JSONL: `55b82d6d67c37d1dc0ea294085d716c791e97c47665a65a363f71d4888a2ea4f`.

Tre perturbazioni delle risposte sono respinte. Nel raw, l'etichetta
`missing_initial_contribution` descrive in realtà l'aggiunta di 1 al numeratore
della corrente: va letta come perturbazione di coefficiente. L'omissione effettiva
delle IC è coperta separatamente dalla mutazione `omit_initial` dell'oracolo,
eseguita prima del congelamento. Non viene attribuita a queste prove una
mutazione del codice produttivo.

Le maglie di questo corpus hanno al massimo un condensatore e un induttore.
Il confronto non estende automaticamente la copertura a reti di ordine maggiore.
