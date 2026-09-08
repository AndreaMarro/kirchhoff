#!/usr/bin/env node
/* Verifica degli artefatti di deploy: il pubblicato corrisponde alla main?
   Confronta index.html, asset JS/CSS referenziati e JSON di sessione fra la
   build locale attesa (web/dist, prodotta da main) e l'URL pubblicato.
   E' verifica operativa d'artefatto, NON provenienza crittografica (H3 resta
   differito): dice "il deploy e' quello giusto", non "chi l'ha firmato".
   Uso: npm run build --prefix web && node web/scripts/verify-artifacts.mjs [baseUrl]
   Esce 0 se ogni artefatto coincide (sha256), 1 altrimenti. */
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const qui = dirname(fileURLToPath(import.meta.url));
const dist = resolve(qui, "..", "dist");
const base = (process.argv[2] ?? "https://andreamarro.github.io/kirchhoff/").replace(/\/?$/, "/");

function sha(buf) {
  return createHash("sha256").update(buf).digest("hex").slice(0, 16);
}

let fallimenti = 0;
function riga(cond, nome, dettaglio = "") {
  console.log(`${cond ? "MATCH" : "DIFF "}  ${nome}${dettaglio ? ` — ${dettaglio}` : ""}`);
  if (!cond) fallimenti += 1;
}

if (!existsSync(join(dist, "index.html"))) {
  console.log("DIFF   build locale assente — esegui prima: npm run build --prefix web");
  process.exit(1);
}

async function locale(rel) {
  return readFile(join(dist, rel));
}
async function remoto(rel) {
  const url = new URL(rel, base).toString();
  const res = await fetch(url, { redirect: "follow" });
  if (res.status >= 400) throw new Error(`${url} -> ${res.status}`);
  return Buffer.from(await res.arrayBuffer());
}

// index.html: normalizza gli asset con hash (il nome cambia a ogni build)
// confrontando la struttura, poi confronta byte dei file puntati.
const idxLocale = (await locale("index.html")).toString("utf8");
let idxRemoto;
try {
  idxRemoto = (await remoto("index.html")).toString("utf8");
} catch (e) {
  riga(false, "index.html", String(e).slice(0, 140));
  console.log(`VERIFICA ARTEFATTI: ${fallimenti} DIFFERENZE`);
  process.exit(1);
}
const normalizza = (s) => s.replace(/index-[A-Za-z0-9_-]+\.(js|css)/g, "index.HASH.$1");
riga(normalizza(idxLocale) === normalizza(idxRemoto), "index.html (struttura)");

const asset = [...new Set([...idxLocale.matchAll(/(\.\/)?assets\/(index-[A-Za-z0-9_-]+\.(?:js|css))/g)].map((m) => `assets/${m[2]}`))];
for (const a of asset) {
  try {
    const [l, r] = await Promise.all([locale(a), remoto(a)]);
    riga(sha(l) === sha(r), a, `locale ${sha(l)} / remoto ${sha(r)}`);
  } catch (e) {
    riga(false, a, String(e).slice(0, 140));
  }
}

const sessions = ["sessions/index.json", "sessions/partitore-d1.json", "sessions/scala-due-riduzioni.json", "sessions/ponte-nodale.json", "sessions/rifiuto-reattivo.json"];
for (const s of sessions) {
  try {
    const [l, r] = await Promise.all([locale(s), remoto(s)]);
    riga(sha(l) === sha(r), s, `locale ${sha(l)} / remoto ${sha(r)}`);
  } catch (e) {
    riga(false, s, String(e).slice(0, 140));
  }
}

console.log(fallimenti === 0 ? "VERIFICA ARTEFATTI: OK" : `VERIFICA ARTEFATTI: ${fallimenti} DIFFERENZE`);
process.exit(fallimenti === 0 ? 0 : 1);
