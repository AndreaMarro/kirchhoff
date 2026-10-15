#!/usr/bin/env node
/* Confronta tutti i file della build attesa con quelli serviti alla base
   esplicita: HTML esatto, tutti assets/chunk/worker, lessons, MCP e sessions.
   Non prova l'assenza di file remoti extra non referenziati né una firma H3.
   Uso: node web/scripts/verify-artifacts.mjs BASE_URL [DIR_BUILD_ATTESA]
   Default directory: web/dist. Non esegue build, deploy o richieste implicite. */
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { baseDaArgomento, leggiIndice, urlFile, validaVista } from "./artifact-contract.mjs";
const qui = dirname(fileURLToPath(import.meta.url));
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
let differenze = 0;
function riga(ok, nome, dettaglio = "") {
  console.log(`${ok ? "MATCH" : "DIFF "}  ${nome}${dettaglio ? " — " + dettaglio : ""}`);
  if (!ok) differenze++;
}
async function elenco(directory, prefix = "") {
  const result = [];
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const rel = prefix + item.name;
    if (item.isDirectory()) result.push(...await elenco(join(directory, item.name), rel + "/"));
    else if (item.isFile()) result.push(rel);
    else throw new Error("build attesa con entry non regolare: " + rel);
  }
  return result.sort();
}
async function main() {
  const base = baseDaArgomento(process.argv[2]);
  const dist = resolve(process.argv[3] ?? join(qui, "..", "dist"));
  const files = await elenco(dist);
  if (!files.includes("index.html")) throw new Error("build attesa senza index.html");
  const cache = new Map();
  async function remoto(rel) {
    if (!cache.has(rel)) {
      const url = urlFile(base, rel);
      const res = await fetch(url, { redirect: "follow", signal: AbortSignal.timeout(15_000) });
      if (!res.ok) throw new Error(`${url} -> ${res.status}`);
      cache.set(rel, Buffer.from(await res.arrayBuffer()));
    }
    return cache.get(rel);
  }
  // HTML senza normalizzazione: un nuovo nome di asset è già una differenza.
  // Si confrontano anche tutti i file non indicati direttamente nell'HTML.
  for (const file of files) {
    try {
      const [locale, servito] = await Promise.all([readFile(join(dist, file)), remoto(file)]);
      riga(locale.equals(servito), file, `atteso ${sha(locale)} / servito ${sha(servito)}`);
    } catch (error) { riga(false, file, String(error)); }
  }
  try {
    const locale = leggiIndice(JSON.parse(await readFile(join(dist, "sessions/index.json"), "utf8")));
    const servito = leggiIndice(JSON.parse((await remoto("sessions/index.json")).toString("utf8")));
    if (JSON.stringify(locale) !== JSON.stringify(servito)) throw new Error("indice locale/remoto differente");
    const corpi = files.filter(f => f.startsWith("sessions/") && f.endsWith(".json") && f !== "sessions/index.json");
    const attesi = locale.map(v => `sessions/${v.id}.json`).sort();
    if (JSON.stringify(corpi.sort()) !== JSON.stringify(attesi)) throw new Error("indice/file locali disallineati o orfani");
    for (const voce of locale) {
      const file = `sessions/${voce.id}.json`;
      try {
        validaVista(JSON.parse(await readFile(join(dist, file), "utf8")), voce);
        validaVista(JSON.parse((await remoto(file)).toString("utf8")), voce);
      } catch (error) { riga(false, file, String(error)); }
    }
  } catch (error) { riga(false, "indice/catalogo", String(error)); }
}
try { await main(); } catch (error) { riga(false, "argomenti/build", String(error)); }
console.log(differenze ? `VERIFICA ARTEFATTI: ${differenze} DIFFERENZE` : "VERIFICA ARTEFATTI: OK");
process.exitCode = differenze ? 1 : 0;
