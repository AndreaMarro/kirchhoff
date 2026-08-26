// Il gate che nessun test della suite dava: i byte diventano un DISEGNO?
//
// La suite verifica che `render` emetta certi byte, e che quei byte siano XML
// ben formato. Nessuno verificava che un browser, ricevendoli, disegni qualcosa:
// un SVG puo' essere valido, deterministico, semanticamente annotato — e non
// dipingere un pixel, perche' il viewBox esclude il contenuto o perche' ogni
// tratto e' largo zero. Sono difetti che la riparsatura della Story 1.6 non
// vedrebbe: lei rilegge la struttura, non l'immagine.
//
// **Cosa questo cancello NON copre, misurato.** Con `stroke-width="0"` sulla
// radice tutti i fili spariscono e il gate resta VERDE: pallini ed etichette
// hanno un `fill` proprio e continuano a dipingere 627 pixel, sopra la soglia.
// Cattura «non disegna niente», non «disegna meta'». Una soglia calibrata su un
// riferimento lo coprirebbe, al prezzo di un cancello che diventa rosso a ogni
// ritocco legittimo del disegno — e un cancello che grida sempre viene spento.
// Dichiararlo qui vale piu' che lasciar credere che copra tutto.
import { chromium } from 'playwright';
import { readFileSync, readdirSync, existsSync } from 'fs';

const file = process.argv[2];
if (!file) { console.error('uso: node gate.mjs <file.svg>'); process.exit(64); }
const svg = readFileSync(file, 'utf8');

// Il browser si prende da quelli GIA' sul disco. Playwright pretende una
// versione esatta e scaricherebbe: qui il gate deve poter girare su una macchina
// senza rete, e un cancello che dipende da un download e' un cancello che un
// giorno non gira.
const trovato = process.env.KIRCHHOFF_CHROME || (() => {
  const base = process.env.HOME + '/Library/Caches/ms-playwright';
  for (const d of readdirSync(base).filter(x => x.startsWith('chromium_headless_shell')).sort().reverse()) {
    const p = `${base}/${d}/chrome-headless-shell-mac-arm64/chrome-headless-shell`;
    if (existsSync(p)) return p;
  }
  return null;
})();
if (!trovato) { console.error('  nessun chromium sul disco: `npx playwright install chromium-headless-shell`'); process.exit(69); }
const browser = await chromium.launch({ executablePath: trovato });
const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
await page.setContent(`<!doctype html><body style="margin:0;background:#fff">${svg}</body>`);

const esiti = [];
const dice = (nome, ok, dettaglio) => esiti.push({ nome, ok, dettaglio });

// 1. il disegno occupa spazio reale
const box = await page.locator('svg').boundingBox();
dice('il disegno ha un riquadro non degenere',
     !!box && box.width > 10 && box.height > 10,
     box ? `${Math.round(box.width)}x${Math.round(box.height)}` : 'nessun riquadro');

// 2. ogni elemento disegnato e' DENTRO il viewBox
const fuori = await page.evaluate(() => {
  const r = document.querySelector('svg').getBoundingClientRect();
  return [...document.querySelectorAll('svg line, svg rect, svg circle, svg polyline')]
    .filter(e => { const b = e.getBoundingClientRect();
      return b.right < r.left - 1 || b.left > r.right + 1 ||
             b.bottom < r.top - 1 || b.top > r.bottom + 1; })
    .map(e => e.tagName + (e.getAttribute('data-component-id') || e.getAttribute('data-node-id') || ''));
});
dice('nessun elemento cade fuori dal viewBox', fuori.length === 0,
     fuori.length ? fuori.slice(0,4).join(', ') : 'tutti dentro');

// 3. gli attributi semantici sono interrogabili nel DOM, non solo nel testo
const sem = await page.evaluate(() => ({
  componenti: document.querySelectorAll('[data-component-id]').length,
  nodi: document.querySelectorAll('[data-node-id]').length,
  morsetti: document.querySelectorAll('[data-terminal-node]').length,
}));
dice('gli attributi semantici sono interrogabili',
     sem.componenti > 0 && sem.nodi > 0 && sem.morsetti > 0,
     `${sem.componenti} componenti · ${sem.nodi} nodi · ${sem.morsetti} morsetti`);

// 4. l'alternativa testuale e' collegata alla radice, non solo presente
const a11y = await page.evaluate(() => {
  const s = document.querySelector('svg');
  const t = s.getAttribute('aria-labelledby'), d = s.getAttribute('aria-describedby');
  return { ruolo: s.getAttribute('role'),
           titolo: t ? !!document.getElementById(t) : false,
           desc: d ? (document.getElementById(d)?.textContent || '').length : 0 };
});
dice('la radice dichiara ruolo, titolo e descrizione risolvibili',
     a11y.ruolo === 'img' && a11y.titolo && a11y.desc > 40,
     `role=${a11y.ruolo} titolo=${a11y.titolo} desc=${a11y.desc} caratteri`);

// 5. dipinge davvero: qualcosa di non bianco finisce sui pixel
const png = await page.screenshot();
const nonBianchi = await page.evaluate(async () => {
  const s = new XMLSerializer().serializeToString(document.querySelector('svg'));
  const img = new Image();
  await new Promise(r => { img.onload = r; img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(s))); });
  const c = document.createElement('canvas');
  c.width = img.width || 900; c.height = img.height || 700;
  const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0,0,c.width,c.height);
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0,0,c.width,c.height).data;
  let n = 0;
  for (let i = 0; i < d.length; i += 4) if (d[i] < 250 || d[i+1] < 250 || d[i+2] < 250) n++;
  return n;
});
dice('dipinge pixel non bianchi', nonBianchi > 200, `${nonBianchi} pixel`);

await browser.close();

let rossi = 0;
for (const e of esiti) {
  console.log(`  ${e.ok ? '[ok]' : '[NO]'}  ${e.nome} — ${e.dettaglio}`);
  if (!e.ok) rossi++;
}
console.log(rossi === 0 ? '\n  vista: verde' : `\n  vista: ${rossi} controlli rossi`);
process.exit(rossi === 0 ? 0 : 1);
