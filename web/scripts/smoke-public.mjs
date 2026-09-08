#!/usr/bin/env node
/* Fumo pubblico post-deploy: la produzione risponde e dice il vero minimo.
   Solo HTTP + JSON, niente browser: homepage, asset JS/CSS, indice esercizi,
   3 sessioni di successo + 1 rifiuto, nessun HTTP >= 400.
   Uso: node web/scripts/smoke-public.mjs [baseUrl]
   Default: https://andreamarro.github.io/kirchhoff/
   Esce 0 se tutto passa, 1 altrimenti. Non e' la suite completa: fumo, non CI. */
const base = (process.argv[2] ?? "https://andreamarro.github.io/kirchhoff/").replace(/\/?$/, "/");

let fallimenti = 0;
function ok(cond, nome, dettaglio = "") {
  console.log(`${cond ? "PASS" : "FAIL"}  ${nome}${dettaglio ? ` — ${dettaglio}` : ""}`);
  if (!cond) fallimenti += 1;
}

async function prendi(percorso, nome) {
  const url = new URL(percorso, base).toString();
  let res;
  try {
    res = await fetch(url, { redirect: "follow" });
  } catch (e) {
    ok(false, nome, `${url} rete: ${String(e).slice(0, 120)}`);
    return null;
  }
  ok(res.status < 400, nome, `${url} -> ${res.status}`);
  if (res.status >= 400) return null;
  return res;
}

const home = await prendi("", "homepage carica");
let testo = "";
if (home) {
  testo = await home.text();
  ok(testo.includes('id="root"'), "homepage monta il banco", "id=root presente");
  const asset = [...testo.matchAll(/((?:\.\/)?assets\/[A-Za-z0-9._-]+\.(?:js|css))/g)].map((m) => m[1]);
  ok(asset.length >= 2, "asset JS+CSS referenziati", [...new Set(asset)].join(", ") || "nessuno");
  for (const a of new Set(asset)) {
    const r = await prendi(a.replace(/^\.\//, ""), `asset ${a}`);
    if (r) await r.arrayBuffer();
  }
}

const indiceRes = await prendi("sessions/index.json", "indice esercizi");
let indice = [];
if (indiceRes) {
  try {
    indice = await indiceRes.json();
  } catch {
    indice = [];
  }
  ok(Array.isArray(indice) && indice.length === 4, "indice con 4 voci", `trovate ${indice.length}`);
}

const attesi = [
  ["partitore-d1", "closed"],
  ["scala-due-riduzioni", "closed"],
  ["ponte-nodale", "closed"],
  ["rifiuto-reattivo", "refusal"],
];
for (const [id, esito] of attesi) {
  const r = await prendi(`sessions/${id}.json`, `${id} apre (${esito})`);
  if (!r) continue;
  let corpo = null;
  try {
    corpo = await r.json();
  } catch {
    corpo = null;
  }
  ok(corpo?.outcome === esito, `${id} esito onesto`, `outcome=${corpo?.outcome}`);
}

console.log(fallimenti === 0 ? "FUMO PUBBLICO: OK" : `FUMO PUBBLICO: ${fallimenti} FALLIMENTI`);
process.exit(fallimenti === 0 ? 0 : 1);
