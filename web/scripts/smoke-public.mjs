#!/usr/bin/env node
/* Fumo HTTP esplicito: ingresso/asset diretti e tutte le viste del catalogo
   proof DC. Non esegue il browser, non risolve e non verifica tutta la build.
   Uso: node web/scripts/smoke-public.mjs BASE_URL
   Per byte e chunk dell'intera build usare verify-artifacts.mjs. */
import { baseDaArgomento, leggiIndice, urlFile, validaVista } from "./artifact-contract.mjs";
let fallimenti = 0;
function riga(ok, nome, dettaglio = "") {
  console.log(`${ok ? "PASS" : "FAIL"}  ${nome}${dettaglio ? " — " + dettaglio : ""}`);
  if (!ok) fallimenti++;
}
async function main() {
  const base = baseDaArgomento(process.argv[2]);
  async function prendi(file) {
    const url = urlFile(base, file);
    const res = await fetch(url, { redirect: "follow", signal: AbortSignal.timeout(15_000) });
    if (!res.ok) throw new Error(`${url} -> ${res.status}`);
    return res;
  }
  try {
    const html = await (await prendi("")).text();
    riga(html.includes('id="root"'), "homepage monta l'ingresso");
    const assets = [...new Set([...html.matchAll(/(?:src|href)=["']([^"']+\.(?:js|mjs|css))["']/g)].map(m => m[1]))];
    riga(assets.some(a => /\.(?:m?js)$/.test(a)) && assets.some(a => a.endsWith(".css")), "asset JS/CSS d'ingresso");
    for (const asset of assets) {
      const url = new URL(asset, base);
      try {
        const res = await fetch(url, { redirect: "follow", signal: AbortSignal.timeout(15_000) });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await res.arrayBuffer(); riga(true, "asset " + asset);
      } catch (error) { riga(false, "asset " + asset, String(error)); }
    }
  } catch (error) { riga(false, "homepage", String(error)); }
  let indice;
  try { indice = leggiIndice(await (await prendi("sessions/index.json")).json()); riga(true, "indice esercizi", `${indice.length} voci valide`); }
  catch (error) { riga(false, "indice esercizi", String(error)); return; }
  for (const voce of indice) {
    try { validaVista(await (await prendi(`sessions/${voce.id}.json`)).json(), voce); riga(true, voce.id, voce.outcome); }
    catch (error) { riga(false, voce.id, String(error)); }
  }
}
try { await main(); } catch (error) { riga(false, "argomenti/esecuzione", String(error)); }
console.log(fallimenti ? `FUMO PUBBLICO: ${fallimenti} FALLIMENTI` : "FUMO PUBBLICO: OK");
process.exitCode = fallimenti ? 1 : 0;
