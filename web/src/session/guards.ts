/* Validazione al confine: JSON del kernel -> tipi stretti o errore.
   Niente `any` giustificabile: ogni campo e' ristretto prima dell'uso. */
import { SCHEMA_VERSION } from "./types.ts";
import type {
  AnswerView,
  EntityView,
  ExerciseIndexEntry,
  Outcome,
  ProvenanceView,
  QuestionView,
  RefusalView,
  FailureView,
  StateView,
  StepView,
  StudentSessionView,
  TruthView,
  VerificationView,
} from "./types.ts";

type Json = unknown;

function isRecord(v: Json): v is Record<string, Json> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function str(v: Json, cosa: string): string {
  if (typeof v !== "string") throw new Error(`campo ${cosa}: serve stringa`);
  return v;
}

function strNull(v: Json, cosa: string): string | null {
  if (v === null) return null;
  return str(v, cosa);
}

function bool(v: Json, cosa: string): boolean {
  if (typeof v !== "boolean") throw new Error(`campo ${cosa}: serve boolean`);
  return v;
}

function indice(v: Json, cosa: string): number {
  if (typeof v !== "number") throw new Error(`campo ${cosa}: serve numero`);
  if (!Number.isFinite(v)) throw new Error(`campo ${cosa}: serve numero finito`);
  if (!Number.isInteger(v)) throw new Error(`campo ${cosa}: serve intero`);
  if (v < 0) throw new Error(`campo ${cosa}: negativo`);
  return v;
}

/* Linguaggio lessicale razionale condiviso col confine Python:
   le stringhe che `str(Fraction)` emette (interi, frazioni con segno,
   zero, negativi); niente decimali/esponenziali. Mai `Number`/`float`
   per validare l'esatto. */
const RE_EXACT = /^[+-]?\d+(\/\d+)?$/;

const UNITA_PER_QUANTITA: Record<string, Set<string>> = {
  current: new Set(["ampere"]),
  voltage: new Set(["volt"]),
};

function exact(v: Json, cosa: string): string {
  const testo = str(v, cosa);
  const pulito = testo.trim();
  if (!RE_EXACT.test(pulito)) {
    throw new Error(`campo ${cosa}: forma non riconosciuta`);
  }
  const barra = pulito.indexOf("/");
  if (barra >= 0) {
    const denominatore = pulito.slice(barra + 1);
    if (/^0+$/.test(denominatore)) {
      throw new Error(`campo ${cosa}: denominatore zero`);
    }
  }
  return testo;
}

function arr(v: Json, cosa: string): Json[] {
  if (!Array.isArray(v)) throw new Error(`campo ${cosa}: serve lista`);
  return v;
}

function outcome(v: Json): Outcome {
  if (v === "closed" || v === "refusal" || v === "failure") return v;
  throw new Error("outcome fuori dal vocabolario chiuso");
}

function question(v: Json): QuestionView {
  if (!isRecord(v)) throw new Error("question non e' un oggetto");
  return {
    request_id: str(v["request_id"], "question.request_id"),
    quantity: str(v["quantity"], "question.quantity"),
    target: str(v["target"], "question.target"),
  };
}

function answer(v: Json): AnswerView {
  if (!isRecord(v)) throw new Error("answer non e' un oggetto");
  return {
    target: str(v["target"], "answer.target"),
    quantity: str(v["quantity"], "answer.quantity"),
    exact: str(v["exact"], "answer.exact"),
    decimal: str(v["decimal"], "answer.decimal"),
    unit: str(v["unit"], "answer.unit"),
  };
}

function truth(v: Json): TruthView {
  if (!isRecord(v)) throw new Error("truth non e' un oggetto");
  return {
    electrical_claim_status: strNull(v["electrical_claim_status"], "truth.claim"),
    backend_closure_status: strNull(v["backend_closure_status"], "truth.session"),
    product_verified: bool(v["product_verified"], "truth.product_verified"),
  };
}

function state(v: Json): StateView {
  if (!isRecord(v)) throw new Error("state non e' un oggetto");
  return {
    ref: str(v["ref"], "state.ref"),
    svg: str(v["svg"], "state.svg"),
    description: str(v["description"], "state.description"),
  };
}

function entity(v: Json): EntityView {
  if (!isRecord(v)) throw new Error("entity non e' un oggetto");
  return { kind: str(v["kind"], "entity.kind"), id: str(v["id"], "entity.id") };
}

function step(v: Json): StepView {
  if (!isRecord(v)) throw new Error("step non e' un oggetto");
  const beforeSvg = v["before_svg"];
  const afterSvg = v["after_svg"];
  return {
    index: indice(v["index"], "step.index"),
    kind: str(v["kind"], "step.kind"),
    before_ref: str(v["before_ref"], "step.before_ref"),
    after_ref: str(v["after_ref"], "step.after_ref"),
    action: strNull(v["action"], "step.action"),
    equation: strNull(v["equation"], "step.equation"),
    equations: arr(v["equations"], "step.equations").map((e, i) =>
      str(e, `step.equations[${i}]`),
    ),
    affected: arr(v["affected"], "step.affected").map(entity),
    preserved: arr(v["preserved"], "step.preserved").map(entity),
    evidence_refs: arr(v["evidence_refs"], "step.evidence_refs").map((e, i) =>
      str(e, `step.evidence_refs[${i}]`),
    ),
    before_svg: beforeSvg === null ? null : str(beforeSvg, "step.before_svg"),
    after_svg: afterSvg === null ? null : str(afterSvg, "step.after_svg"),
  };
}

function verification(v: Json): VerificationView {
  if (!isRecord(v)) throw new Error("verification non e' un oggetto");
  return {
    claim_status: strNull(v["claim_status"], "verification.claim_status"),
    claim_verifier: strNull(v["claim_verifier"], "verification.claim_verifier"),
    claim_version: strNull(v["claim_version"], "verification.claim_version"),
    claim_subjects: arr(v["claim_subjects"], "verification.claim_subjects").map((e, i) =>
      str(e, `verification.claim_subjects[${i}]`),
    ),
    session_status: strNull(v["session_status"], "verification.session_status"),
    evidence_ids: arr(v["evidence_ids"], "verification.evidence_ids").map((e, i) =>
      str(e, `verification.evidence_ids[${i}]`),
    ),
  };
}

function provenance(v: Json): ProvenanceView {
  if (!isRecord(v)) throw new Error("provenance non e' un oggetto");
  return {
    producer: str(v["producer"], "provenance.producer"),
    source_sha: str(v["source_sha"], "provenance.source_sha"),
    detail: str(v["detail"], "provenance.detail"),
  };
}

function refusal(v: Json): RefusalView {
  if (!isRecord(v)) throw new Error("refusal non e' un oggetto");
  return {
    cause: str(v["cause"], "refusal.cause"),
    subject: str(v["subject"], "refusal.subject"),
    subject_kind: str(v["subject_kind"], "refusal.subject_kind"),
    diagnosis: str(v["diagnosis"], "refusal.diagnosis"),
  };
}

function failure(v: Json): FailureView {
  if (!isRecord(v)) throw new Error("failure non e' un oggetto");
  return {
    dove: str(v["dove"], "failure.dove"),
    messaggio: str(v["messaggio"], "failure.messaggio"),
  };
}

function nullable<T>(v: Json, fn: (x: Json) => T): T | null {
  if (v === null || v === undefined) return null;
  return fn(v);
}

export function parseSession(payload: Json): StudentSessionView {
  if (!isRecord(payload)) throw new Error("sessione non e' un oggetto");
  if (payload["schema_version"] !== SCHEMA_VERSION) {
    throw new Error(`schema ${String(payload["schema_version"])} non supportato`);
  }
  const esito = outcome(payload["outcome"]);
  const vista: StudentSessionView = {
    schema_version: SCHEMA_VERSION,
    session_id: str(payload["session_id"], "session_id"),
    outcome: esito,
    question: nullable(payload["question"], question),
    answer: nullable(payload["answer"], answer),
    truth: truth(payload["truth"]),
    states: arr(payload["states"], "states").map(state),
    steps: arr(payload["steps"], "steps").map(step),
    verification: nullable(payload["verification"], verification),
    provenance: nullable(payload["provenance"], provenance),
    refusal: nullable(payload["refusal"], refusal),
    failure: nullable(payload["failure"], failure),
  };
  if (vista.truth.product_verified !== false) {
    throw new Error("product_verified deve essere false in questo profilo");
  }
  if (vista.outcome === "closed") {
    if (vista.answer === null || vista.verification === null) {
      throw new Error("chiusura senza risposta o senza evidenza");
    }
    if (vista.refusal !== null || vista.failure !== null) {
      throw new Error("chiusura con rifiuto o guasto");
    }
    if (vista.truth.electrical_claim_status !== "VERIFIED") {
      throw new Error("claim elettrico della closed diverso da VERIFIED");
    }
    if (vista.truth.backend_closure_status !== "CLOSED") {
      throw new Error("chiusura di backend diverso da CLOSED");
    }
    if (vista.verification.claim_status !== "VERIFIED") {
      throw new Error("verification.claim_status diverso da VERIFIED");
    }
    if (vista.verification.session_status !== "CLOSED") {
      throw new Error("verification.session_status diverso da CLOSED");
    }
    if (vista.question === null) {
      throw new Error("closed senza domanda");
    }
    if (vista.answer.target !== vista.question.target) {
      throw new Error("answer.target non coincide con question.target");
    }
    if (vista.answer.quantity !== vista.question.quantity) {
      throw new Error("answer.quantity non coincide con question.quantity");
    }
    const ammesse = UNITA_PER_QUANTITA[vista.answer.quantity];
    if (ammesse === undefined || !ammesse.has(vista.answer.unit)) {
      throw new Error(
        `unita' ${vista.answer.unit} non coerente con quantity ${vista.answer.quantity}`,
      );
    }
    exact(vista.answer.exact, "answer.exact");
    if (vista.verification.evidence_ids.length === 0) {
      throw new Error("closed senza evidenza");
    }
    if (vista.states.length === 0) {
      throw new Error("closed senza stati");
    }
    const refs = new Set(vista.states.map((s) => s.ref));
    if (refs.size !== vista.states.length) {
      throw new Error("state refs duplicati");
    }
    if (vista.steps.length === 0) {
      throw new Error("closed senza passi");
    }
    const indici = new Set<number>();
    for (const passo of vista.steps) {
      if (indici.has(passo.index)) {
        throw new Error(`indice ${passo.index} duplicato`);
      }
      indici.add(passo.index);
      if (!refs.has(passo.before_ref)) {
        throw new Error(`before_ref ${passo.before_ref} non risolubile negli stati`);
      }
      if (!refs.has(passo.after_ref)) {
        throw new Error(`after_ref ${passo.after_ref} non risolubile negli stati`);
      }
      if (passo.kind === "analytical") {
        if (passo.before_ref !== passo.after_ref) {
          throw new Error("passo analitico con before_ref diverso da after_ref");
        }
        if (
          passo.evidence_refs.length !== 1 ||
          passo.evidence_refs[0] !== passo.before_ref
        ) {
          throw new Error("evidence_refs del passo analitico non coincide con lo stato");
        }
      } else if (passo.kind === "transform") {
        if (passo.before_ref === passo.after_ref) {
          throw new Error("passo topologico con before_ref uguale ad after_ref");
        }
        if (
          passo.evidence_refs.length !== 2 ||
          passo.evidence_refs[0] !== passo.before_ref ||
          passo.evidence_refs[1] !== passo.after_ref
        ) {
          throw new Error(
            "evidence_refs del passo topologico non coincide con before_ref/after_ref",
          );
        }
      } else {
        throw new Error(`kind ${passo.kind} fuori dal vocabolario chiuso`);
      }
      for (const ref of passo.evidence_refs) {
        if (!refs.has(ref)) {
          throw new Error(`evidence_ref ${ref} non risolubile negli stati`);
        }
      }
    }
    const ordinati = [...indici].sort((a, b) => a - b);
    for (let i = 0; i < ordinati.length; i++) {
      if (ordinati[i] !== i) {
        throw new Error("indici dei passi non consecutivi da zero");
      }
    }
  }
  if (vista.outcome === "refusal") {
    if (vista.refusal === null || vista.answer !== null) {
      throw new Error("rifiuto senza diagnosi o con risposta");
    }
    if (vista.verification !== null) {
      throw new Error("rifiuto con verification");
    }
    if (vista.truth.electrical_claim_status === "VERIFIED") {
      throw new Error("rifiuto con claim positivo");
    }
    if (
      vista.truth.backend_closure_status === "CLOSED" ||
      vista.truth.backend_closure_status === "VERIFIED"
    ) {
      throw new Error("rifiuto con prova di chiusura");
    }
    if (vista.states.length !== 0 || vista.steps.length !== 0) {
      throw new Error("rifiuto con stati o passi");
    }
  }
  if (vista.outcome === "failure") {
    if (vista.failure === null || vista.answer !== null) {
      throw new Error("guasto senza messaggio o con risposta");
    }
    if (vista.verification !== null) {
      throw new Error("guasto con verification");
    }
    if (vista.truth.electrical_claim_status === "VERIFIED") {
      throw new Error("guasto con claim positivo");
    }
    if (
      vista.truth.backend_closure_status === "CLOSED" ||
      vista.truth.backend_closure_status === "VERIFIED"
    ) {
      throw new Error("guasto con prova di chiusura");
    }
    if (vista.states.length !== 0 || vista.steps.length !== 0) {
      throw new Error("guasto con stati o passi");
    }
  }
  return vista;
}

export function parseIndex(payload: Json): ExerciseIndexEntry[] {
  return arr(payload, "index").map((voce, i) => {
    if (!isRecord(voce)) throw new Error(`index[${i}] non e' un oggetto`);
    const domanda = voce["domanda"];
    if (!isRecord(domanda)) throw new Error(`index[${i}].domanda non e' un oggetto`);
    const entry: ExerciseIndexEntry = {
      id: str(voce["id"], `index[${i}].id`),
      titolo: str(voce["titolo"], `index[${i}].titolo`),
      outcome: outcome(voce["outcome"]),
      domanda: {
        quantity: str(domanda["quantity"], `index[${i}].domanda.quantity`),
        target: str(domanda["target"], `index[${i}].domanda.target`),
      },
    };
    if (typeof voce["risposta_esatta"] === "string") {
      entry.risposta_esatta = voce["risposta_esatta"];
    }
    return entry;
  });
}
