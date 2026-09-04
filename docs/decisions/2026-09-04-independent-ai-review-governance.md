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
BASE_SHA=
CANDIDATE_SHA=
CI_RUN=
CI_STATUS=
REVIEWER_1_TOOL_MODEL=
REVIEWER_1_VERDICT=
REVIEWER_1_SHA=
REVIEWER_2_TOOL_MODEL=
REVIEWER_2_VERDICT=
REVIEWER_2_SHA=
FAULT_INJECTION=
P0_OPEN=
P1_OPEN=
P2_ACCEPTED=
THREADS_OPEN=
FINAL_GATE=AI_REVIEW_GATE_PASSED|AI_REVIEW_GATE_FAILED
```

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
