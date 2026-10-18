# ADR-GOV-CODEX-001 — Verifiche senza dipendenza dal worker

Data: 18 ottobre 2026. Stato: **PROPOSTA, NON ADOTTATA**.
Ambito implementato: comando locale di verifica affiancato al processo corrente.
Ritiro di BMAD/Claude e autorizzazione al merge: **non ottenuti da questa ADR**.

## Problema e decisione proposta

L'entrypoint corrente lega doctor e scheduler a Claude e al runtime BMAD installato
fuori dal repository. Lo scheduler contiene `--dangerously-skip-permissions`.
I gate deterministici non richiedono quel worker: possono eseguire i comandi già
versionati conservando origine, log, esiti e limiti. Il worker della chat può così
verificare un candidato senza avviare un'altra sessione a pagamento o concedere
un'approvazione di prodotto.

Si propone una migrazione incrementale. Il primo incremento aggiunge soltanto
`ops/loop/kirchhoff-loop verify --output DIRECTORY_ESTERNA_NUOVA`.
Usa `.venv/bin/python`, che va preparato con
`uv sync --frozen --extra dev --extra mcp`. Non installa tool, non modifica gli
artefatti di planning e non determina quale storia sia eleggibile.

## Controlli conservati e dipendenze

| Ingresso / autorità | Comando / generatore | Prova prodotta |
|---|---|---|
| Planning e catena dichiarata | `scripts/bmad_chain.py verifica --con-loop` | Log di coerenza; nessuna promozione di readiness |
| Test e configurazione pytest correnti | `python -m pytest tests` con report JUnit e coverage della corsa | Numero passato/fallito/saltato, log ed hash |
| Decisione di copertura del 18 ottobre, baseline versionata | `scripts/check_domain_coverage.py` sul nuovo report | Minimo globale, assenza regressione, dominio 100% |
| Confini architetturali | `scripts/check_boundaries.py` | Log del controllo esistente |
| File locali, commit e symlink | Fotografia Git + SHA256 prima/dopo | Il risultato non vale se le sorgenti cambiano durante i controlli |
| Costituzione, confini owner-locked, policy review | Restano autorità vigenti | Nessun nuovo `Verified` e nessun permesso di integrazione |

Il DAG operativo è: policy/configurazione → entrypoint CLI → verificatore neutrale
→ catena → pytest → coverage fresca → boundary → ricevuta locale.
Il vecchio DAG di selezione/build/review/promozione resta attivo e non viene
sostituito da quello di verifica.

Il report di coverage risiede nella directory nuova della corsa: un report
preesistente nella root non è un input valido. Un exit non-zero, un timeout, una
suite senza test effettivamente passati, un report assente o una mutazione delle
sorgenti impediscono `CHECKS_PASSED`. Gli skip sono numeri separati. I timeout
terminano il gruppo dei processi avviato, inclusi i figli sopravvissuti al padre.
Le ricevute non sono firme e restano evidenza locale modificabile.

File di evidenza precedenti al comando, symlink e antenati symlink delle sorgenti
vengono rifiutati prima della lettura. Un timeout controlla soltanto il gruppo
iniziale: un figlio che crea una nuova sessione non è confinato. Questo limite è
esplicito nella ricevuta (`process_tree_isolation=false`). Il verificatore non è
una sandbox per codice ostile. L'isolamento di worker arbitrari resta nel gate
futuro `GOV-K-01/worker-isolation`, prima di adottare un nuovo orchestratore.

## Mappa della governance da migrare in seguito

| Oggetto attuale | Classe | Trattamento proposto |
|---|---|---|
| K-0…K-5, privacy, billing, retention, holdout, counter-metriche | Owner-locked / scientifico | Preservare; nessun cambio in questo incremento |
| `AGENTS.md` tra marcatori `bmad:context` | Contesto gestito da `bmad-project-context` | Non editarlo: migrare il generatore prima del ritiro |
| Tabella FASE 1 e `bmad-chain-status.json` | Stato generato da `scripts/bmad_chain.py` | Verificare, mai riscrivere manualmente |
| `implementation-readiness.md` del 24 agosto | Gate storico `CONCERNS` | Riconciliare per storia; AGENTS oggi presente non implica PASS |
| Claude CLI, scelta modelli e flag di bypass dello scheduler | Processo legato al provider | Progettare worker sostituibile con controlli dell'ambiente conservati |
| CI Python e web | Gate deterministici | Preservare; CI remota sul candidato resta obbligatoria prima del merge |
| Decisione review AI del 4 settembre | Governance d'integrazione | Due tool/famiglie indipendenti; la self-review non soddisfa il quorum |
| `pubblica.sh` main-only | Pubblicazione | Nessun uso automatico; riconciliare separatamente il flusso PR |
| Vault e giornale storico | Prove / decisioni | Conservare; non cancellare né alterare la genealogia |

## Limiti e adozione

`CHECKS_PASSED` significa soltanto i quattro gate locali su sorgenti rimaste
identiche. Web build/unit/E2E, oracolo scientifico, review indipendente, CI remota,
approvazione docente, Pencil e pilot sono prove separate. Non significa
`FLOW_DONE`, `SCIENCE_DONE`, `PRODUCT_READY` o `AI_REVIEW_GATE_PASSED`.

Prima di ritirare l'orchestrazione attuale occorrono: inventario completo del
generatore di contesto e dei required checks, confronto su due task comparabili,
test del nuovo resolver/worker e del ripristino, conferma dei permessi e decisione
del proprietario sul processo proposto. Le misure di questo incremento non
soddisfano da sole quel gate. Nessun invio a provider o spesa esterna viene
autorizzato da un file del repository.

Rollback proposto: rimuovere il verbo `verify` e il modulo candidato con un diff
separato. Non sono coinvolti dati applicativi o migrazioni. Conservare le ricevute
private; non pubblicare dossier, inventari personali o log degli studenti.
