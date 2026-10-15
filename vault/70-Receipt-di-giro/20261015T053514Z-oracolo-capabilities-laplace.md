---
storia: oracolo-capabilities-laplace
istante: 20261015T053514Z
sha: 71aa0cf61ce53f20717ca4d7d52cda9987b94244
ramo: codex/pr17-notebook-20261015
esito: verde-test-locale-non-promosso
tipo: receipt-di-giro
---

# Giro 20261015T053514Z — oracolo-capabilities-laplace

## Requisito e baseline

Manutenzione del solo test live «il perimetro visibile coincide con quello dichiarato dal server». Nessuna nuova capability o decisione normativa. Il contratto già versionato richiede transientsTrue con risposta Laplace limitata: test_laplace_lesson111–119 e test_mcp_server60–69, capabilities schema.v1 e paragrafo UI ricevuto dal server. La precedente selezione sulla basea6 poi conservata in71aa aveva22PASS/2FAIL: il vecchio test pretendevaFalse prima di page.goto. Modulo HEAD esatto e HTTP reale concordavanoTrue; non era una nuova suite browser baseline. Quel fallimento resta registrato e non viene cambiato retroattivamente.

## Modifica delimitata

Unico file: web/tests-e2e/student-session-live.spec.ts, unico callback modificato; gli altri sei callback sono byte-invariati. Verifica HTTP riuscito, schema/solve/controlledFalse/acTrue/transientsTrue/productFalse/acCertifiedFalse e laplace_scope delimitato: tipi RLC/V/I, grandezze V/I, auto/laplace, step/impulse, tutte le condizioni iniziali C/L esplicite, dominio Laplace e unità V*s/A*s, coefficienti razionali in ordine crescente, nessuna antitrasformata/commutazione e certified_lessonFalse. Il solo cambio False→True non sarebbe sufficiente.

Dopo la navigazione e l’apertura dei dettagli, il primo paragrafo UI deve coincidere col testo scope non vuoto dichiarato dal server. App/API, solver, schema effettivo, Verified, soglie, produttori e skip restano byte-invariati. Nessuna nuova solve o API visione.

## Verifiche

- Live reale desktop/mobile:24PASS/0FAIL,27.7s, incluse le dieci esecuzioni recovery quaderno19 e la parità scope ora realmente raggiunta. Non è l’esecuzione di tutti i50casi saltati nella precedente suite default.
- Reviewer: vero callback transpiled ed expectPlaywright, un payload sano raggiunge il punto goto; quattordici mutanti rifiutati prima di goto (flag negativi, transientsFalse, forme/iniziali/dominio/unità/metodi, scope vuoto, laplace_scope assente e HTTPnonOK). È probe in memoria/fetch iniettato, non UI o baseline browser aggiuntiva. Non sono quattordici bug prodotto.
- Controprova causale UI separata: modificato solo scope nella risposta capabilities al browser con marker sintetico, desktop/mobile. Una intercettazione ciascuno, primo paragrafo mostra esattamente il testo ricevuto con marker, pageerror0. Non intercetta il fetchNode preliminare del test permanente e non viene presentata come sua esecuzione con dati diversi. Nessuna variazione della produzione per il probe.
- Quattro comandi BMAD/con-loop, confini, cachedcheck e diffunstaged exit0; verifica addizionale invarianza prodotto e hash. E2E escluse dal project tsc: eseguite/trasformate, non typecheck statiche.
- Nessun fullPython/build/defaultbrowser ripetuto per questo solo test: precedente71aa aveva2520PASS,97.36% e dominio100%, web161/defaultbrowser114PASS50SKIP. Sono misure della precedente unità, non nuove esecuzioni qui.

## Review e pin

Assessment separata recuperabile, SHA256d4968e2c2f9af2aca3d11fde215d9688ad8758099fe22b9705b915143a04599c. Review tecnica finale del singolo hash: APPROVE, report privato SHA25697b6c3a9c729ba925d0d63e7866ed7a5e7a0359938cc7dc1848b80b8a74d1b75. Contesto avversario Codex separato, modello specifico non esposto; nessun quorum formale non-Codex o approval di main. Pin futuro commit/receipt/indice ancora PENDING.

```text
17cf86d28f5d213b75070122143f6679344069ff62fa8caeac5b0d4ea3980a16  web/tests-e2e/student-session-live.spec.ts
```

## Destinazione e limiti

Corretto localmente l’oracolo che bloccava la selezione live; nessuna nuova attestazione di capacità matematica, tutte le famiglie transitorie, test umano/hardware, H3 o UI sempre corretta in ogni race. Nessun code push, CI remota, mainmerge, deploy, PRclosure o quorum. Parent16/catalogo11/host/script/provenienza e H5/K4/design/21famiglie restano unità distinte pendenti.

## Archi

- [[00-INDICE]]
