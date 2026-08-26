# Kirchhoff

**Il contesto di questo progetto vive in [`AGENTS.md`](AGENTS.md). Leggi quello.**

Questo file esiste perché lo cerchi chi arriva da un altro progetto, e non ripete
ciò che AGENTS.md dice. Due file che descrivono la stessa cosa divergono nel punto
dove nessuno guarda — è il difetto E-62 del registro degli errori, e sarebbe
sciocco commetterlo proprio nel file che dovrebbe prevenirlo.

Le tre cose che servono prima di toccare qualunque cosa:

```bash
uv run --with pytest --with pytest-cov python -m pytest tests
```

`uv run python -m pytest` esce **1** con «No module named pytest», e `--no-cov`
senza `pytest-cov` fra i `--with` esce **4** per errore d'uso: un'uscita che
somiglia a un test rosso e non lo è.

```bash
./ops/loop/kirchhoff-loop dry-run 1.7
```

Il piano di un giro senza spendere un token. Il lavoro di implementazione passa
dal loop, non da modifiche a mano.

```bash
cat vault/10-Costituzione/'Confini owner-locked.md'
```

Cosa nessun agente può decidere da solo — la definizione di `Verified`, le soglie
di qualità, l'holdout, gli invarianti di privacy. Incontrarne uno ferma il lavoro
e si segnala: non si sceglie, non si aggira.
