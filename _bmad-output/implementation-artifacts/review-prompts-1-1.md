# Prompt di revisione per la storia 1.1 — da eseguire in una sessione separata

Lo step 4 di `bmad-build` prevede tre revisori senza contesto, idealmente su un LLM diverso.
In questa sessione i subagenti non sono disponibili, quindi le tre passate sono state eseguite
inline dall'autore del codice — che è precisamente ciò che questi prompt esistono per compensare.

**Contenuto da passare come CONTENT / review content:** il diff della storia 1.1, cioè

- nuovi: `src/kirchhoff/domain/exact.py`, `src/kirchhoff/domain/transient.py`,
  `src/kirchhoff/eval/transformations.py`, `src/kirchhoff/eval/generator_ac.py`,
  `src/kirchhoff/eval/generator_transient.py`, `src/kirchhoff/eval/generator_three_phase.py`,
  `tests/test_exact.py`, `tests/test_domain_reattivo.py`, `tests/test_domain_transitorio.py`
- modificati: `src/kirchhoff/domain/ir.py`, `src/kirchhoff/domain/mna.py`,
  `src/kirchhoff/eval/generator.py`, `src/kirchhoff/eval/reference_set.py`,
  `src/kirchhoff/eval/metrics.py`, `src/kirchhoff/eval/cli.py`,
  `tests/test_reference_set.py`, `tests/test_percorsi_di_errore.py`, `tests/test_cli.py`,
  `README.md`

## 1. Blind Hunter

> Conduct a review of CONTENT.
> Look for what's missing, not only what's wrong.
> Find at least ten issues to fix or improve.
> Output a Markdown list of findings only — no severity, priority, or ranking.
> If the content is empty, stop and say so.
> If you have zero findings, re-check and keep thinking; do not stop with an empty list.
>
> CONTENT: {diff}
>
> Do not invoke any skill. Return only the review result.

## 2. Edge Case Hunter

> Read `/Users/andreamarro/.claude/plugins/cache/bmad-method/bmad-method-analyze-plan-build/6.11.0/src/bmm-skills/ship/bmad-build/review-prompts/edge-case-hunter.md`
> completely and follow it as your review instructions.
>
> Review content: {diff}
>
> Do not invoke any skill. Return only the review result.

## 3. Verification Gap Reviewer

> Read `/Users/andreamarro/.claude/plugins/cache/bmad-method/bmad-method-analyze-plan-build/6.11.0/src/bmm-skills/ship/bmad-build/review-prompts/verification-gap.md`
> completely and follow it as your review instructions.
>
> Review content: {diff}
>
> Do not invoke any skill. Return only the review result.

## Cosa ha già trovato la revisione inline

Perché una passata indipendente non ripeta il lavoro già fatto:

1. **`Fraction(0.1)` non fallisce** — restituisce `3602879701896397/36028797018963968`. Un float
   entrava nel campo ciclotomico e in un valore di componente travestito da razionale esatto,
   compromettendo in silenzio ogni confronto a zero. Corretto: `Cyc12.of`, `Component.value` e
   `IR.omega` rifiutano tutto ciò che non è `int` o `Fraction`.
2. **`Cyc12` era diventato non hashabile** — definire `__eq__` in un corpo di classe azzera
   `__hash__`. Corretto con un `__hash__` esplicito.
3. **`_verify_transient` sollevava `KeyError`** su un id di componente sconosciuto, mentre il
   percorso in continua lo segnalava come problema. Reso simmetrico.
4. **`write` non ripuliva** — ricostruire sopra un insieme precedente lasciava casi con lo schema
   vecchio, e `load` esplodeva. Ora ogni split riparte da zero.
