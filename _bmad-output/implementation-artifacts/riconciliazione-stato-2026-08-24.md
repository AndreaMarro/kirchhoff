---
title: 'Riconciliazione dello stato — 24 agosto 2026'
type: 'record'
created: '2026-08-24'
baseline_commit: '093d8ce'
---

# Perché

`sprint-status.yaml` dichiarava `backlog` storie il cui codice esiste, gira ed è coperto.
Lo stato del file era più indietro della realtà. L'action item #4 della retrospettiva Epic 1
lo aveva già annotato per la 2.5. Questo documento riconcilia **soltanto** ciò che
l'evidenza sostiene, e lascia dichiarato tutto il resto.

Regola applicata: una storia passa a `done` **solo** se ogni suo criterio di accettazione
ha un test nominato che passa. Nessuna storia parziale è stata marcata completa.

# Evidenza raccolta (24/08/2026)

```
$ uv run --with pytest --with pytest-cov python -m pytest tests
191 passed in 16.18s   ·   TOTAL 1046 stmt / 0 miss / 330 branch / 0 partial — 100.00%

$ uv run python scripts/check_boundaries.py
exit=0 · "domain/ non importa nulla del progetto fuori da se'"

$ uv run python scripts/check_domain_coverage.py
exit=0 · "domain/ al 100%"

$ uv run kirchhoff-eval report --root reference-set --split dev
exit=0 · {"ok": true, "total": 36, "published": 36, "VSR": 1.0, "SER": 0.0, "refusal_rate": 0.0}
```

# Storia 2.2 — schema IR e canonicalizzazione: `backlog` → `done`

I tre criteri di accettazione, ognuno con il test che lo copre, tutti verdi:

| Criterio di accettazione | Test | Esito |
|---|---|---|
| Valore privo di unità → respinto nominando il componente | `test_ir_schema.py::test_valore_nudo_respinto` | passa |
| Due IR con ordine diverso → forme canoniche identiche | `test_ir_canonical.py::test_ordine_diverso_stessa_forma_canonica` | passa |
| Generatore coi terminali invertiti → forma canonica **diversa** | `test_ir_canonical.py::test_una_sorgente_rovesciata_e_un_altro_circuito` | passa |

Anche gli altri test della mappa criterio→test della spec passano: versione semantica,
magnitudine/unità/forma simbolica, provenienza esatta quando la sorgente è un'immagine e
respinta altrove, unità incoerente col tipo, confronto identico dopo canonicalizzazione.

Comando eseguito, esito `8 passed`:

```
uv run --with pytest python -m pytest \
  tests/test_ir_schema.py::test_versione_semantica_richiesta \
  tests/test_ir_schema.py::test_ogni_componente_porta_magnitudine_unita_e_forma_simbolica \
  tests/test_ir_schema.py::test_sorgente_immagine_esige_provenienza \
  tests/test_ir_schema.py::test_provenienza_su_sorgente_non_fotografica_respinta \
  tests/test_ir_schema.py::test_valore_nudo_respinto \
  tests/test_ir_schema.py::test_unita_incoerente_col_tipo_respinta \
  tests/test_ir_canonical.py::test_ordine_diverso_stessa_forma_canonica \
  tests/test_ir_canonical.py::test_il_confronto_dopo_la_canonicalizzazione_e_identico
```

`baseline_commit` della spec resta `NO_VCS`: il lavoro precede il versionamento, e
riscriverlo con lo SHA di oggi produrrebbe un record falso.

# Storia 2.5 — MNA simbolica: resta `backlog`, con una nota

`domain/mna.py` contiene già `solve_dc`, `solve_phasor`, `mna_matrix_at`, `kcl_residuals` e
`power_balance`, coperti al 100%. **Non basta per dichiararla `done`:** la storia non ha un
file di spec, quindi non esistono criteri di accettazione contro cui misurare, e marcarla
completa significherebbe dichiarare soddisfatti criteri mai scritti.

Resta `backlog`. All'apertura della storia va riconciliato l'ambito — è esattamente
l'action item #4 della retrospettiva Epic 1, che con questo documento resta aperto e ora ha
un riferimento.

# Lacune di dominio verificate oggi (non congetture)

Rilevate leggendo il codice, non la documentazione. Non toccano lo stato delle storie, ma
vincolano la pianificazione a valle:

- **Transitori solo a stato zero.** `domain/transient.py::initial_state` sostituisce gli
  elementi di accumulo con valore `ZERO`; la docstring dichiara «a t = 0+, a stato zero».
  Nessuna condizione iniziale non nulla, nessuna commutazione, nessuna topologia per `t < 0`.
- **Nessun generatore dipendente** fra i `ComponentType`.
- **Convenzione RMS/picco assente dall'IR**: nulla distingue un'ampiezza di picco da un
  valore efficace.
- **Fasi limitate ai multipli di 30°**: `Cyc12` è l'anello ciclotomico dodicesimo, e
  `phase_steps` è un intero. Un fasore a −18° non è rappresentabile in aritmetica esatta.
- `render/`, `adapters/`, `api/`, `pipeline/` sono pacchetti vuoti (0 righe).
- Nessuna rappresentazione del procedimento dello studente esiste in alcuna forma.

Queste voci sono materiale per storie nuove, non correzioni a storie esistenti.
