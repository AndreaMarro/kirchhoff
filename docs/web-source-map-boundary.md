# Mappe sorgente indicizzate nella toolchain web

Il lock seleziona `source-map-js` 1.2.2 per la dipendenza già richiesta da
PostCSS. La catena risolta è Vite 7.3.6 → PostCSS 8.5.28 → source-map-js;
il range del parent è `^1.2.1`. La risoluzione nativa cambia soltanto il
blocco di questo pacchetto nel lock. Manifest, override, workflow e
configurazione del prodotto restano quelli esistenti.

La release upstream corregge CVE-2026-93749: una mappa indicizzata piccola
poteva amplificare lavoro e memoria attraverso offset enormi o annidati.
Il consumer aggiornato rifiuta offset di linea/colonna negativi o
frazionari e linee oltre il limite upstream, compresa la somma degli offset
annidati. È un limite della libreria di build; le soglie e la definizione
di Verified del motore circuitale conservano la propria autorità.

## Guardia permanente

`web/tests/source-map-boundary.test.ts` risolve il modulo dalla dipendenza
reale di Vite attraverso PostCSS, anche in presenza di installazioni non
hoisted. Non aggiunge una dipendenza diretta al prodotto.

Sei casi verificano il rifiuto nel solo costruttore: linea oltre il limite,
linea negativa o frazionaria, colonna negativa o frazionaria e somma di due
offset annidati fuori limite. Questi input non vengono appiattiti o
serializzati e non tentano di esaurire risorse.

Due controlli sani con zero o tre righe di offset conservano posizione e
contenuto della sorgente. L'API pubblica SourceNode ricostruisce il codice,
verificato esattamente, e una mappa piccola; dopo serializzazione e
riapertura sono ricontrollati posizione e contenuto. Nessun budget, skip,
retry o expected dei test preesistenti viene modificato.

## Ambito e debiti distinti

L'evidenza riguarda il consumer risolto dalla toolchain e questi confini
concreti. La raggiungibilità di una mappa malevola dall'intero percorso CSS
del progetto richiede un'analisi distinta; `sourcemap: false` da solo non
la esclude. Il test non è un exploit end-to-end o una certificazione di
sicurezza di tutte le dipendenze.

Un primo controllo sano usava SourceMapGenerator.fromSourceMap con un
IndexedSourceMapConsumer che non espone sourceRoot. La libreria passava
undefined a util.relative e sollevava TypeError. Il test è stato corretto
prima di cambiare il lock, usando SourceNode senza mutare il consumer e
conservando gli assert di posizione, contenuto e riapertura. Il run iniziale
è conservato separatamente. Questa riparazione non corregge quel percorso
legacy; la sua rilevanza per il prodotto resta da triagiare nella voce
`WEB-DEPENDENCY-TRIAGE-2026-10-15`.

Gli advisory di Vitest, tinypool e mocker restano nelle rispettive
valutazioni aperte. Il presente aggiornamento non modifica il loro runner
o introduce un override di major. Kernel, schema, cataloghi didattici,
provenienza e contratti Ardesia restano fuori dal delta.

## Fonti primarie

- [Release 1.2.2](https://github.com/7rulnik/source-map-js/releases/tag/v1.2.2)
- [Correzione upstream e relativi test](https://github.com/7rulnik/source-map-js/pull/79)
- [API pubblica SourceNode](https://github.com/7rulnik/source-map-js#sourcenodefromstringwithsourcemapcode-sourcemapconsumer-relativepath)
- [Risoluzione mirata npm update](https://docs.npmjs.com/cli/v11/commands/npm-update/)
