import type {TraceStep} from './StudentTracePanel.tsx';

export const SESSION_SCHEMA='kirchhoff-portable-session.v1' as const;
export type BoardSourceRecord={sceneSha256:string;selectedElementIds:string[];selectionOnly:boolean};
export type SessionBundle={
 schema:typeof SESSION_SCHEMA;
 netlist:string;
 method:string;
 circuitFingerprint:string;
 answerExact:string;
 engineRevision:string;
 selectedStep:number;
 showOriginal:boolean;
 boardScene:string;
 traceSteps:TraceStep[];
 priorImageSha256:string|null;
 boardSource?:BoardSourceRecord|null;
};

const record=(value:unknown):value is Record<string,unknown>=>Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
const digest=async(text:string)=>{
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
 return [...new Uint8Array(bytes)].map(byte=>byte.toString(16).padStart(2,'0')).join('');
};
export const boardSceneSha256=digest;

export async function makeSessionBundle(fields:Omit<SessionBundle,'schema'|'circuitFingerprint'>):Promise<SessionBundle>{
 return {schema:SESSION_SCHEMA,...fields,circuitFingerprint:await digest(fields.netlist)};
}

export async function readSessionBundle(text:string):Promise<SessionBundle>{
 if(text.length>10_500_000)throw new Error('Il quaderno supera 10 MB. Riduci le immagini nella lavagna.');
 let value:unknown;
 try{value=JSON.parse(text);}catch{throw new Error('Il quaderno non è un JSON leggibile.');}
 if(!record(value)||value.schema!==SESSION_SCHEMA||typeof value.netlist!=='string'||!value.netlist.trim()||value.netlist.length>16000||
    typeof value.method!=='string'||value.method.length>40||typeof value.answerExact!=='string'||value.answerExact.length>200||
    typeof value.engineRevision!=='string'||value.engineRevision.length>100||typeof value.circuitFingerprint!=='string'||
    !/^[a-f0-9]{64}$/.test(value.circuitFingerprint)||!Number.isInteger(value.selectedStep)||Number(value.selectedStep)<0||Number(value.selectedStep)>512||
    typeof value.showOriginal!=='boolean'||typeof value.boardScene!=='string'||value.boardScene.length>10_000_000||
    !Array.isArray(value.traceSteps)||value.traceSteps.length<1||value.traceSteps.length>32||
    !(value.priorImageSha256===null||typeof value.priorImageSha256==='string'&&/^[a-f0-9]{64}$/.test(value.priorImageSha256)))
   throw new Error('Versione o campi del quaderno non validi.');
 if(value.boardSource!==undefined&&value.boardSource!==null){
  const source=value.boardSource;
  if(!record(source)||value.priorImageSha256===null||!value.boardScene||typeof source.sceneSha256!=='string'||
     !/^[a-f0-9]{64}$/.test(source.sceneSha256)||typeof source.selectionOnly!=='boolean'||
     !Array.isArray(source.selectedElementIds)||!source.selectedElementIds.length||source.selectedElementIds.length>10000||
     !source.selectedElementIds.every(id=>typeof id==='string'&&id.length>0&&id.length<=128)||
     new Set(source.selectedElementIds).size!==source.selectedElementIds.length)
   throw new Error('La provenienza della lavagna nel quaderno non è valida.');
 }
 if(await digest(value.netlist)!==value.circuitFingerprint)throw new Error('Il circuito nel quaderno è stato modificato senza aggiornare la revisione.');
 for(const step of value.traceSteps){
  if(!record(step)||!['serie','parallelo','kcl','kvl','corrente','tensione','altro'].includes(String(step.operation))||!['clear','ambiguous','unreadable'].includes(String(step.reading))||
     !['transcription','first','second'].every(key=>typeof step[key]==='string'&&(step[key] as string).length<=500)||
     !(step.claimed_value===null||typeof step.claimed_value==='string'&&step.claimed_value.length<=100))
    throw new Error('Il procedimento nel quaderno contiene un passaggio non valido.');
 }
 if(value.boardScene){
  let scene:unknown;
  try{scene=JSON.parse(value.boardScene);}catch{throw new Error('La lavagna nel quaderno non è leggibile.');}
  if(!record(scene)||!Array.isArray(scene.elements)||scene.elements.length>10000||!record(scene.files))
   throw new Error('La lavagna nel quaderno non è valida.');
  if(record(value.boardSource)){
   const source=value.boardSource as BoardSourceRecord;
   const live=scene.elements.filter((element:unknown):element is {id:string;isDeleted?:boolean}=>
    record(element)&&typeof element.id==='string'&&element.id.length>0&&element.isDeleted!==true);
   const ids=new Set(live.map(element=>element.id));
   if(await digest(value.boardScene)!==source.sceneSha256||ids.size!==live.length||
      !source.selectedElementIds.every(id=>ids.has(id))||
      !source.selectionOnly&&source.selectedElementIds.length!==live.length)
    throw new Error('La provenienza della lavagna nel quaderno non è valida.');
  }
 }
 return value as SessionBundle;
}
