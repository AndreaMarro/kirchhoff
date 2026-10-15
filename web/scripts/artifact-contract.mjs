/* Contratto operativo del catalogo statico proof DC, non un secondo solver
   né una firma H3. I guard del browser e il kernel restano le autorità. */
export function baseDaArgomento(raw) {
  if (!raw?.trim()) throw new Error("URL base esplicito richiesto (http/https).");
  const base = new URL(raw);
  if (!["http:", "https:"].includes(base.protocol)) throw new Error("URL base non http/https.");
  base.search = "";
  base.hash = "";
  if (!base.pathname.endsWith("/")) base.pathname += "/";
  return base;
}
export function urlFile(base, file) {
  return new URL(file.split("/").map(encodeURIComponent).join("/"), base);
}
const testo = v => typeof v === "string" && v.trim().length > 0;
const oggetto = v => v !== null && typeof v === "object" && !Array.isArray(v);
const stringhe = v => Array.isArray(v) && v.length > 0 && v.every(testo);
function esigi(condizione, causa) { if (!condizione) throw new Error(causa); }
export function leggiIndice(raw) {
  esigi(Array.isArray(raw) && raw.length > 0, "indice vuoto o non array");
  const ids = new Set();
  for (const voce of raw) {
    esigi(oggetto(voce) && testo(voce.id) && !/[\/\?#]/.test(voce.id) && ![".", ".."].includes(voce.id), "indice: identificatore/file non valido");
    esigi(!ids.has(voce.id), "indice: identificatore duplicato " + voce.id);
    ids.add(voce.id);
    esigi(testo(voce.titolo) && ["closed", "refusal"].includes(voce.outcome), "indice: titolo/esito non valido (profilo operativo: closed/refusal, ogni failure è un guasto)");
    esigi(oggetto(voce.domanda) && testo(voce.domanda.quantity) && testo(voce.domanda.target), "indice: domanda assente");
  }
  return raw;
}
function razionale(raw) {
  if (typeof raw !== "string" || !/^[+-]?\d+(?:\/\d+)?$/.test(raw.trim())) return false;
  const parti = raw.trim().split("/");
  return parti.length === 1 || BigInt(parti[1]) !== 0n;
}
export function validaVista(vista, voce) {
  esigi(oggetto(vista) && vista.schema_version === "student-session.v0.1", "schema vista non riconosciuto");
  esigi(vista.outcome === voce.outcome, "esito diverso dall'indice");
  esigi(oggetto(vista.question) && vista.question.quantity === voce.domanda.quantity && vista.question.target === voce.domanda.target, "domanda diversa dall'indice");
  esigi(oggetto(vista.truth) && vista.truth.product_verified === false, "truth/product_verified incoerente");
  esigi(oggetto(vista.provenance) && /^[0-9a-f]{40}$/.test(vista.provenance.source_sha ?? "") && testo(vista.provenance.producer), "provenienza dichiarata assente");
  esigi(["closed", "refusal"].includes(vista.outcome), "profilo operativo: ogni failure è un guasto, non un catalogo sano");
  if (vista.outcome === "closed") {
    // Questo fumo copre il catalogo proof DC, non le lezioni AC/Laplace dell'API.
    const unita = { current: "ampere", voltage: "volt" }[voce.domanda.quantity];
    esigi(oggetto(vista.answer) && unita && vista.answer.unit === unita && razionale(vista.answer.exact), "risposta esatta/unità DC incoerente");
    esigi(testo(voce.risposta_esatta) && voce.risposta_esatta.trim() === vista.answer.exact.trim() + " " + vista.answer.unit, "risposta diversa dalla risposta dichiarata nell’indice");
    esigi(vista.answer.quantity === voce.domanda.quantity && vista.answer.target === voce.domanda.target, "risposta non riferita alla domanda");
    esigi(vista.truth.electrical_claim_status === "VERIFIED" && vista.truth.backend_closure_status === "CLOSED", "chiusura/truth incoerente");
    const verifica = vista.verification;
    esigi(oggetto(verifica) && verifica.claim_status === "VERIFIED" && verifica.session_status === "CLOSED" && testo(verifica.claim_verifier) && testo(verifica.claim_version) && stringhe(verifica.evidence_ids) && stringhe(verifica.claim_subjects), "evidenza della chiusura assente");
    esigi(vista.refusal === null && vista.failure === null, "chiusura con rifiuto/guasto");
    esigi(Array.isArray(vista.states) && vista.states.length > 0 && vista.states.every(s => oggetto(s) && testo(s.ref) && testo(s.svg)), "stati/disegni assenti");
  } else {
    esigi(vista.answer === null && vista.verification === null && vista.truth.electrical_claim_status !== "VERIFIED" && !["CLOSED", "VERIFIED"].includes(vista.truth.backend_closure_status), "rifiuto con risposta o attestazione positiva");
    esigi([vista.truth.electrical_claim_status, vista.truth.backend_closure_status].every(v => v === null || testo(v)), "truth del rifiuto non nullo/stringa");
    const diagnosi = vista.refusal;
    esigi(vista.failure === null && oggetto(diagnosi) && ["cause", "subject", "subject_kind", "diagnosis"].every(k => testo(diagnosi[k])), "diagnosi/causa/soggetto del rifiuto assente");
    esigi(oggetto(voce.rifiuto) && voce.rifiuto.cause === diagnosi.cause && voce.rifiuto.diagnosis === diagnosi.diagnosis, "rifiuto diverso dall’indice");
    esigi(Array.isArray(vista.states) && vista.states.length === 0 && Array.isArray(vista.steps) && vista.steps.length === 0, "rifiuto con stati o passi");
  }
  return vista;
}
