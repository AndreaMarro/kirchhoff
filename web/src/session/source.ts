/* Sorgente dati: JSON statici generati dal kernel, mai inventati qui.
   `fetch` su stesso host; nessun backend, nessun account, nessuna rete
   esterna durante l'esperienza. */
import { parseIndex, parseSession } from "./guards.ts";
import type { ExerciseIndexEntry, StudentSessionView } from "./types.ts";

async function getJson(path: string): Promise<unknown> {
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return (await res.json()) as unknown;
}

export async function loadIndex(base = "sessions"): Promise<ExerciseIndexEntry[]> {
  return parseIndex(await getJson(`${base}/index.json`));
}

export async function loadSession(
  id: string,
  base = "sessions",
): Promise<StudentSessionView> {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error(`id esercizio non valido: ${id}`);
  return parseSession(await getJson(`${base}/${id}.json`));
}
