---
storia: giustificazione-passo-in-review
istante: 20261015T173935Z
sha: fec4fff5fd347e899501010185edb4b0d2393175
ramo: codex/k4-boundary-inspection-20261015
esito: fallito
tipo: receipt-di-giro
---

# Giro 20261015T173935Z — giustificazione-passo-in-review

> Questa nota registra MISURE, non giudizi. Un giudizio di modello che
> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha
> verificato.

## Misure agli oracoli

| grandezza | valore |
|---|---|
| `test_passati` | 2594 Python;355 unit web;12 browser mirati;6 viewport;2 journey reali;179 default per run |
| `test_falliti` | 1 timeout in ciascuno dei due default completi |
| `copertura` | 97.39366138448707% (soglia95% invariata) |
| `recinti` | PASS |
| `dominio` | 100% |
| `verde` | False |

## Esito: fallito

## Revisioni

- Review sorgente separata APPROVE_SOURCE_ONLY_LOCAL_COMMIT, SHA256156fedb1f358f5f583f21e6cbf13ee6d0959ef67462d0d36a97b16680a7de438; cataloghi PASS_CSRC_PIN_AND_CATALOG_REVIEW_ONLY, SHA256b0c835ac52f9652790693c02384c2de16edc1f19b58796169262cfdceb113076. Non approvazione finale.
- Review visuale/gate conclusi SHA256e5b83504f0b9cf91a56dd4c6f7af13c47c3ea1e75889a75ed90b3b7eaf4bb272 e continuita SHA2567be12995a6fe4251288b920dcf1f2f17fc14a6eae0ee6a86a5fb101182e98b6a: PASS delimitati. Candidato esatto, CI e quorum finale ancora PENDING.

## Archi

- [[00-INDICE]]


## Requisito, implementazione e confine

UX-DR23/FR13/FR49, porzione H5/K4: «Perché posso farlo?» apre i quattro dati
gia presenti in `VisualStep.giustificazione`: terminali del boundary,
precondizioni ordinate del Catalogo, formula originaria e certificato
completo (operazione, controlli, attestazioni). Il DTO riusa la stessa
esecuzione di trasformazione: nessuna seconda composizione o solve per
aprire il pannello. Formula e azione restano legate al passo corrente.

Trasporto additivo `student-session.v0.1`: produttore nuovo sempre con chiave
`justification`, oggetto sui trasformativi e null sugli analitici. Legacy
con chiave assente su tutti i passi accettato e dichiarato; presenza parziale
o struttura incoerente respinta. Le sei proprieta delle attestazioni sono
quelle dell'autorita `IDENTITY_ATTRIBUTES`, senza copiare licenze per
operazione. Il boundary non equivale all'intero insieme preservato.

L'interfaccia usa details/summary nativo e i token esistenti, testo opaco
inerte e wrap. Nessuna nuova definizione di Verified o autenticazione della
provenienza. Il caso sintetico V1/value,type esercita il trasporto, non
una nuova licenza canonica. Residui numerici, cross-check completo e
terminal mapping restano fuori da questa porzione; H3 rimane aperto.

## Identita di produzione e rigenerazione

Commit sorgente Csrc `fec4fff5fd347e899501010185edb4b0d2393175`, tree
`1a6af9440a850f376a30fa33dd2ce387aed5d6db`, parent
`0d643d3b7bab291d80a9b8c93cf7dbefd235ae9a`. Dodici file sorgente/test/doc.
Il successivo candidato con cataloghi e questa receipt e ancora PENDING:
Csrc non e retroattivamente l'artifact commit o un candidato CI verde.

CLI canonici eseguiti da Csrc pulito: closure proof112 file, Student113,
insieme tracked e filesystem108 moduli Python coincidenti; nessun override
source_sha e nessun ripristino temporaneo per simulare un checkout pulito.
Solo dopo i confronti sono stati copiati gli output proof privati.
Undici viste proof (nove closed, due refusal), dieci trasformazioni:
sette serie e tre parallelo. Indice proof invariato. Tolta solo la nuova
giustificazione e normalizzato source_sha, tutti i campi precedenti
coincidono, inclusi risposta e SVG.

Il fingerprint globale del pacchetto cambia legittimamente in
`c19394eab476400f2a4a9bb4e8fa92c87390ff0a63fc741f0d577e024e58a424`. Diciotto lesson JSON differiscono solo per source_sha
e lesson_build; diciotto PDF sono stati confrontati con il produttore
canonico prima/dopo e dopo normalizzazione dei due metadati. Indice Student
invariato. I due audit pubblici in `docs/evidence/2026-10-15-k4-*.json`
registrano i file produttori e generati con percorsi relativi e digest.
Non e un cambiamento del dominio matematico o dei percorsi delle lezioni.

## Oracoli conclusi e qualificazione

Controesempio iniziale tre FAIL per campo justification mancante, poi stessi
tre PASS. Guardie runtime:40 FAIL piu un sano sullo stesso test, poi41 PASS.
Wire originale:91 FAIL e9 sani, poi gli stessi100 PASS; estensione122 casi
piu due controlli Python del vocabolario. UI SSR:5 FAIL e1 analitico sano,
poi stessi6 PASS. Il primo file SSR non raccolto (zero testcase) e l'errore
XML del collector host sono conservati separatamente: non sono RED di
prodotto. Il modulo presentazione completo passa136 casi, compreso il
binding agli oggetti canonici e lo scambio di due giustificazioni di serie.

Gate non browser su sorgenti e cataloghi correnti:355 unit web,2594 Python,
zero fail/error/skip, typecheck/build standalone+MCP, setup canonico reference,
BMAD con loop, boundaries e diff-check exit0. Coverage97.39366138448707%,
dominio100%. Nessun contenuto holdout letto; readiness CONCERNS invariata.

HTTP923 corpi MATCH/zero DIFF. Mirati12 PASS e viewport6 PASS, worker1,
retry0, budget invariati. Tab reale raggiunge il summary; dopo scroll
misurati142 elementi,290 rettangoli e194 gruppi di riga nei sei stati.
Le full-page conservate mostrano una banda coperta dal footer: i dodici
viewport separati e le misure dimostrano raggiungibilita delle righe
esaminate, non simultanea visibilita totale, WCAG, touch o fix scroll349.

## Due browser completi: FAIL preservati

Entrambi raccolgono tutti234 casi, un risultato per caso/retry0:
179 PASS,54 skip opzionali annotati,1 timedOut,zero noResult/flaky.
Identita, expectedStatus, annotazioni e tutti923 hash dist coincidono.

Primo risultato SHA256`4d701ca9f8d70a0356bb5d12d14ddd4c28aa7bc897aa6b6ba9e3b4a28a77af04`: timeout mobile
`validation.spec.ts:35`, verificatore assente. Create page17.666883s;
il rifiuto atteso e raggiunto, ma gli assert terminano oltre deadline30s.

Conferma SHA256`0d8c9df29e160ee49954212be6f280c3ab6d55f311fb85a43706e00045808998`: timeout desktop
`integrazione.spec.ts:67`, cornice stretta. Create page25.540075s;
il percorso raggiunge la UI e prosegue durante cleanup, oltre30s.
Nessun assertion mismatch separato o causa host specifica dimostrati.
Nessun PASS retrodatato dai risultati tardivi e nessuna somma dei casi
verdi dei due run per fingere una suite verde. Nessun terzo run locale.
Preview/browser/helper propri conclusi, porta4177 chiusa nei due record.

Stato dell'unita: **IN_REVIEW**, gate locale completo non soddisfatto.
Eventuale commit/push di una PR draft ha solo scopo di verifica diagnostica
con la CI test-only gia configurata su runner differente. Non e un merge,
un gate AI passato, una deroga a budget/CI o una dichiarazione di prodotto
pronto. Restano necessarie review del candidato esatto, CI e disposizione
tecnica dei timeout prima di qualsiasi integrazione.

## Continuita reale e compatibilita delimitata

Due journey reali desktop/mobile, budget120s invariato, da una copia esatta
del quaderno main22:677 byte SHA256
`7e93bc0f70c01848a7f83b68a66b163e502c1a4c0b32ddcfe661f2cc0e2bba29`.
Quattro solve reali espongono Csrc/nuovo lesson_build e1/250 A, con
product_verified false. Sei diagnosi: illeggibile step1, primo errore step2,
poi stesso errore dopo riapertura in nuovo contesto. Avviso cambio motore,
confronto prima/dopo via tastiera, PDF e salvataggio/riapertura osservati.
Il dato ripristina clear; unreadable e selezionato esplicitamente prima
della diagnosi incerta e poi si torna a clear, senza mutare l'input.

PDF desktop/mobile identici49775 byte/sei pagine, SHA256
`c8a6d67a82281859f24a01bfcf9cba9dc10c4851c99f28f75cd3655c69362ba1`.
Rispetto al PDF precedente, normalizzando solo source metadata, full build
metadata e sei footer di revisione, i byte coincidono. Il primo confronto
source-only del collector ometteva il footer/build cambiato e resta
conservato come aspettativa errata dell'harness, non difetto corretto nel PDF.
Quaderni nuovi identici677 byte: solo engineRevision cambia nei byte.
L'originale piu vecchio682 byte non era leggibile entro10s: nessuna
equivalenza o riapertura di quel diverso input e dichiarata.

Due reader Kirchhoff del precedente main e2c0 su11 viste old/new:
44 accettazioni, vecchi campi invariati dopo normalizzazione dichiarata.
Sono due reader Kirchhoff, **non Ardesia**. Ardesia rimane soltanto locale;
identita corrente e compatibilita K4 non attestate dopo i timeout di lettura.
Nessuna modifica/risoluzione di credenziali o pubblicazione Ardesia.

## Review e destinazioni residue

Due Codex separati ammessi dall'owner soltanto per questa esecuzione;
nessuna modifica permanente della governance. Il writer conta una volta.
Le review elencate sono limitate ai rispettivi gate: candidato finale,
quorum exact-SHA e CI sono PENDING in questa receipt. Non ci sono nuovi
P0/P1 concreti nei rapporti delimitati; questa non e garanzia universale.

P2 gate locale: BLOCK per promozione corrente, destinazione diagnosi CI
exactcandidate e review finale della stessa unita. P3 ritardi/affidabilita:
DEFERRED verso issue20, con trace e contatori reali. P2 K4 completo verso
prossima unita H5/K4; autenticita verso H3. Interoperabilita Ardesia
NOT_CHECKED_CURRENT verso verifica locale quando nuovamente disponibile.
Source-map resta differito sul suo ramo, non e incluso in questo candidato;
advisory restanti verso WEB-DEPENDENCY-TRIAGE-2026-10-15. Scroll349,
21famiglie, design/accessibilita globali e pilot mantengono le destinazioni
precedenti. Nessun deploy, release, nuova credenziale o spesa autorizzata.
