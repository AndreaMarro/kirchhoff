---
storia: h5-main-verificato
istante: 20261015T112300Z
sha: 1b2ac783898ae273367e5586d6afb8942d39218e
ramo: codex/h5-main-receipt-20261015
esito: promosso
tipo: receipt-di-giro
---

# Giro 20261015T112300Z — h5-main-verificato

> Questa nota registra MISURE, non giudizi. Un giudizio di modello che
> entrasse qui diventerebbe, tre giri dopo, un fatto che nessuno ha
> verificato.

## Misure agli oracoli

| grandezza | valore |
|---|---|
| `test_passati` | 2541 |
| `test_falliti` | 0 |
| `copertura` | CI 97.31% / soglia 95% |
| `recinti` | PASS |
| `dominio` | 100% |
| `verde` | True |

## Esito: promosso

## Revisioni

- Separate adversarial Codex postmerge APPROVE; SHA256 4e2b76d3dcec213b9c607d6d9d582b54c32039789d946123fdad0b9ce010a611

## Archi

- [[00-INDICE]]

## Oggetto della promozione e ordine dei fatti

La promozione registrata riguarda PR #21, unita il 2026-10-15 alle 11:07:44Z:
base `edd29eac7511db379437c6b8a06426b46d1b0f5c`, candidato
`071f12eab56dd78eabdeaf0e1eb9c4a72b0ab4e9`, nuovo main
`1b2ac783898ae273367e5586d6afb8942d39218e`, tree
`bc93ae33634fd4ba671fe89ecda2943f4aba8b44`, parent [base, candidato].
Il tree main coincide esattamente con quello revisionato. Questa nota è un delta
documentale successivo: non era nel tree del candidato e non dichiara già integrato
il commit che la conterrà. La receipt precommit conserva i suoi stati PENDING.

Il gate candidato è registrato nel body della PR: due review APPROVE, una primaria
del writer contata una sola volta e una avversaria in contesto distinto, quattro
CI concluse sul candidato e sul suo merge sintetico. Il proprietario ha autorizzato
per questa sola esecuzione il secondo reviewer Codex al posto della famiglia
differente; policy permanente e tutti gli altri gate invariati. Nessun approval
GitHub impersonato. Gate SHA256:
`f3a173f3494429b67cc122931baa41cf229f4e920614c8c245381c052d661d1b`.

## Verifica del main effettivo

- CI push test, run 38725139060: 2541 PASS, 3 SKIP, copertura 97,31% oltre soglia
  95%, dominio 100%, confini PASS. Log SHA256
  `ab317755eb7c010f90bab39d2410225653124ca3d0bb832b8985ecfe5ce3c088`.
- CI push web, run 38725138948: 227 unit PASS, 160 browser PASS, 54 SKIP.
  Log SHA256 `71bafcdacc180515441ecda6b62819c6aeaec2607652e6e0549256ba97a110d8`.
  Entrambi i checkout effettivi nei log sono il nuovo main; nessun rerun.
- Build standalone e MCP PASS. HTML `cbaef527…`, JS `e095b964…`, CSS `9ae8536b…`
  coincidono con il candidato. Tutti i 923 file serviti corrispondono alla build.
- Tre run locali distinti: 16 navigazione proof/componente, 2 continuità DC,
  22 AC/Laplace PASS. Zero fail, skip o flaky nei tre run. I 22 derivano da quattro
  spec su desktop/mobile e non si sommano come test unici al profilo CI.
- API locale reale sul nuovo main: apertura del vecchio quaderno, avviso motore
  cambiato, Prima/Dopo con tastiera, lettura incerta senza falsa accusa,
  chiarimento e primo errore al passo 2, PDF e quaderno, riapertura in nuovo
  contesto. Quattro corpi solve DC e dodici lesson AC/port/Laplace salvate portano
  il nuovo source SHA. ProductVerified resta false.
- I build canonici dipendono anche dal profilo: DC `f92d7d03…`, AC `a09b7b52…`,
  port `b687dbb4…`, Laplace `9f21005d…`. Il reviewer li ha ricostruiti dai 108
  sorgenti e dai call site, senza eseguire il solver. I cataloghi statici conservano
  la provenienza del producer pulito `8a580e9658098b6f91fb16febe5396502c46c268`.

Il PDF DC main ha 6 pagine, 49.775 byte, SHA256
`26080d0ab223bef1852a43121d2a68e61b29a0ef221f04ee8f4d1133f391e427`.
Una normalizzazione soltanto in memoria dell'unico token UTF16 del Subject
sourceSHA ricostruisce ogni byte del PDF candidato. Il quaderno è byteidentico al
candidato, SHA256 `7e93bc0f70c01848a7f83b68a66b163e502c1a4c0b32ddcfe661f2cc0e2bba29`.
Writer e reviewer hanno ispezionato i quattro nuovi PNG DC. Non viene dichiarata
una nuova ispezione visiva completa di ogni PDF o delle schermate AC/Laplace.

## Fallimenti e limiti preservati

Il primo full locale 1 FAIL / 2543 PASS per drift del catalogo StudentApp resta
fallito. La successiva rigenerazione canonica ha portato al nuovo full verde;
il test stretto e il fingerprint globale non sono stati indeboliti. Gli errori
precedenti dei soli harness/audit restano registrati. Il nuovo audit main aveva
assunto erroneamente il build DC per tutti i profili: corretti i controlli degli
stessi corpi sui call site canonici, senza rerun o retag del prodotto.

È integrata la sola navigazione Claim → derivazione → passo. Full K4 (residui,
cross-check, terminal mapping e provenienza completa) resta DEFERRED a H5/K4;
autenticità DEFERRED a H3. P3 affidabilità locale → issue #20; scroll iniziale 349
→ unità isolata UX host/frame. Nessuna delle 21 famiglie è completa; design e
accessibilità globali, PDF-UA, durabilità Ardesia e pilot umano non attestati.

Nel readback finale: PR #21 MERGED, zero PR Kirchhoff aperte, tutte le 27 ref
identiche al postmerge, gh-pages invariato e protezioni immutate. Il comando è
merge ordinario con match-head, senza admin, auto-merge o cancellazione branch.
Nessun deploy, release, nuova credenziale o servizio a consumo. Ardesia rimane
soltanto locale per istruzione esplicita del proprietario.

Prova pubblica: https://github.com/AndreaMarro/kirchhoff/pull/21#issuecomment-6190861930

not_checked: ulteriori input/famiglie; implementazioni K4/H3 future; intero design
WCAG/PDF-UA; nuovi browser/durabilità Ardesia; host MCP esterni; pilot umano;
assenza universale di integrazioni terze o eventi remoti non osservati.
