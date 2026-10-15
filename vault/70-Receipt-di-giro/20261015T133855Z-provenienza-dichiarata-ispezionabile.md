---
storia: provenienza-dichiarata-ispezionabile
istante: 20261015T133855Z
sha: 4fa3912b9635f8f522b529b264ab3bcf1316870b
ramo: codex/provenance-inspection-20261015
esito: verde-non-promosso
tipo: receipt-di-giro
---

# Giro 20261015T133855Z — provenienza-dichiarata-ispezionabile

> Questa nota registra MISURE, non giudizi. Un giudizio di modello che
> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha
> verificato.

## Misure agli oracoli

| grandezza | valore |
|---|---|
| `test_passati` | 2544 |
| `test_falliti` | 0 |
| `copertura` | 97.37% (soglia 95%) |
| `recinti` | PASS |
| `dominio` | 100% |
| `verde` | True |

## Esito: verde-non-promosso

## Revisioni

- Codex primario writer contato una volta: APPROVE_TESTED_UNIT_CONTENT_ONLY, SHA256 dd0c292928537d91c98bfac89c79ac333e85238372c20562d0675e980fbac1d2; candidato esatto e CI ancora PENDING.
- Codex avversario in contesto distinto: APPROVE_TESTED_SOURCE_CONTENT_ONLY, SHA256 0848e28c958bd7d10e8683cf689de666278fbdb2a5f0350bcae8315ea532a5f7; ledger/candidato/CI/main ancora IN_REVIEW.

## Archi

- [[00-INDICE]]

## Requisito e confine

Il pannello «Perché fidarsi» espone produttore, revisione sorgente completa
e contesto dichiarati. Due revisioni di quaranta caratteri con lo stesso
prefisso di dodici restano distinguibili. Stringhe non vuote conservate,
null e blank espliciti, HTML come testo, nessun link inventato o spunta di
autenticazione sui metadati. Navigazione Claim e token esistenti conservati.
La revisione sorgente dichiarata del catalogo resta
`8a580e9658098b6f91fb16febe5396502c46c268`, distinta dall'HEAD UI.

Nessuna modifica a Python, schema, parser, kernel, cataloghi, definizione di
Verified, workflow o dipendenze. Il parent documentale `4fa3912` conserva
la receipt della verifica main H5 `1b2ac78`, già revisionata separatamente.

## Misure delimitate

- Otto casi browser RED sull'interfaccia originale, ciascuno fermo al primo
  assert nuovo; stessa spec poi otto PASS desktop/mobile, tastiera Enter/Space
  e reload, SHA con prefisso comune, stringhe opache, null e blank.
- Gate locale completo dopo setup canonico: 2544 Python PASS, zero fail/skip,
  431.12 s; coverage 97.37%, domain 100%, confini PASS; 227 unit web/13 suite,
  tipi e build standalone/MCP exit 0.
- HTTP canonico: 923 corpi MATCH, zero DIFF. Mirati otto PASS; default
  222 risultati singoli: 168 PASS e 54 SKIP opt-in espliciti preesistenti,
  zero fail/flaky. Gli otto nuovi sono inclusi nei 168, non casi aggiuntivi.
- Probe viewport separato: due PASS, quattro schermate lette, tre valori e
  disclosure dopo scroll; 14 centri di riga distinti colpiscono il target
  nel viewport. Misura sul catalogo canonico, non attestazione globale WCAG,
  geometria di ogni input, hardware o utenti pilota.

Budget, assertion, retry zero e soglie del repository invariati. I 112 file
canonici della closure e i quattro file della patch sono stati ricontrollati
dal reviewer distinto; il lock è rimasto identico al parent.

## Fallimenti conservati

Il primo default Documents resta fallito/incompleto: otto PASS, cinque
timeout, due skip espliciti, un interrotto e 206 senza risultato; i 209
skipped del riepilogo non sono 209 profili opzionali. Causa originaria dei
timeout browser non dimostrata. Un pytest precedente fu interrotto su una
lettura di sorgente dataless: nessun esito completo gli è attribuito.
Il recupero esatto di un solo blob, con placeholder originale conservato,
e il checkout fisico separato sono prove di pin, non test verdi.

Il primo pytest fisico resta 12 FAIL/2532 PASS/97.09%: dieci asset MCP
assenti e due split dev assente. Il driver privato aveva omesso i due
preparativi documentati di test.yml. Il secondo run li esegue prima dei
test e passa integralmente; nessun expected o controllo è stato indebolito.
Nessun contenuto holdout è stato ispezionato per sviluppo o diagnosi.

Il primo probe viewport resta due FAIL a page.goto per connessione rifiutata,
prima di ogni assert di lettura. La preview non risultava più presente;
il meccanismo preciso di terminazione non è provato. Preview dedicata e
pin dei byte serviti, stesso probe e nuove destinazioni: due PASS.
Il primo pin del riavvio controllava HTML/JSON ma non gli URL relativi dei
chunk; un addendum distinto verifica entrambi gli entry JS/CSS. Non è una
seconda verifica di tutti i 923 corpi.

## Review, stato e debito

Il reviewer distinto ha tentato undici profili reali parser/React/callback:
la base rende identico il markup delle revisioni con prefisso comune,
la patch le distingue. Questi sono controlli del consumer, non certificati
di nuovi circuiti o collisioni fra commit reali. P0/P1 nuovi: nessuno
individuato nel perimetro; nessun nuovo finding di codice P2/P3.

Rimangono P2 differiti: autenticità H3; report completo H5/K4 di residui,
cross-check e terminal mapping; dipendenze web esistenti verso
`WEB-DEPENDENCY-TRIAGE-2026-10-15`. P3 preesistenti verso issue #20 e unità
isolata host/scroll349. Le 21 famiglie, design/accessibilità globali e pilot
mantengono le destinazioni precedenti. Nessuna non-sfruttabilità globale
delle dipendenze è dichiarata.

Il secondo reviewer Codex separato è consentito dall'owner per questa
esecuzione soltanto; governance permanente e altri gate invariati. Il writer
è contato una volta. Al momento di questa receipt locale, candidato
committato, CI esatta, quorum finale, merge e verifica main sono PENDING.
Una receipt successiva deve attestare l'integrazione effettiva. Ardesia resta
soltanto locale. Nessun deploy, release, nuova credenziale o spesa.
