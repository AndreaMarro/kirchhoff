# Test automatizzati — Epic 1

**Data:** 13 agosto 2026 · **Framework rilevato:** pytest con pytest-cov, già in uso nel progetto
(`pyproject.toml`, `[tool.pytest.ini_options]`, `--cov-fail-under=95`).

## Superficie coperta

Epic 1 non espone né API HTTP né interfaccia grafica: la sua unica superficie è il comando
`kirchhoff-eval`. I test generati sono quindi E2E di riga di comando.

## Che cosa mancava

`tests/test_cli.py` invoca `main(argv)` dentro il processo di pytest. È il test giusto per la
logica del comando, ma non attraversa mai il confine che attraversa l'utente. Restavano scoperti:

- il caricamento del modulo come `__main__` (un errore d'importazione a livello di modulo non
  sarebbe emerso);
- la propagazione del codice d'uscita al guscio — ciò su cui si regola uno script di integrazione
  continua;
- il fallimento di argparse al confine del sistema operativo, con `stdout` che deve restare vuoto
  perché nessun consumatore provi a interpretarlo come JSON.

## Test generati

`tests/test_e2e_cli.py`, tre casi, tutti lanciano un processo Python vero:

| Test | Cosa dimostra |
|---|---|
| `test_e2e_costruzione_e_rapporto` | costruzione e rapporto completano con uscita 0; le quattro classi di dominio compaiono; VSR 1.0 e SER 0.0; la nota di copertura dichiara l'esclusione dell'estrazione |
| `test_e2e_la_parte_trattenuta_fa_uscire_con_due` | il Rifiuto della parte trattenuta esce **2** e non emette alcuna metrica; con l'autorizzazione esplicita esce 0 |
| `test_e2e_argomento_sconosciuto_non_produce_json` | argparse fallisce con uscita 2, `stdout` vuoto, diagnostica su `stderr` |

## Osservazione emersa scrivendo i test

Con meno di due casi per classe (`--n` sotto 8), il taglio a metà per eccesso manda l'unico caso di
ogni classe nella parte di sviluppo e **la parte trattenuta resta vuota**. Il comando lo dichiara
nel proprio JSON (`split: {"holdout": 0}`), quindi non è silenzioso, e la costruzione documentata
(`--n 60`) produce 24 casi trattenuti. Registrato come comportamento, non come difetto.

## Esito

Suite completa verde. Copertura globale **100%** su righe e rami; `domain/` al 100%.
