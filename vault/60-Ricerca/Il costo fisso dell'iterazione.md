---
tipo: misura
fonte: docs/04-ricerca-token-e-automiglioramento.md §2.1
---

# Il costo fisso dell'iterazione

Misurato sulla stessa macchina, riportato da tre sessioni indipendenti. È il costo **per rispondere
«ok»** — prima di qualunque lavoro, a **ogni** iterazione.

| configurazione | `cache_creation` | costo |
|---|---:|---:|
| baseline, 92 plugin abilitati su 300 installati | 46 943 | $0,479 |
| `--strict-mcp-config` | 46 958 | $0,479 |
| `--setting-sources project,local` | 6 316 | $0,0736 |
| **`--setting-sources project,local` + cinque `--plugin-dir` mirati** | **12 218** | **$0,1451** |

## Tre letture

1. **`--strict-mcp-config` non taglia niente.** 46 958 contro 46 943. Risultato negativo misurato:
   non riprovarlo.
2. La terza riga è a costo minimo **ma senza gli strumenti**: non è utilizzabile da sola.
3. La quarta è quella scelta: **3,3× di risparmio**, strumenti inclusi.

## ⚠️ La trappola

> `--plugin-dir` inesistente → **exit 0**, il comando gira senza quella skill, **in silenzio**.
> Fallisce aperto.

Un percorso sbagliato non produce errore: produce un loop che gira senza gli strumenti che credi di
avergli dato. **Prima di lanciare: `ls -d` su ogni percorso, e leggi l'exit.**

È la stessa classe di [[La memoria letta e mai scritta]]: sembra funzionare.

← [[Risparmio token]]
