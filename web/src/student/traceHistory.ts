/** Cronologia applicativa: input conservati, diagnosi sempre ricalcolate. */
export type TraceStep={transcription:string;operation:string;first:string;second:string;claimed_value:string|null;reading:string};
export type Diagnosis={schema:'student-diagnosis.v1';outcome:'first_invalid'|'valid_so_far'|'not_assessable';step:number|null;category:string|null;message:string;focus:string[];circuit_fingerprint:string;engine_revision:string};
export type StoredTraceAttempt={steps:TraceStep[];engineRevision:string;circuitFingerprint:string};
export type TraceAttempt=StoredTraceAttempt&{diagnosis:Diagnosis};
export const MAX_TRACE_ATTEMPTS=32;
export const MAX_TRACE_HISTORY_BYTES=2_500_000;
const record=(x:unknown):x is Record<string,unknown>=>Boolean(x)&&typeof x==='object'&&!Array.isArray(x);

export function validTraceSteps(value:unknown):value is TraceStep[]{
 return Array.isArray(value)&&value.length>=1&&value.length<=32&&value.every(step=>record(step)&&
  typeof step.operation==='string'&&['serie','parallelo','kcl','kvl','corrente','tensione','ohm-tensione','altro'].includes(step.operation)&&
  typeof step.reading==='string'&&['clear','ambiguous','unreadable'].includes(step.reading)&&
  ['transcription','first','second'].every(key=>typeof step[key]==='string'&&step[key].length<=500)&&
  (step.claimed_value===null||typeof step.claimed_value==='string'&&step.claimed_value.length<=100));
}

export function readTraceHistory(value:unknown,fingerprint:string):StoredTraceAttempt[]{
 if(!Array.isArray(value)||value.length>MAX_TRACE_ATTEMPTS||value.some(attempt=>!record(attempt)||
  Object.keys(attempt).length!==3||!Object.keys(attempt).every(key=>['steps','engineRevision','circuitFingerprint'].includes(key))||
  typeof attempt.engineRevision!=='string'||!/^[a-f0-9]{40}$/.test(attempt.engineRevision)||
  attempt.circuitFingerprint!==fingerprint||!validTraceSteps(attempt.steps)||
  attempt.steps.some(step=>Object.keys(step).length!==6)))
  throw new Error('La cronologia contiene un tentativo non valido o supera 32 controlli.');
 if(new TextEncoder().encode(JSON.stringify(value)).length>MAX_TRACE_HISTORY_BYTES)
  throw new Error('La cronologia supera 2,5 MB: nessun tentativo viene sovrascritto.');
 return value as StoredTraceAttempt[];
}

export function storedTraceHistory(attempts:TraceAttempt[]):StoredTraceAttempt[]{
 return attempts.map(({steps,engineRevision,circuitFingerprint})=>({steps:steps.map(step=>({...step})),engineRevision,circuitFingerprint}));
}

export async function checkTrace(netlist:string,fingerprint:string,steps:TraceStep[]):Promise<Diagnosis>{
 const response=await fetch('api/diagnose',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({netlist,trace:{schema:'student-trace.v1',circuit_fingerprint:fingerprint,steps}})});
 const result:unknown=await response.json();
 if(!response.ok)throw new Error(record(result)&&typeof result.message==='string'?result.message:'Controllo non riuscito.');
 if(!record(result)||result.schema!=='student-diagnosis.v1'||result.circuit_fingerprint!==fingerprint||
  !['first_invalid','valid_so_far','not_assessable'].includes(String(result.outcome))||
  !(result.step===null||Number.isInteger(result.step)&&Number(result.step)>=1&&Number(result.step)<=steps.length)||
  !(result.category===null||typeof result.category==='string'&&result.category.length<=100)||
  typeof result.message!=='string'||result.message.length>4000||!Array.isArray(result.focus)||result.focus.length>64||
  !result.focus.every(x=>typeof x==='string'&&x.length<=500)||
  typeof result.engine_revision!=='string'||!/^[a-f0-9]{40}$/.test(result.engine_revision))
  throw new Error('Diagnosi non interpretabile o circuito cambiato: ripeti il controllo.');
 if(result.outcome==='valid_so_far'?(result.step!==null||result.category!==null||result.focus.length!==0):
    (result.step===null||typeof result.category!=='string'||!result.category))
  throw new Error('Diagnosi incoerente: ripeti il controllo.');
 return result as Diagnosis;
}

export function traceOutcome(diagnosis:Diagnosis):string{
 return diagnosis.outcome==='valid_so_far'?'Passaggi controllati validi fin qui':
  diagnosis.outcome==='not_assessable'?'Passaggio non valutabile':
  `Primo errore al passaggio ${diagnosis.step}: ${diagnosis.category==='reference'?'riferimento':diagnosis.category==='algebra'?'calcolo':diagnosis.category??'da rivedere'}`;
}

export function describeTraceStep(step:TraceStep):string{
 return `${step.operation}; primo: ${step.first||'non indicato'}; secondo/verso: ${step.second||'non indicato'}; valore: ${step.claimed_value??'non indicato'}; lettura: ${step.reading}`;
}
