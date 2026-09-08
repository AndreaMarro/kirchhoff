# Contratto d'integrazione sito — Proof Workbench (beta 0.3)

Verificato il 2026-09-08 su `work/beta-hardening-0.3-integration-muse13`.
Il banco non conosce GitHub Pages: parla solo URL relativi e hash.

## URL canonico

```text
https://andreamarro.github.io/kirchhoff/
```

Stato profondo via hash, formato fisso:

```text
#exercise=<id>&step=<n>&frame=before|after
```

Esempio: `https://andreamarro.github.io/kirchhoff/#exercise=partitore-d1&step=0&frame=after`

## Strategia raccomandata

1. **Cornice (iframe)** per l'incasso nella pagina del sito — via misurata,
   non presunta (matrice in `web/tests-e2e/integrazione.spec.ts`).
2. **Pagina intera (link)** come alternativa sempre valida: un link al
   deep link qui sopra funziona senza alcun lavoro.

Snippet minimo per il proprietario del sito (nessun accoppiamento
di framework; l'ospite resta fuori da questo repository):

```html
<iframe title="Kirchhoff Proof Workbench"
  src="https://andreamarro.github.io/kirchhoff/#exercise=partitore-d1&step=-1&frame=before"
  width="1120" height="720" loading="lazy"
  allow="clipboard-read; clipboard-write"></iframe>
```

## Misure d'incorniciamento (beta remota + build locale)

- `X-Frame-Options`: assente — la cornice non e' bloccata.
- `Content-Security-Policy` / `frame-ancestors`: assenti — nessuna restrizione.
- Asset relativi (`./assets/…`, `sessions/…`, `base: "./"` in Vite):
  nessun percorso assoluto da riscrivere.
- Stato profondo dentro la cornice: l'hash vive nell'URL della cornice.
- Tastiera: gli eventi restano nella cornice (verificato: l'ospite non
  riceve i tasti premuti nel banco).
- Archiviazione negata (cookie bloccati, ITP): il banco resta in piedi,
  il tema vive in memoria per la sessione.

## Dimensioni pratiche

| Contesto | Cornice provata | Esito |
|---|---|---|
| Desktop larga | 1120×720 | invarianti, rifiuto, tema, copia |
| Tablet | 780×700 | usabile, senza trabocco |
| Mobile 390px | 358×640 | usabile, senza trabocco |

Regola: nessuna larghezza sotto ~340px; altezza minima ~600px
sotto la quale l'ispettore richiede scorrimento interno.

## Comportamenti garantiti dentro la cornice

- Niente trabocco orizzontale del documento a nessuna misura provata.
- Circuito, rail, ispettore, evidenza, rifiuto, tema: come da pagina intera.
- Guasto di trasporto: si dichiara come mancato caricamento con Riprova
  e si supera **senza ricaricare la pagina ospite**.
- Copia-link copia il **deep link autonomo del banco** (URL della cornice):
  e' il comportamento voluto. Stessa origine: riesce sempre. Origine
  diversa: richiede `allow="clipboard-read; clipboard-write"` sulla cornice;
  senza delega il pulsante resta onesto (nessun falso "Copiato").

## Modalita' embed: non necessaria

Nessun `?embed=1`, nessuna chrome alternativa. Motivo: nessun problema
concreto misurato (niente doppia branding conflittuale, niente conflitto
di altezza, navigazione coerente). Stesso banco, guscio invariato.
Solo presentazione sarebbe ammessa in futuro; mai dati, passi, risposta,
stato di verita', rifiuto/guasto, evidenza, certificazione.

## Futuro stesso-dominio (`/kirchhoff/`)

Pronto senza modifiche applicative: asset relativi, JSON di sessione
relativi, stato solo in hash (nessuna riscrittura server richiesta).
Resta da decidere fuori da questo repository hosting e migrazione;
nessuna migrazione in questa sessione.

## Ipotesi di sicurezza e isolamento

- Il banco non legge `window.parent`, non chiama l'ospite, non dipende
  dall'origine dell'ospite.
- L'ospite non deve ispezionare il DOM della cornice: l'unico contratto
  e' l'URL col deep link.
- `source_sha` nelle sessioni e' provenienza dichiarata dal generatore,
  non autenticita' storica verificata (H3 resta differito).
