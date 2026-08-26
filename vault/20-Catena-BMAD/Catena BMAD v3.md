---
tipo: stato
fonte: _bmad-output/planning-artifacts/bmad-chain-status.json
generato_da: scripts/bmad_chain.py
aggiornato: 2026-08-14
---

# Catena BMAD v3 — correct-course chain-top

Otto passi dal piano master §25.1. **Non si costruisce Gate A finché la catena non è chiusa**: le
epiche attuali descrivono un prodotto che non è più questo.

## Stato al 14 agosto 2026, 12:20

| # | Passo | Stato | Prova sul disco |
|---|---|---|---|
| 1 | Costituzione K-0…K-5 | ✅ | `02-costituzione-kirchhoff.md` |
| 2 | Brief update | ✅ | `brief.md` `version: 3` + `addendum.md` §H |
| 3 | **PRD v3** | ⬜ **prossimo** | attende `version: 3` |
| 4 | UX Pro update | ⬜ | attende `version: 3` su DESIGN + EXPERIENCE |
| 5 | Architecture Spine v2 | ⬜ | attende `version: 2` + `LayoutPatch` |
| 6 | Ribilanciamento epiche → Gate A–G | ⬜ | attende «Gate A» e «Gate G» |
| 7 | Readiness gate | ⬜ | attende `version: 3` |
| 8 | Ship loop | ✅ | `.claude/loop.md` coi marcatori |

**Questa tabella è una fotografia, non la verità.** La verità è
`uv run python scripts/bmad_chain.py stato`. Vedi [[Tracciamento derivato dalle prove]].

## Cosa deve entrare nei documenti dei passi 3-7

`CircuitIR` e `LayoutIR` **distinti** · `ProofGraph` (non lista lineare) · `LayoutPatch` con
`preserve/remove/create/node_mapping/reroute_scope` · grammatica obbligatoria di ogni passo
`BEFORE + ACTION + AFTER + EQUATION + CERTIFICATE + PROVENANCE` · visual round-trip con confronto
esatto di grafi, **non** un VLM che dice «sembra giusto» · metriche NED, TVR, VCER, SEC, RRC, VDR
con north star **VVDR** · tre adapter, un kernel.

## Poi

FASE 2, **Gate A — Visual Proof Kernel**, con il suo kill criterion: se la continuità visuale non è
chiaramente migliore di un re-layout completo, non espandere il catalogo. Bastano serie, parallelo e
partitore per saperlo.

Vedi anche: [[Costituzione Kirchhoff]] · [[Decisioni aperte]] · [[Lezioni sul loop]]
