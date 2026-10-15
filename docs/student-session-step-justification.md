# La giustificazione della trasformazione

Il banco proof DC espone «Perché posso farlo?» nel dettaglio del passo
topologico. I quattro campi provengono dalla proprietà `VisualStep.giustificazione`
già esistente (UX-DR23): la presentazione riusa la composizione del passo,
senza avviare un'altra trasformazione, risoluzione, certificazione o emissione
SVG quando si apre il dettaglio.

| Campo di presentazione | Fonte canonica |
|---|---|
| `terminals` | `TransformResult.boundary.entities` |
| `preconditions` | `preconditions_of(certificate.operation)`, nell'ordine del Catalogo |
| `formula` | Resa letterale dell'`Equation` del risultato |
| `certificate` | Operazione, controlli e attestazioni del `Certificate` originale |

La proiezione conserva il collegamento fra esecuzione, risultato e indice
del passo. Le precondizioni sono dichiarazioni del Catalogo: non sono nuove
misure di residui, né una dimostrazione che l'elenco descriva ogni guardia
possibile. Il certificato include sempre `attestations`, anche quando è
vuoto. Vuoto significa che non sono dichiarate attestazioni di identità.

## Contratto di trasporto

L'estensione additiva di `student-session.v0.1` porta `StepView` da 13 a 14
chiavi, aggiungendo `justification`. Il produttore emette l'oggetto completo
sulle trasformazioni e `null` sui passi analitici. Il profilo analitico senza
trasformazioni, tutto `null`, è valido se valgono gli altri invarianti.

I nuovi reader browser e CLI accettano il legacy quando tutti i passi
omettono la chiave e ne conservano l'assenza. Se compare in un passo, deve
comparire in tutti. La rilevazione è indipendente da `derivation_ref`:
un catalogo con il collegamento Claim-passo può ancora essere legacy per
questa giustificazione. Una trasformazione `null`, un analitico con oggetto
o la presenza parziale sono incoerenti.

Il profilo delle riduzioni attualmente esposte richiede terminali nodo
non vuoti, unici e appartenenti ai preservati del passo. Non ridefinisce
il tipo generale `Boundary` e non prova che il sottoinsieme dichiarato sia
completo. I preservati possono comprendere componenti che non sono terminali.
Gli identificatori sono opachi e confrontati insieme al genere dell'entità.

Precondizioni e controlli sono sequenze non vuote di stringhe non bianche,
senza duplicati; non vengono ordinati, ripuliti o deduplicati per renderli
accettabili. Formula ed operazione del certificato coincidono rispettivamente
con equazione ed azione del passo. Ogni attestazione nomina un componente
preservato, con soggetto unico ed attributi cambiati non vuoti ed unici.
Il vocabolario strutturale è quello di `catalog.IDENTITY_ATTRIBUTES`:
`type`, `terminals`, `value`, `symbolic`, `phase_steps`, `control_nodes`.
Questi nomi non concedono una licenza di modifica: i controlli del dominio
rimangono l'autorità sulle licenze e sul confronto prima/dopo.

Il browser può ignorare chiavi future, ma il produttore e il pannello di
questa unità espongono soltanto i quattro campi. La parità dei nuovi campi
fra reader browser e CLI non rende equivalenti tutti i loro contratti:
il CLI operativo mantiene il proprio perimetro di catalogo proof DC.
La compatibilità con ogni consumer esterno, inclusa Ardesia, richiede una
prova distinta; l'estensione additiva da sola non la certifica.

## Interazione e limiti

Il dettaglio usa un disclosure HTML nativo, con i quattro campi nell'ordine
della fonte. Controlli ed attestazioni sono testo leggibile; nessuna nuova
spunta attribuisce un esito ad ogni precondizione. Le stringhe sono contenuto
inerte React e vanno a capo anche per identificatori lunghi. Il legacy mostra
che la giustificazione non è esposta; i passi analitici non ricevono un pannello
topologico fabbricato.

Il quaderno portabile conserva input, selezione e traccia, non una copia del
`StepView`: questa estensione non inventa una migrazione del quaderno.
La riapertura e il PDF restano oggetto delle prove di integrazione della build.

Questa unità copre una parte dell'ispezione H5/K4. Non completa residui numerici,
cross-check, terminal mapping generale, autenticazione H3 o le 21 famiglie.
Le guardie strutturali non autenticano dati ostili: rimuovere tutte le chiavi
nuove rende il payload indistinguibile dal legacy. `product_verified=false`,
definizione di Verified, soglie e costituzione restano invariati.
Gate, provenienza del catalogo e risultati effettivi appartengono alla receipt
della specifica build; questo documento non attesta un deploy o il completamento
delle prove ancora da eseguire.
