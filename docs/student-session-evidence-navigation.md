# Dal Claim al passo che produce la derivazione

Il banco proof DC espone il collegamento già presente nella `ProofSession`:
gli `evidence_ids` del Claim finale corrispondono, nello stesso ordine, ai
`derivation_after` dei passi analitici. La proiezione copia questi riferimenti;
non risolve di nuovo il circuito e non ricava un indice dal nome `D1`.

## Estensione additiva del contratto

`student-session.v0.1` mantiene le proprie chiavi di sessione. `StepView` passa
da 12 a 13 chiavi con l'aggiunta di `derivation_ref`:

| Passo del nuovo produttore | `derivation_ref` |
|---|---|
| `transform` | `null` |
| `analytical` | Il vero `AnalyticalProofStep.derivation_after` |

Gli `evidence_refs` esistenti continuano a riferire gli stati IR e hanno le
proprie guardie. Non sono sostituiti o reinterpretati. Il nuovo produttore
espone sempre il campo e impone riferimenti analitici non vuoti, unici e in
corrispondenza esatta con gli `evidence_ids` del Claim. L'ordine dei passi
deve corrispondere agli indici, come nel consumer web.

Il nuovo parser web e il controllo operativo CLI leggono anche le viste
legacy quando **tutti** i passi omettono il campo. Mantengono l'assenza:
non aggiungono `null` e non inventano collegamenti. Appena la chiave compare
in un passo, il profilo deve essere completo su tutti: trasformazioni `null`,
analitici con stringhe uniche e sequenza uguale a quella del Claim.
Un profilo tutto `null`, parziale, duplicato, pendente o riordinato è respinto.
Gli ID sono opachi; gli spazi non vengono rimossi per far coincidere due ID.
Il CLI richiede passi non vuoti anche per un legacy sano.

La versione resta 0.1 perché l'aggiunta è leggibile dai consumer precedenti,
che ignorano le chiavi extra, e il nuovo consumer mantiene il percorso legacy.
Non è un censimento di ogni consumer esterno. Rimuovere tutti i campi nuovi
rende il payload indistinguibile dal legacy: la UI toglie i link e dichiara
il limite. Questo non autentica un produttore ostile e non implementa H3.

## Navigazione e focus

«Perché fidarsi» mostra gli ID delle evidenze. Con il mapping esplicito,
ogni pulsante indica ID, azione e numero del passo; attivarlo seleziona quel
passo e porta il focus al suo dettaglio. Funziona anche se il passo è già
corrente. Il cambio di sessione annulla il focus richiesto dal contesto
precedente, anche se la nuova vista riusa lo stesso `session_id`.

La navigazione usa il callback del banco esistente. `App` normalizza il
fotogramma disponibile; non si sovrappongono due aggiornamenti di selezione.
Le viste legacy mostrano gli ID e dichiarano che il collegamento non è
esposto, senza pulsanti dedotti dalla posizione. Rifiuto e guasto restano
superfici prive di risposta e di evidenza positiva.

La scala con tre riduzioni è un esempio discriminante: `D1` produce il
passo con indice 3, `D2` quello con indice 4. Questi due atti non hanno
equazioni; il ponte nodale espone separatamente i passi `write_kcl` con
le equazioni proiettate dal kernel.

## Perimetro e prove

Questo collegamento affronta il debito di navigazione H5/K4; non completa
l'ispezione di ogni residuo, cross-check, terminal mapping o provenienza.
`Verified`, soglie, solver, costituzione e `product_verified=false` restano
invariati. Nessuna nuova famiglia matematica viene dichiarata supportata.

I test confrontano la proiezione col dominio reale, respingono mapping
incoerenti in Python/web/CLI e mantengono il legacy sano. I browser coprono
ID canonici e opachi, KCL, Enter/Space/click, passo già corrente e cambio
di contesto. Un harness di test monta il vero componente con viste del
produttore: non è un ingresso o un asset pubblico del prodotto.
I risultati, la fonte committed del generatore e i gate del candidato finale
sono registrati nella receipt dell'unità; questo documento descrive il
contratto e non certifica da solo una build o una distribuzione.
