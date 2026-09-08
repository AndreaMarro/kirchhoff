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

function num(v: Json, cosa: string): number {
  if (typeof v !== "number") throw new Error(`campo ${cosa}: serve numero`);
  return v;
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
    index: num(v["index"], "step.index"),
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
  if (vista.outcome === "closed" && (vista.answer === null || vista.verification === null)) {
    throw new Error("chiusura senza risposta o senza evidenza");
  }
  if (vista.outcome === "refusal" && (vista.refusal === null || vista.answer !== null)) {
    throw new Error("rifiuto senza diagnosi o con risposta");
  }
  if (vista.outcome === "failure" && (vista.failure === null || vista.answer !== null)) {
    throw new Error("guasto senza messaggio o con risposta");
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
