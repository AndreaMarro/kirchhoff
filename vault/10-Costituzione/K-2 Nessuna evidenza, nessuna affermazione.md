---
tipo: legge
id: K-2
---

# K-2 — Nessuna evidenza, nessuna affermazione

Ogni claim di dominio rilevante porta un riferimento allo stato, agli elementi e alla regola o al
verifier che lo sostengono.

## Il claim è un tipo, non una frase

```text
Claim
├── claim_type
├── state_id
├── subject_ids
├── evidence_ids
├── verifier_id + version
└── status
```

## Eco nel processo

Lo stesso schema è ciò che rende il [[Tracciamento derivato dalle prove]] diverso da una tabella:
uno stato dichiarato senza prova è un claim senza `evidence_ids`.

← [[Costituzione Kirchhoff]]
