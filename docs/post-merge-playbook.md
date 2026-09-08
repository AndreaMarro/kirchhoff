# Playbook post-merge — pubblicare la beta 0.3 dopo l'approvazione di PR #15

Sequenza operativa esatta. Non eseguire ora: PR #15 attende revisione
indipendente e il ramo RC resta congelato. Ogni passo verifica il
precedente; fermarsi al primo rosso e passare al rollback.

Contesto: `main` + push che tocca `web/**` attiva
`.github/workflows/deploy-workbench.yml` (build → artifact → Pages).
URL canonico: `https://andreamarro.github.io/kirchhoff/`.

## 1. Fondere la PR approvata

```bash
gh pr view 15 --json state,mergeable,reviewDecision
gh pr merge 15 --merge
git fetch origin
git rev-parse origin/main   # = FINAL_MAIN_SHA, annotarlo nella ricevuta
```

Solo merge dopo approvazione indipendente. Mai `--rebase` creativo:
la storia del RC deve restare riconoscibile.

## 2. Attendere il workflow automatico

```bash
gh run list --workflow=deploy-workbench.yml --branch main --limit 3
gh run watch <RUN_ID> --exit-status
```

Verde atteso su build (typecheck, unit, build di produzione) + deploy.
Se rosso: niente link dal sito, vai al rollback.

## 3. Verificare l'artefatto pubblicato contro main

```bash
npm run build --prefix web                                  # build attesa da main
node web/scripts/verify-artifacts.mjs https://andreamarro.github.io/kirchhoff/
```

Atteso: `MATCH` su `index.html (struttura)`, asset JS/CSS, `sessions/`
(5 file). Differenze ammesse: nessuna. Lo script confronta sha256 dei
byte: dice «il deploy è quello giusto», non chi l'ha firmato (H3 resta
differito per decisione).

Confronto incrociato con la sorgente (difende da build sporche):

```bash
diff <(git show origin/main:web/public/sessions/index.json) \
     <(curl -s https://andreamarro.github.io/kirchhoff/sessions/index.json)
# atteso: nessuna uscita
```

## 4. Fumo pubblico (solo HTTP, niente browser)

```bash
node web/scripts/smoke-public.mjs https://andreamarro.github.io/kirchhoff/
```

Atteso: homepage, asset, indice con 4 voci, partitore/scala/ponte
`closed` + rifiuto `refusal`, zero HTTP >= 400, `FUMO PUBBLICO: OK`.

## 5. Fumo browser + errori di pagina e fumo d'integrazione

```bash
KIRCHHOFF_PUBLIC_URL=https://andreamarro.github.io/kirchhoff/ \
  npm run test:e2e --prefix web -- fumo-pubblico
```

Atteso: 2 test verdi per progetto (desktop + mobile): 3 successi con
risposte `3/80`, `6/325`, `87/425`, rifiuto «Non certificata», zero errori
di pagina, cornice ospite con tastiera confinata e tema.

## 6. Guscio ospite contro il pubblicato

```bash
KIRCHHOFF_WORKBENCH_URL=https://andreamarro.github.io/kirchhoff/ \
  npm run test:e2e --prefix web -- site-host
```

Atteso: 8 verdi per progetto. Prova il guscio reale (`web/site-host/`)
puntato al pubblicato: copia, cornice, CTA schermo intero, tastiera,
trasporto, tablet, mobile.

## 7. Solo ora: collegare dal sito e ritirare il percorso manuale

1. Collegare la pagina del sito al canonico (fuori da questo repository):
   default cornice B + «Apri a schermo intero» (vedi
   `web/site-host/README.md` e `web/site-host/copy-it.md`).
2. Ritirare il vecchio percorso manuale `origin/gh-pages` (build statica
   ferma a `f24e4a8`, precedente alle Pages automatiche):

```bash
git fetch origin
git log --oneline origin/gh-pages -1   # annotare: ultimo noto buono manuale
git push origin --delete gh-pages
```

Solo dopo i passi 3–6 verdi. Se i passi 3–6 sono rossi, il ramo manuale
resta come ultima rete (vedi rollback) e il sito non si tocca.

## Rollback — se il deploy automatico è rotto

Risposte alle tre domande, in ordine:

**Qual è l'ultimo artefatto buono noto?**
L'ultimo deploy verde registrato:

```bash
gh run list --workflow=deploy-workbench.yml --branch main --limit 5
# ultimo RUN_ID verde = ultimo buono; lo SHA pubblicato e' nello stesso run
```

Rete secondaria (solo se il passo 7.2 non e' ancora avvenuto):
`origin/gh-pages` come era prima del ritiro.

**Come lo si ripristina?**
Via codice, mai a mano sul hosting: revert del merge su `main`, che
riattiva il workflow e ripubblica il precedente stato buono.

```bash
git fetch origin
git revert -m 1 <FINAL_MAIN_SHA>   # annulla il merge di PR #15
git push origin main
gh run watch <NUOVO_RUN_ID> --exit-status
node web/scripts/smoke-public.mjs https://andreamarro.github.io/kirchhoff/
```

**Come si evita che un'integrazione rotta resti collegata dal sito?**
Il sito si collega solo dopo il passo 6 verde (mai prima, mai «intanto»).
Se il rotto e' gia' collegato: togliere il link/cornice dalla pagina del
sito (un commit fuori da questo repository) e verificare con
`smoke-public.mjs` che il canonico torni buono prima di ricollegare.
Nessuna nuova piattaforma di deploy: solo revert + Pages automatico.

## Evidenza da conservare (ricevuta post-merge)

`FINAL_MAIN_SHA`, `RUN_ID` verde, uscite di `verify-artifacts.mjs`,
`smoke-public.mjs`, `fumo-pubblico` e `site-host` contro il pubblicato,
data/ora. Senza questi cinque, il lancio non e' dichiarato.
