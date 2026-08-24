# Kirchhoff

Risolutore di circuiti verificato. Il valore non è la risposta: è che la risposta ha superato
cinque controlli indipendenti prima di essere mostrata.

Il piano completo è in `docs/00-fonte-piano-kirchhoff.md` (decisioni **D1–D12** in testa, sono il
contratto). Gli artefatti BMAD stanno in `_bmad-output/`.

## Stato

Fase *plan* completa. **Epic 1 chiusa** (apparato di misura), verdetto
`accepted-with-open-items` — vedi `_bmad-output/implementation-artifacts/epic-1-retro-2026-08-13.md`.
Epic 2 in corso: il motore verificato da riga di comando.

| Storia | Stato |
|---|---|
| 1.1 Insieme di riferimento a risposta nota | `done` — quattro classi di dominio verificate: `dc_resistive`, `transient`, `ac_sinusoidal`, `three_phase`. Resta aperta la metà fotografica (CGHD), che dipende da una decisione umana |
| 1.2 Script di valutazione | `done` — metriche riproducibili, matrice degli errori chiusa |
| 2.1 Struttura con confini verificati | `done` — controllo dei confini sull'albero sintattico, configurazione validata all'avvio |

## Uso

```bash
uv run kirchhoff-eval build --n 60 --out reference-set
uv run kirchhoff-eval report --root reference-set --split dev
uv run --with pytest python -m pytest tests -q
```

La parte trattenuta dell'insieme non è leggibile dal flusso di sviluppo: serve `--allow-holdout`,
e usarla durante lo sviluppo invalida ogni misura successiva.

## I gate

Tre controlli che falliscono da soli, senza che qualcuno debba ricordarsene:

```bash
uv run python scripts/check_domain_coverage.py   # domain/ al 100%, righe e rami
uv run python scripts/check_boundaries.py        # domain/ non importa fuori da sé
uv run --with pytest --with pytest-cov python -m pytest   # copertura globale >= 95%
```

Il controllo dei confini legge l'albero sintattico, non il testo: `import kirchhoff.adapters as a`
e `from kirchhoff import pipeline` sono viste come `from ..adapters import x`, e un percorso
sbagliato solleva invece di dichiarare tutto pulito.

La configurazione (`src/kirchhoff/config.py`) valida all'avvio e **impedisce di partire** se
qualcosa non torna. Tre vincoli del piano vivono lì come condizioni di avvio invece che come prosa:
almeno 3 passi di estrazione (D4, AD-12), immagini cancellate entro 72 ore (FR-30), dati in Unione
Europea (NFR-14). Le soglie stanno sul tipo `Settings`, non nel lettore: costruirlo a mano non le
aggira.

## Come è verificato l'oracolo

Un oracolo che si autocertifica non è un oracolo. Per ogni classe, chi genera un caso e chi lo
verifica partono da estremi opposti e devono incontrarsi **esattamente**:

| Classe | Costruzione | Verifica indipendente |
|---|---|---|
| `dc_resistive` | albero serie/parallelo, tensioni propagate sulle foglie | analisi nodale sull'IR appiattito, che dell'albero non sa nulla |
| `ac_sinusoidal` | stesso albero, ma con impedenze complesse | analisi nodale complessa |
| `three_phase` | circuito monofase equivalente più rotazione di 120° | analisi nodale sull'intera rete, che della simmetria non sa nulla |
| `transient` | si scelgono le radici caratteristiche, si derivano i componenti | la matrice MNA a sorgenti spente deve essere singolare in quelle radici |

Tutta l'aritmetica è esatta: `Fraction`, e per fasori e trifase il campo ciclotomico `Q(ζ₁₂)`, che
contiene insieme `j` e `√3`. Un float non entra: né in un valore di componente, né nel campo — e il
tentativo è un errore, non un arrotondamento. Quindi la somma delle tre correnti di fase è **zero**,
non "circa zero", e un residuo diverso da zero è sempre un bug.

## Attribuzioni

Il materiale esterno usato e le sue licenze sono in `docs/01-fonti-esterne.md`.
