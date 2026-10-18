# Evidenze della consegna del 18 ottobre 2026

Pacchetto tecnico per il candidato applicativo `a7890f9` del ramo
`codex/gov-k-01-20261018`. Leggere la [consegna dettagliata](../../ops/CONSEGNA-2026-10-18.md).

- [Manifest e hash](manifest.json): ogni file elencato ha SHA-256 originale e pubblico.
- [Gate Python](offline-verification-transport/receipt.json), [JUnit](offline-verification-transport/pytest.xml), [coverage](offline-verification-transport/coverage.json).
- [Build/unit web](offline-transport-web-source-binding.json), [browser](offline-browser-source-binding.json), [legame ai byte committati](offline-verified-commit-binding.json).
- [Review del verificatore](review-disposition.json) e [review offline](offline-review-disposition.json): verdetti originari e disposizione dell'autore, senza quorum inventato.
- [Oracolo/flow sintetico](divider-offline-flow/receipt.json), [precondizioni StudentTrace](loaded-method-precondition-observation.json).
- [Quaderno sintetico](divider-offline-flow/quaderno.json), [PDF di nove pagine](divider-offline-flow/lezione.pdf), [tutte le pagine rese](divider-offline-flow/pdf-pages/contact.png).
- [Desktop](divider-offline-flow/desktop-correct.png), [errore numerico](divider-offline-flow/desktop-wrong.png), [mobile](divider-offline-flow/mobile-entry.png), [cold reopen online](divider-offline-flow/cold-reopen.png), [cold reopen offline](divider-offline-flow/offline-cold-reopen.png).

I file di testo differiscono dagli originali soltanto per segnaposto dei percorsi
locali: `${REPO_ROOT}`, `${EVIDENCE_ROOT}`, `${USER_HOME}`, `${TMP_ROOT}` e
`${CHROMIUM_EXECUTABLE}`. Anche gli hash dei log nelle ricevute originali sono
conservati: per la copia pubblica usare il digest nel manifest. La configurazione
Playwright è una registrazione della configurazione usata; sostituire i
segnaposto e scegliere nuovi output prima di rieseguirla.

Le immagini e il PDF sono dati sintetici originali, senza foto o scena personale.
Sono stati prodotti nelle osservazioni delle 13:36–13:40 UTC. La suite finale
con fingerprint è successiva (14:46–14:52 UTC); non si attribuisce retroattivamente
lo SHA finale ai vecchi export. Il runtime dichiarava la revisione di base
mentre i byte della feature erano ancora non committati, come mostrano le ricevute.

I fallimenti precedenti sono descritti nella consegna; gli originali completi,
i trace, i documenti di contesto e i materiali personali restano nell'archivio
locale. Questi documenti non sono pubblicati da questo pacchetto. I test pubblici
e i lockfile permettono di ripetere i gate; un receipt locale non è un'approvazione
scientifica, una firma docente o il gate tra due famiglie indipendenti.

Per verificare le copie, dalla root del repository:

```bash
python3 - <<'PY_CHECK'
from pathlib import Path
import hashlib, json
root = Path('docs/evidence/2026-10-18-convergence')
manifest = json.loads((root / 'manifest.json').read_text())
for entry in manifest['files']:
    data = (root / entry['path']).read_bytes()
    assert len(data) == entry['bytes']
    assert hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
print(len(manifest['files']), 'evidenze integre')
PY_CHECK
```

Il manifest esclude se stesso e questo README per evitare hash autoreferenziali.
La CI remota e lo SHA dell'head documentale sono riferiti dalla PR GitHub.
