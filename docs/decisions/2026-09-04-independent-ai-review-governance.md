# Decisione — Independent AI Review Gate

Data: 2026-09-04
Stato: ADOTTATA
Ambito: repository `AndreaMarro/kirchhoff`

## Decisione

Per il progetto Kirchhoff, mantenuto principalmente da un singolo autore, il gate di merge non richiede più una review umana indipendente come requisito di governance del progetto.

Il gate è sostituito da `INDEPENDENT_AI_REVIEW`.

Questa scelta NON afferma che una review AI equivalga a una review umana. È una diversa politica di controllo qualità, scelta consapevolmente per un progetto personale e resa verificabile tramite quorum, exact-SHA evidence, CI, fault injection e registrazione delle review.

## Requisiti del gate

Una PR può essere dichiarata `AI_REVIEW_GATE_PASSED` solo se TUTTI i requisiti seguenti sono soddisfatti sullo stesso candidate SHA.

1. **Exact-SHA CI verde**
   - il workflow richiesto deve essere `SUCCESS` sul candidate SHA esatto;
   - una CI verde su uno SHA precedente è solo evidenza storica.

2. **Due review AI indipendenti**
   - almeno due reviewer AI di famiglie/tool differenti;
   - almeno una review deve essere eseguita da **Codex**;
   - il secondo reviewer non deve essere Codex e deve appartenere a una famiglia/tool diversa;
   - ogni reviewer deve dichiarare tool/modello, candidate SHA, base SHA, data e verdict.

3. **Indipendenza operativa**
   - ogni reviewer deve analizzare il codice/diff senza assumere corrette le conclusioni di una review precedente;
   - il reviewer deve cercare attivamente falsificazioni, non conferme;
   - idealmente la review iniziale non deve leggere il verdict dell'altro reviewer prima di formulare il proprio.

4. **Review avversariale**
   - almeno una delle due review deve includere fault injection, mutation test, scenario di forgery o altro tentativo concreto di rompere le invarianti rilevanti;
   - coverage alta da sola non soddisfa questo requisito.

5. **Zero P0/P1 irrisolti**
   - nessun finding classificato P0 o P1 può restare aperto;
   - P2/P3 devono essere esplicitamente classificati e assegnati a un gate futuro o accettati come debito.

6. **Dissenso tra reviewer**
   - `APPROVE + APPROVE` => quorum soddisfatto, se gli altri requisiti sono verdi;
   - `APPROVE + REQUEST_CHANGES` su P2/P3 => l'autore deve risolvere il punto o motivare tecnicamente il non-blocker; dopo la modifica serve nuova exact-SHA review del delta;
   - qualunque `REQUEST_CHANGES` motivato da P0/P1 => gate fallito fino alla correzione;
   - se la severity resta contestata, serve un **terzo reviewer AI tie-breaker** di una terza famiglia/tool.

7. **Conversazioni**
   - nessun thread di review classificato blocker può restare irrisolto;
   - un finding deferito deve avere destinazione esplicita (es. R1, R2, H3, H5, R3).

8. **No self-approval semantico**
   - l'agente che ha prodotto materialmente il delta non può essere contato come entrambi i reviewer;
   - una review deve essere eseguita in una sessione distinta e con istruzione esplicita di revisione avversariale.

## Receipt minima obbligatoria

Ogni gate deve registrare almeno:

```text
AI_REVIEW_GATE_RECEIPT

BASE_SHA=<sha>
CANDIDATE_SHA=<sha>
CI_STATUS=<SUCCESS|FAILURE>
CI_RUN=<url-or-id>

REVIEWER_1_TOOL_MODEL=<...>
REVIEWER_1_DATE=<YYYY-MM-DD>
REVIEWER_1_BASE_SHA=<sha>
REVIEWER_1_CANDIDATE_SHA=<sha>
REVIEWER_1_VERDICT=<APPROVE|REQUEST_CHANGES>
REVIEWER_1_P0=<none|finding(s)>
REVIEWER_1_P1=<none|finding(s)>
REVIEWER_1_P2=<none|finding(s)>
REVIEWER_1_P2_DISPOSITION=<NOT_APPLICABLE|FIXED_IN_CANDIDATE|ACCEPTED|DEFERRED|BLOCK>
REVIEWER_1_P2_DESTINATION=<N/A|H3|H5|R1|R2|R3|PR...|issue...|decision record...>
REVIEWER_1_P3=<none|finding(s)>
REVIEWER_1_P3_DISPOSITION=<NOT_APPLICABLE|FIXED_IN_CANDIDATE|ACCEPTED|DEFERRED|BLOCK>
REVIEWER_1_P3_DESTINATION=<N/A|H3|H5|R1|R2|R3|PR...|issue...|decision record...>
REVIEWER_1_ADVERSARIAL_EVIDENCE=<...>
REVIEWER_1_RESIDUAL_RISKS=<...>

REVIEWER_2_TOOL_MODEL=<...>
REVIEWER_2_DATE=<YYYY-MM-DD>
REVIEWER_2_BASE_SHA=<sha>
REVIEWER_2_CANDIDATE_SHA=<sha>
REVIEWER_2_VERDICT=<APPROVE|REQUEST_CHANGES>
REVIEWER_2_P0=<none|finding(s)>
REVIEWER_2_P1=<none|finding(s)>
REVIEWER_2_P2=<none|finding(s)>
REVIEWER_2_P2_DISPOSITION=<NOT_APPLICABLE|FIXED_IN_CANDIDATE|ACCEPTED|DEFERRED|BLOCK>
REVIEWER_2_P2_DESTINATION=<N/A|H3|H5|R1|R2|R3|PR...|issue...|decision record...>
REVIEWER_2_P3=<none|finding(s)>
REVIEWER_2_P3_DISPOSITION=<NOT_APPLICABLE|FIXED_IN_CANDIDATE|ACCEPTED|DEFERRED|BLOCK>
REVIEWER_2_P3_DESTINATION=<N/A|H3|H5|R1|R2|R3|PR...|issue...|decision record...>
REVIEWER_2_ADVERSARIAL_EVIDENCE=<...>
REVIEWER_2_RESIDUAL_RISKS=<...>

OPEN_P0=0
OPEN_P1=0
OPEN_BLOCKER_THREADS=0

FINAL_GATE=<AI_REVIEW_GATE_PASSED|AI_REVIEW_GATE_FAILED>
```

Vocabolario obbligatorio, distinto per ogni reviewer:

- **classification** = quanto è grave il finding: `P0`, `P1`, `P2`, `P3`.
  Ogni reviewer deve classificare esplicitamente P0, P1, P2 e P3
  (valorizzare con `none` quando assenti, mai omettere la voce).
- **disposition** = cosa si è deciso di farne:
  `BLOCK`, `FIXED_IN_CANDIDATE`, `ACCEPTED`, `DEFERRED`, `NOT_APPLICABLE`.
  Ogni P2 e ogni P3 non-`none` deve avere una disposition esplicita;
  quando P2/P3 è `none`, la disposition è `NOT_APPLICABLE`.
- **destination** = dove viene chiuso il finding differito
  (es. `H3`, `H5`, `R1`, `R2`, `R3`, `PR #10`, `PR #11`,
  `issue <id>`, `decision record <path>`).
  È obbligatoria quando la disposition è `DEFERRED`;
  quando la disposition non è `DEFERRED`, la destination è `N/A`.

Regole di completezza (normative):

- A deferred P2/P3 finding without an explicit destination is an incomplete
  receipt and cannot contribute to AI_REVIEW_GATE_PASSED.
- Missing mandatory receipt metadata => gate remains NOT_SATISFIED.
  In particolare, un receipt senza reviewer date per ciascun reviewer,
  senza classificazione esplicita di P2/P3, o senza disposition/destination
  esplicite di P2/P3, non può supportare `AI_REVIEW_GATE_PASSED`.

Chiarimento non-blocker (nessun indebolimento di P0/P1):

- Un P2 correttamente classificato con disposition `FIXED_IN_CANDIDATE`,
  `ACCEPTED`, oppure `DEFERRED` con destination esplicita, è compatibile
  con `AI_REVIEW_GATE_PASSED` quando P0/P1 aperti sono zero e tutti gli
  altri requisiti del gate sono soddisfatti.
- Un finding P0/P1 non può essere sbloccato con `DEFERRED` ai fini del gate:
  resta blocker fino a `FIXED_IN_CANDIDATE` (o riclassificazione motivata
  con tie-breaker secondo §6 dei requisiti).

## Politica specifica per Codex

La review Codex deve:

- lavorare sul candidate SHA esatto;
- leggere prima codice/diff, poi test, poi documentazione;
- controllare invarianti e trust boundary;
- tentare almeno un caso di falsificazione quando il dominio lo consente;
- distinguere fatti osservati, inferenze e raccomandazioni;
- produrre un verdict `APPROVE` o `REQUEST_CHANGES`;
- non usare il conteggio test o la coverage come sostituto della review semantica.

## Rapporto con GitHub branch protection

Questa decisione descrive la governance del progetto.

Le GitHub branch protection/ruleset devono essere configurate in modo coerente:

- required status check `test`: mantenuto;
- strict/up-to-date branch requirement: mantenuto se già attivo;
- conversation resolution: mantenuto;
- required approving human reviews: **0**, perché il gate di governance è ora `INDEPENDENT_AI_REVIEW`;
- nessun bypass automatico della CI.

Se GitHub continua a richiedere una review umana, la PR può risultare tecnicamente `AI_REVIEW_GATE_PASSED` ma `GITHUB_POLICY_BLOCKED`; non va descritto come fallimento tecnico del codice.

## Applicazione a PR #8

PR #8 H2.5 passa al nuovo processo.

Le review AI storiche già prodotte restano evidenza tecnica, ma per soddisfare formalmente il nuovo gate sul candidate corrente devono essere attribuibili a tool/modello e candidate SHA.

Per il candidate corrente è richiesto almeno:

1. review **Codex** sullo SHA esatto;
2. review di un secondo modello/tool indipendente sullo stesso SHA;
3. CI exact-SHA verde;
4. almeno una review con fault injection;
5. zero P0/P1 irrisolti.

## Non-goal

Questa policy non introduce `Product Verified`, non modifica i trust boundary runtime di Kirchhoff e non sostituisce H3/H5. Governa esclusivamente il processo di integrazione del codice.
