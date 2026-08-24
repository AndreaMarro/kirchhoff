---
name: Kirchhoff
version: 3
description: "Motore di prova visuale. Strumento di precisione portato al livello di cura di Linear o Figma: scuro, denso, veloce. La fiducia si guadagna mostrando il lavoro, non decorandolo."
status: draft
created: 2026-08-13
updated: 2026-08-15
supersedes: "DESIGN v2 (13 ago 2026) — chiaro per default, prodotto centrato sull'Anteprima da foto"
sources:
  - ../../prds/prd-Kirchhoff-2026-08-13/prd.md
  - ../../briefs/brief-Kirchhoff-2026-08-13/brief.md
  - ../../briefs/brief-Kirchhoff-2026-08-13/addendum.md
colors:
  surface-base: '#0F1013'
  surface-raised: '#17191E'
  surface-sunken: '#0A0B0D'
  surface-overlay: '#1F222A'
  ink-primary: '#F2F3F5'
  ink-secondary: '#A6ACB8'
  ink-muted: '#6E747F'
  rule-hairline: '#22252C'
  rule-strong: '#343841'
  verified: '#54D19A'
  verified-surface: '#10241C'
  suspended: '#E0B168'
  suspended-surface: '#241D10'
  fault: '#EE8E72'
  fault-surface: '#2A1713'
  provenance: '#7C9BFF'
  provenance-surface: '#141B31'
  focus-ring: '#7C9BFF'
  surface-base-light: '#FCFCFA'
  surface-raised-light: '#FFFFFF'
  surface-sunken-light: '#F1F1EC'
  surface-overlay-light: '#FFFFFF'
  ink-primary-light: '#16181C'
  ink-secondary-light: '#565C66'
  ink-muted-light: '#878D96'
  rule-hairline-light: '#E3E3DC'
  rule-strong-light: '#C8C8BE'
  verified-light: '#1E6A4A'
  verified-surface-light: '#E7F1EB'
  suspended-light: '#8A6220'
  suspended-surface-light: '#F9F0DF'
  fault-light: '#A6412A'
  fault-surface-light: '#F7E8E3'
  provenance-light: '#2F51BE'
  provenance-surface-light: '#E7ECFA'
  focus-ring-light: '#2F51BE'
motion:
  instant: '90ms'
  quick: '140ms'
  considered: '220ms'
  easing: 'cubic-bezier(0.2, 0, 0, 1)'
  note: "Il movimento esiste per far capire cosa e' cambiato, mai per festeggiare. prefers-reduced-motion rimuove ogni transizione tranne il cambio di stato del passo, che diventa istantaneo."
typography:
  display:
    fontFamily: 'Inter Tight, system-ui, sans-serif'
    fontSize: '28px'
    fontWeight: 600
    lineHeight: '1.2'
    letterSpacing: '-0.01em'
  title:
    fontFamily: 'Inter Tight, system-ui, sans-serif'
    fontSize: '20px'
    fontWeight: 600
    lineHeight: '1.3'
  body:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '16px'
    fontWeight: 400
    lineHeight: '1.55'
  meta:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '13px'
    fontWeight: 400
    lineHeight: '1.4'
  quantity:
    fontFamily: 'JetBrains Mono, ui-monospace, monospace'
    fontSize: '16px'
    fontWeight: 500
    lineHeight: '1.4'
    note: 'Cifre tabulari obbligatorie — font-variant-numeric: tabular-nums'
  residual:
    fontFamily: 'JetBrains Mono, ui-monospace, monospace'
    fontSize: '12px'
    fontWeight: 400
    lineHeight: '1.5'
    note: 'Cifre tabulari. Notazione esponenziale ammessa.'
  label-drawing:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '11px'
    fontWeight: 500
    note: 'Dimensione minima effettiva nei disegni dei circuiti — vincolo FR-15, non preferenza.'
rounded:
  sm: '4px'
  md: '8px'
  lg: '14px'
  full: '9999px'
spacing:
  '1': '4px'
  '2': '8px'
  '3': '12px'
  '4': '16px'
  '5': '24px'
  '6': '32px'
  '7': '48px'
  '8': '64px'
  gutter: '16px'
  margin-mobile: '16px'
  margin-desktop: '32px'
  drawing-inset: '12px'
components:
  badge-verified:
    background: '{colors.verified-surface}'
    foreground: '{colors.verified}'
    border: '1px solid {colors.verified}'
    radius: '{rounded.full}'
    padding: '{spacing.2} {spacing.3}'
    icon: 'segno di spunta dentro un cerchio pieno'
    label: 'Verificata'
    note: 'Icona + etichetta + colore. Mai colore da solo.'
  badge-suspended:
    background: '{colors.suspended-surface}'
    foreground: '{colors.suspended}'
    border: '1px solid {colors.suspended}'
    radius: '{rounded.full}'
    padding: '{spacing.2} {spacing.3}'
    icon: 'cerchio con barra orizzontale'
    label: 'Non certificata'
    note: 'Mai icona di allarme, mai triangolo, mai {colors.fault}.'
  provenance-anchor:
    stroke: '{colors.provenance}'
    fill: '{colors.provenance-surface}'
    strokeWidth: '2px'
    radius: '{rounded.sm}'
    note: "Riquadro sull'immagine sorgente che lega un componente alla sua area di lettura."
  quantity-chip:
    font: '{typography.quantity}'
    background: '{colors.surface-sunken}'
    foreground: '{colors.ink-primary}'
    radius: '{rounded.sm}'
    padding: '{spacing.1} {spacing.2}'
  residual-row:
    font: '{typography.residual}'
    foreground: '{colors.ink-secondary}'
    rule: '1px solid {colors.rule-hairline}'
  step-card:
    background: '{colors.surface-raised}'
    border: '1px solid {colors.rule-hairline}'
    radius: '{rounded.lg}'
    padding: '{spacing.5}'
    gap: '{spacing.4}'
  question-card:
    background: '{colors.surface-raised}'
    border: '2px solid {colors.provenance}'
    radius: '{rounded.lg}'
    padding: '{spacing.5}'
  disclosure-bar:
    background: '{colors.surface-sunken}'
    foreground: '{colors.ink-secondary}'
    font: '{typography.meta}'
    padding: '{spacing.2} {spacing.4}'
    note: 'Persistente. Non chiudibile. Presente su ogni superficie, pannello assistente incluso.'
  subgraph-highlight:
    stroke: '{colors.provenance}'
    strokeWidth: '2px'
    halo: '0 0 0 5px {colors.provenance-surface}'
    scope: 'local'
    note: "Marca SOLO i componenti che cambiano, stretto attorno alla loro sagoma. Compare PRIMA di qualunque testo. Lo scope e' locale per obbligo sperimentale: un fondo colorato esteso dietro il sottografo e' una versione morbida del braccio C e contaminerebbe il confronto A-C."
  boundary-anchor:
    stroke: '{colors.provenance}'
    strokeWidth: '1.4px'
    fill: 'none'
    size: '9px'
    layer: 6
    note: "Overlay effimero ancorato a un nodo di boundary. NON e' il nodo ridisegnato: e' un segno sovrapposto, deliberatamente piu' discreto del segnale sul delta. Togliendolo, il nodo torna identico — perche' non era mai cambiato. Vive nel TransformOverlay, non nel LayoutIR."
  region-highlight:
    fill: '{colors.provenance-surface}'
    radius: '{rounded.lg}'
    arm: 'variabile sperimentale'
    note: "Fondo esteso dietro l'intera regione di trasformazione. NON e' default: se lo si vuole misurare diventa una condizione dichiarata, mai un dettaglio di stile."
  attenuation:
    opacity: '0.38'
    transition: '{motion.quick} {motion.easing}'
    arm: 'C'
    note: "NON e' comportamento di default. Revocato dall'owner il 15 agosto: attenuare i sopravvissuti E' comunque modificarli, e dice 'queste sono le cose che non ci interessano' invece di 'il circuito e' ancora questo'. Esiste SOLO come braccio C dell'esperimento di Gate A, cioe' come pattern comune da battere."
  unchanged-marker:
    stroke: '{colors.ink-muted}'
    strokeWidth: '1px'
    strokeDasharray: '2 3'
    arm: 'B'
    note: "Codifica leggera 'unchanged' sui preservati. Come attenuation, NON e' default: esiste solo come braccio B dell'esperimento. E' l'esatta negazione di A-0, ed e' li' apposta."
  identity-tag:
    font: '{typography.label-drawing}'
    foreground: '{colors.ink-secondary}'
    note: "L'etichetta di un componente o nodo conservato NON cambia trattamento fra un passo e l'altro, e non riceve marcatore. Braccio A, il default."
  beforeafter-toggle:
    background: '{colors.surface-sunken}'
    border: '1px solid {colors.rule-strong}'
    radius: '{rounded.full}'
    padding: '{spacing.1}'
    activeBackground: '{colors.surface-overlay}'
    transition: '{motion.instant} {motion.easing}'
    note: "Due stati, PRIMA e DOPO. Commutazione istantanea e reversibile a volonta': la comprensione nasce dal confronto ripetuto, non da un'animazione vista una volta."
  equation-anchor:
    background: '{colors.surface-raised}'
    border: '1px solid {colors.rule-hairline}'
    radius: '{rounded.md}'
    padding: '{spacing.3}'
    font: '{typography.quantity}'
    note: "L'equazione sta ACCANTO al sottografo che l'ha generata, con una linea di collegamento. Un'equazione staccata dal disegno e' una spiegazione; attaccata, e' una prova."
  certificate-chip:
    background: '{colors.verified-surface}'
    foreground: '{colors.verified}'
    border: '1px solid {colors.verified}'
    radius: '{rounded.sm}'
    padding: '{spacing.1} {spacing.2}'
    font: '{typography.meta}'
    icon: 'segno di spunta dentro un quadrato'
    note: "Il campo CERTIFICATE del passo. Forma quadrata, distinta dal badge-verified che e' tondo: uno certifica il passo, l'altro la soluzione."
  proofgraph-rail:
    background: '{colors.surface-sunken}'
    nodeSize: '{spacing.3}'
    edgeStroke: '{colors.rule-strong}'
    activeNode: '{colors.provenance}'
    note: "La derivazione come grafo percorribile, non come elenco. Sempre visibile: e' il prodotto, non una barra di avanzamento. Supporta diramazione e ricongiungimento anche quando l'MVP produce catene quasi lineari."
---

## Brand & Style

Kirchhoff assomiglia a uno strumento di precisione, non a un'app educativa. È una scelta
argomentata, non un gusto: il prodotto vende il diritto di fidarsi di un numero, e un'estetica
giocosa contraddice quella promessa nel primo secondo di esposizione — prima che l'utente legga
una sola parola.

> **Precisazione v3 — 15 agosto.** La v2 leggeva «strumento» come **sobrietà**. La v3 lo legge come
> **cura estrema**, che non è la stessa cosa. Il requisito è che il prodotto risulti *estremamente
> attraente* per uno studente universitario, e i riferimenti che lo ottengono senza cambiare
> categoria sono **Linear, Arc, Figma**: scuri per default, densi, velocissimi, con una tipografia
> che qualcuno ha scelto davvero e un movimento che serve a capire. Quegli strumenti sono amati da
> un pubblico universitario **perché** sembrano seri, non nonostante. La v2 chiedeva di non essere
> giocosi; la v3 chiede in più di non essere spogli. **Il nemico non è la bellezza: è la
> carineria.**

**Scuro per default, chiaro come alternativa.** Non è una preferenza di gusto: l'uso è
prevalentemente notturno e sotto scadenza, e un disegno di circuito a tratto chiaro su fondo scuro
regge meglio l'attenzione prolungata. Il tema chiaro resta pari grado e completo — è il tema della
stampa e delle aule illuminate — ma i valori senza suffisso sono lo scuro.

Il riferimento mentale è il banco di laboratorio con la strumentazione moderna: superfici neutre,
cifre allineate, nessuna decorazione che competa con i dati, e un solo colore che porti significato
per volta. Il riferimento **anti**-mentale è l'edtech consumer — gradienti, illustrazioni di
personaggi, coriandoli alla soluzione corretta, contatori di serie. Ogni elemento di quel
vocabolario sposterebbe il prodotto nella categoria da cui deve distinguersi.

La regola che governa tutto il resto: **il prodotto mostra il lavoro invece di affermarlo**. Un
badge verde che dice "Verificata" è esattamente ciò che un chatbot potrebbe disegnare senza avere
nessun gate sotto. Quello che un chatbot non può disegnare sono i residui numerici di cinque
controlli, ispezionabili. Il design deve quindi rendere l'ispezione a un tocco di distanza, non
nasconderla in un menu.

## Colors

La palette è quasi acromatica, e i tre colori portanti hanno ciascuno un solo mestiere. Se un
colore ne assume due, ha smesso di comunicare.

> **v3: i valori senza suffisso sono lo scuro.** Le coppie citate qui sotto vanno lette come
> *scuro (default) / chiaro (`-light`)*. La retinatura è stata rialzata per il fondo scuro: i tre
> colori portanti sono più luminosi e meno saturi di prima, perché su `#0F1013` un verde profondo
> smette di leggersi. I mestieri non cambiano.

- **Verificato (`#54D19A` scuro / `#1E6A4A` chiaro)** — verde profondo, non brillante. Compare
  **solo** sul Badge Verificata e sui residui che passano. Non è un colore di successo generico:
  non si usa per conferme, salvataggi, o pulsanti primari. Se comparisse su un pulsante,
  diluirebbe l'unico significato che deve portare.
- **Sospeso (`#8A6220` chiaro / ambra chiara scuro)** — il colore del **Rifiuto di
  certificazione**. Deliberatamente **non rosso**. Il rosso comunica "hai sbagliato tu"; il
  Rifiuto è il sistema che è onesto sul proprio limite, ed è un esito progettato, non un errore
  dell'utente. L'ambra dice "sospeso, non concluso" — che è letteralmente lo stato.
- **Guasto (`#A6412A`)** — riservato ai fallimenti veri: upload non riuscito, servizio non
  raggiungibile, sessione scaduta. **Non appare mai in relazione alla Verifica.** Tenerlo
  separato dal Sospeso è ciò che rende leggibile la differenza fra "il sistema è rotto" e "il
  sistema sta funzionando e te lo sta dicendo".
- **Provenienza (`#2F51BE`)** — il blu che lega un componente ricostruito alla sua area
  sull'immagine sorgente, e che incornicia le Domande mirate. È il colore dell'attenzione
  richiesta, non del pericolo.

Superfici e inchiostri sono neutri freddi nello scuro e neutri caldi nel chiaro. **La modalità
scura è il default**, non un tema alternativo: gran parte dell'uso avviene di notte, sotto
scadenza, e il tratto chiaro su fondo scuro regge meglio l'attenzione prolungata su un disegno.

**Da evitare:** gradienti su qualunque superficie; verde e rosso come unico canale di
distinzione; colori saturi nei disegni dei circuiti — il disegno è **`{colors.ink-primary}` su
`{colors.surface-base}`**, più `{colors.provenance}` per il sottografo in trasformazione, e
nient'altro. Il circuito non è un'illustrazione: ogni colore in più è un'informazione che qualcuno
dovrà decodificare mentre sta cercando di capire cosa è cambiato.

## Typography

Due famiglie, e la seconda esiste per una ragione funzionale precisa.

**Sans (Inter / Inter Tight)** per tutto il testo. Inter Tight nei titoli per compattare le righe
lunghe su schermo telefono.

**Mono a cifre tabulari (JetBrains Mono)** per ogni quantità fisica, ogni valore di componente e
ogni residuo di verifica. Non è un vezzo da terminale: i residui dei cinque controlli si leggono
in colonna, e **si confrontano a colpo d'occhio solo se le cifre sono allineate**. Con cifre
proporzionali, `1,4e-13` e `8,2e-04` occupano larghezze diverse e l'ordine di grandezza smette di
essere visibile nella forma. Questo vale anche dentro i disegni.

`{typography.label-drawing}` a 11 px è un **vincolo, non una preferenza**: viene da FR-15, dove le
etichette dei componenti devono restare leggibili a 360 px di viewport. Un disegno che per stare
nello schermo scende sotto quella soglia va rimpicciolito nella topologia, non nel testo.

Le formule sono composte come matematica, non come testo con simboli: frazioni impilate, indici
in posizione, `Ω`, `μ` e `∥` come glifi veri.

## Layout & Spacing

Scala da 4 px. `{spacing.4}` è il ritmo di default fra elementi correlati; `{spacing.6}` separa
blocchi concettuali; `{spacing.7}` separa le sezioni di una soluzione.

**Mobile-first senza compromessi**, perché il momento d'uso primario è un telefono in mano alle
23:40. Colonna singola sotto 768 px. Il vincolo duro è FR-15: a 360 px il disegno del circuito
resta interamente visibile senza che la pagina scorra in orizzontale. Se un disegno non ci sta, la
soluzione è ridisegnarlo con un layout più compatto, **non** metterlo in un contenitore che scorre
lateralmente — uno schema che si trascina di lato non si legge come schema.

Sopra 768 px l'Anteprima passa a due colonne affiancate (foto sorgente | ricostruzione), che è la
disposizione che rende immediato il confronto. Sotto, le due viste si alternano con un controllo a
due stati, mai in accordion: un accordion nasconde metà del confronto proprio mentre serve.

Studio (B2B) è l'unica superficie pensata per desktop: densità maggiore, tabelle di Varianti,
`{spacing.3}` come ritmo di default.

## Elevation & Depth

Elevazione quasi assente. La gerarchia è portata da regole sottili (`{colors.rule-hairline}`) e
da cambi di superficie, non da ombre: le ombre suggeriscono materiale morbido e questo prodotto
deve sembrare strumentazione.

Due sole eccezioni, entrambe in cui un elemento è realmente sopra il flusso: la Domanda mirata
quando compare in overlay su mobile, e il pannello dei residui quando si apre. Ombra singola,
diffusa, senza colore.

Il pannello dei residui usa `{colors.surface-sunken}` — è *dentro* il documento, non sopra: è la
prova, non un avviso.

## Shapes

Raggi contenuti. `{rounded.sm}` su chip e riquadri di provenienza, `{rounded.md}` su controlli,
`{rounded.lg}` su card di passo e di domanda. `{rounded.full}` **solo** sui due badge di stato —
la forma a pillola li distingue da qualunque altro elemento della pagina anche senza colore, che
è il punto.

Nessun cerchio decorativo, nessuna forma organica. I disegni dei circuiti sono ortogonali:
segmenti orizzontali e verticali, angoli vivi, nessuna curva di raccordo.

## Continuità visuale

Sezione inventata. Nessuna sezione canonica nomina il concern centrale di questo prodotto: **cosa
deve restare identico quando il circuito cambia.** È la superficie su cui Gate A emette il verdetto,
quindi è materia di design, non di implementazione.

### A-0 — Unmarked Preservation Hypothesis

> Un'entità preservata **non riceve una modifica del proprio visual state per comunicare la
> trasformazione**. Colore, movimento, evidenziazione, comparsa e scomparsa appartengono
> **esclusivamente al sottografo trasformato**. Se un'entità preservata appartiene **anche** al
> boundary della trasformazione, il boundary può essere rappresentato da un **overlay effimero e
> indipendente**, ancorato geometricamente all'entità, **senza modificare il rendering dell'entità
> sottostante**.

**Preservato e boundary sono due proprietà diverse.** Per `R3 ∥ R4 → R34` fra `A` e `B`, valgono
insieme `A, B ∈ Pₖ` e `∂Tₖ = {A, B}`. Non si dipinge il nodo di blu: si appoggia un
`boundary-anchor` sopra di esso. **Togliendo l'overlay, `A` torna identico — perché non era mai
cambiato**, ed è il test che distingue le due implementazioni.

| Elemento | Segnale |
|---|---|
| `R3`, `R4` — il delta | forte: sono ciò che cambia |
| `A`, `B` — preservati **e** boundary | solo `boundary-anchor`, più discreto del segnale sul delta |
| `V1`, `R1` — preservati | **nessuno** |

**L'ordine dei layer è deterministico** — R-Visual-1: *un'annotazione di trasformazione non occlude
mai un'entità semantica preservata.*

`0` sfondo · `1` regione di trasformazione · `2` fili · `3` componenti · **`4` nodi ed etichette
semantiche** · `5` enfasi sul cambiato · `6` annotazioni di boundary · `7` interazione · `8` debug

> Questa gerarchia nasce da un difetto vero: **il primo mock dipingeva l'alone sopra le etichette
> di `A` e `B`**, cioè cancellava i due elementi preservati più importanti del passo. È diventata
> un invariante del renderer con test permanente (PRD FR-53, FR-46), non un aneddoto.

**Il focus è positivo e locale, non negativo e globale.** Non «spengo tutto tranne il fuoco», ma
«accendo solo ciò che cambia». La differenza non è stilistica: attenuare i sopravvissuti comunica
*«queste sono le cose che non ci interessano»*, mentre lasciarli intatti comunica *«il circuito è
ancora questo, guarda solo ciò che sta realmente cambiando»*. È il secondo messaggio che il prodotto
deve dare.

**L'invariante è semantico-spaziale, non pixel-perfect.** «Restano esattamente com'erano» sarebbe
troppo forte: responsive, zoom, viewport, anti-aliasing ed evitamento di collisioni producono
differenze minime e legittime. Vale invece `id_{k+1}(x) = id_k(x)` **senza eccezioni**, e
`p_{k+1}(x) ≈ p_k(x)` con `θ_{k+1}(x) = θ_k(x)` **salvo necessità geometriche dimostrabili**, che
sono comunque **misurate e penalizzate da VCER** — mai assolte come libertà del renderer.

`[ASSUMPTION: A-0 è confermata dall'owner il 15 agosto come regola progettuale madre, ed
esplicitamente **non** come legge percettiva dimostrata. Gate A la confronta contro un braccio a
invarianti marcati (B) e uno conventional-focus (C). Vincere «perché sembra più pulita» non basta:
deve vincere sulla continuità mentale del circuito. Vedi PRD §7.0.1.]`

**Quattro classi di stato, e solo la prima è vincolata.** Un invariante **può** cambiare aspetto;
quello che non può è cambiarlo *perché è avvenuta una trasformazione*.

| Classe | Esempi | Vincolata da A-0 |
|---|---|---|
| Stato semantico di trasformazione | il delta di `Cₖ → Cₖ₊₁` | **sì** |
| Stato di interazione | selezione, hover, focus, ispezione del certificato, «mostrami cosa è rimasto uguale» | no |
| Stato di accessibilità | alto contrasto, evidenziazione da lettore di schermo | no |
| Stato di ispezione/debug | modalità diagnostica, sovrapposizione delle misure | no |

Senza questa separazione A-0 sarebbe inapplicabile: vieterebbe anche l'hover su una resistenza
conservata. Pan e zoom della viewport non appartengono a nessuna classe — trasformano la vista, non
il circuito.

### La sequenza di un passaggio

Tre cose, in ordine di comparsa. **Non quattro: l'attenuazione è uscita.**

1. **I componenti che cambiano** ricevono `subgraph-highlight`, stretto attorno alla loro sagoma; i
   nodi di boundary ricevono un `boundary-anchor` sovrapposto. Compare **prima di qualunque testo**.
   **Nessun fondo colorato esteso**: `region-highlight` non è default, è una variabile sperimentale.
2. **L'equazione** compare in `equation-anchor` accanto al sottografo, collegata da una linea. Non
   sotto il disegno, non in un pannello laterale: **accanto a ciò che l'ha generata.**
3. **Il certificato** in `certificate-chip`. Quadrato, per non confondersi col badge tondo della
   soluzione.

**Il resto del circuito non compare in questa lista, ed è il punto.** Non si attenua, non si
ricompone, non si sposta. Non gli succede niente.

**Identità persistente.** `A` resta `A`, `R1` resta `R1`. Le entità che devono sopravvivere non le
sceglie il renderer: derivano da `Pₖ = Entities(Cₖ) ∩ Entities(Cₖ₊₁)` (PRD FR-47), e il renderer
**non ha una funzione per proporne di proprie**. Il design non ha voce su quali, solo su come
restano riconoscibili — che in braccio A significa: non facendo nulla.

**Il vincolo che protegge l'esperimento.** Il protocollo di Gate A confronta due rendering dello
stesso passaggio: layout persistente contro ri-layout indipendente. **I due bracci usano gli stessi
identici token** — stessa palette, stessa tipografia, stesso peso di tratto, stesse spaziature. Una
differenza estetica fra i bracci è un difetto dell'esperimento, non un risultato: renderebbe
impossibile distinguere «ho capito meglio» da «era più bello». Questo è il vincolo di design più
importante del documento, ed è l'unico che non ammette eccezioni per gusto.

## Components

**`badge-verified`** — pillola con segno di spunta in cerchio pieno, etichetta "Verificata",
`{colors.verified}` su `{colors.verified-surface}`. **Sempre e solo tre canali insieme: forma,
etichetta testuale, colore.** Toccabile: apre il pannello dei residui. Un badge che non si può
aprire è un'affermazione; uno che si apre è una prova.

**`badge-suspended`** — pillola con cerchio barrato, etichetta "Non certificata",
`{colors.suspended}`. Stessa dimensione e stessa posizione del badge verificato, così la
differenza si legge nella forma dell'icona e nel testo prima che nel colore. Nessun triangolo di
avvertimento, nessuna icona di allarme.

**`provenance-anchor`** — riquadro `{colors.provenance}` a 2 px sull'immagine sorgente. Compare
in tre momenti: al passaggio sopra un componente della ricostruzione, quando una Domanda mirata
riguarda quel componente, e quando l'utente tocca un valore nella soluzione per chiedersi da dove
venga. È il legame fisico fra ciò che il sistema dice e ciò che ha visto.

**`quantity-chip`** — ogni valore di componente reso in `{typography.quantity}` su
`{colors.surface-sunken}`. Rende i numeri toccabili e visivamente separati dalla prosa che li
circonda.

**`residual-row`** — riga del pannello dei residui: nome del controllo, valore, esito. Cifre
tabulari, `{typography.residual}`. Cinque righe, sempre le stesse cinque, sempre nello stesso
ordine — la costanza è ciò che rende il pannello leggibile a colpo d'occhio dalla seconda volta
in poi.

**`step-card`** — un passo del Piano didattico: nome della Trasformazione, formula letterale,
sostituzione numerica, disegno del circuito risultante. Il disegno non è un allegato del passo:
è metà del passo.

**`question-card`** — la Domanda mirata. Bordo `{colors.provenance}` a 2 px, ritaglio ingrandito
dell'immagine in cima, alternative sotto come scelte grandi e distinte, campo libero sempre
presente in coda.

**`disclosure-bar`** — la dichiarazione d'uso dell'IA (FR-29). Persistente, non chiudibile,
presente su ogni superficie compreso il pannello assistente. Discreta ma non nascosta: usa
`{typography.meta}` e `{colors.ink-secondary}`, mai `{colors.ink-muted}` — che sarebbe conformità
solo formale.

## Do's and Don'ts

**Fai**

- Mostra i residui a un tocco dal badge. La prova è il prodotto.
- Tieni identiche forma e posizione dei due badge di stato: la differenza deve leggersi anche in
  scala di grigi.
- Ancóra ogni valore alla sua area di provenienza sull'immagine sorgente.
- Usa cifre tabulari ovunque compaia un numero, disegni inclusi.
- Dichiara i limiti nel prodotto con lo stesso peso tipografico delle capacità.

**Non fare**

- **Non usare il rosso per il Rifiuto di certificazione.** È l'errore di design che smonta il
  posizionamento: trasforma un atto di onestà in un fallimento percepito.
- Non far portare al colore da solo lo stato di verifica, mai.
- Non aggiungere celebrazione alla soluzione corretta — niente coriandoli, niente animazioni di
  successo. La soluzione corretta è la norma, non un evento.
- Non usare `{colors.verified}` per pulsanti, conferme o salvataggi: perderebbe il suo unico
  significato.
- Non mettere un disegno di circuito in un contenitore a scorrimento orizzontale.
- Non introdurre serie, punteggi, livelli o classifiche: oltre a essere fuori posizionamento,
  qualunque punteggio attribuito a una persona è il confine che il prodotto non attraversa.
- Non nascondere la barra di dichiarazione dietro un'interazione.

**Aggiunte v3 — la continuità**

- **Non fare:** attenuare ciò che non cambia. **Non fare** nemmeno rimuoverlo, ricomporlo o
  spostarlo. Un circuito che si riorganizza attorno alla trasformazione fallisce l'unica cosa che
  Gate A misura — e uno che si spegne attorno alla trasformazione dice all'utente che il resto non
  conta, che è il contrario del messaggio.
  > **Questa riga diceva l'opposto fino al 15 agosto.** L'attenuazione al 38% era comportamento di
  > default; l'owner l'ha revocata perché attenuare i sopravvissuti è comunque modificarli.
  > Sopravvive come **braccio C** dell'esperimento di Gate A, cioè come il pattern comune da
  > battere.
- **Fai:** metti l'equazione accanto al sottografo che l'ha generata. **Non fare:** relegarla a un
  pannello sotto il disegno — lì torna a essere una spiegazione invece di una prova.
- **Fai:** mostra il sottografo evidenziato **prima** del testo. **Non fare:** aprire un passo con
  un paragrafo. L'utente deve vedere dove accade il ragionamento, non leggerlo.
- **Non fare:** marcare le entità conservate. La continuità si comunica non facendo nulla; un badge
  «invariato» trasforma in evento ciò che deve poter essere dato per scontato.
- **Non fare (mai):** differenziare esteticamente i due bracci dell'esperimento di Gate A. Stessi
  token, stesso renderer, stessi vincoli. È il vincolo che rende il verdetto interpretabile, e non
  ha eccezioni.
- **Non fare:** usare il movimento per festeggiare. `{motion.quick}` serve a legare due stati del
  circuito; oltre `{motion.considered}` l'animazione smette di aiutare e comincia a far aspettare.

