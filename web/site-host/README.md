# Guscio ospite dimostrativo — Kirchhoff dentro il sito

Guscio statico di produzione verosimile (`index.html` + `host.css`, più un
micro-script di sola idraulica). Modella intestazione del sito, copia
d'ingresso, area Kirchhoff, invito schermo intero, vincoli reattivi.
**Nessuna logica elettrica**: l'unico contratto con il banco è l'URL con
deep link nell'iframe. Niente secondo root React, niente framework.

## Demo locale (build di produzione reale, non schermate finte)

```bash
# dalla radice del repository
npm run build --prefix web
npm run preview --prefix web -- --port 4173 --strictPort
# in un'altra shell: serve il guscio
python3 -m http.server 4183 --directory web/site-host
# apri (il banco e' la build reale appena prodotta):
# http://localhost:4183/?workbench=http://localhost:4173/%23exercise%3Dpartitore-d1%26step%3D-1%26frame%3Dbefore
```

Il parametro `workbench` accetta qualunque URL assoluto `http(s)` del banco;
senza parametro il guscio punta al canonico pubblico
`https://andreamarro.github.io/kirchhoff/`.

## Misure (Playwright, `tests-e2e/site-host.spec.ts`, build reale)

| Contesto | Larghezza contenuto | Cornice | Esito |
|---|---|---|---|
| Desktop | ~1200px | 1168×720 | invarianti, rail, ispettore, risposta, tema, tastiera |
| Tablet | ~780–820px | 780×700 | usabile, senza trabocco orizzontale |
| Mobile | ~340–390px | 100%×max(620px, 86dvh) | usabile, rail orizzontale, controlli a una mano |

Regole minime sane (misurate, non presunte):

- larghezza minima ~340px (sotto, il banco stesso dichiara il limite);
- il banco intero e' alto ~850px: qualunque cornice sotto richiede
  scorrimento verticale interno, singolo e dentro la cornice (misurato:
  `scrollWidth - clientWidth = 0` fino a 480px di altezza, palco sempre
  intero, rotaia sempre azionabile);
- altezze consigliate desktop ~720px, tablet ~700px, mobile ~620px:
  tengono rotaia + palco + risposta con poco scorrimento; sotto i ~600px
  resta usabile (provato a 560px) ma l'ispettore scende sotto la piega;
- la cornice interna scorre verticalmente da sola; la pagina ospite non
  guadagna barre doppie in orizzontale a nessuna misura provata;
- intestazione appiccicosa dell'ospite e barra controlli appiccicosa del
  banco convivono: la prima resta fuori dalla cornice, la seconda dentro.

## Scelta raccomandata (default del sito)

**Opzione B — pagina di atterraggio con cornice + «Apri a schermo intero»**,
con la pagina intera dedicata come alternativa sempre valida.
Motivi misurati: su desktop la cornice tiene rail, circuito e ispettore
insieme senza scorrimenti strani; su mobile la cornice resta usabile ma la
pagina dedicata dà più aria al circuito; la tastiera resta nella cornice;
il guasto di trasporto si supera con Riprova senza ricaricare l'ospite;
la manutenzione è un URL, non un secondo front-end.

## File

- `index.html` — guscio (header, copia, area Kirchhoff, CTA, faq, footer)
- `host.css` — stili autonomi dell'ospite
- `copy-it.md` — copia d'ingresso pronta per il sito reale
- `../tests-e2e/site-host.spec.ts` — misure riproducibili contro build reale
- `../tests-e2e/fumo-pubblico.spec.ts` — fumo pubblico + fumo d'integrazione
