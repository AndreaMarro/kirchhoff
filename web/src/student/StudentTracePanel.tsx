import {useEffect, useRef, useState} from 'react';

export type TraceStep = {transcription:string;operation:string;first:string;second:string;claimed_value:string|null;reading:string};
type Diagnosis = {outcome:'first_invalid'|'valid_so_far'|'not_assessable';step:number|null;category:string|null;message:string;focus:string[];circuit_fingerprint:string};
export const blankTraceStep = ():TraceStep => ({transcription:'',operation:'serie',first:'',second:'',claimed_value:null,reading:'clear'});

export function StudentTracePanel({netlist,fingerprint,steps,onStepsChange}:{netlist:string;fingerprint:string;steps:TraceStep[];onStepsChange:(steps:TraceStep[])=>void}) {
 const [diagnosis,setDiagnosis]=useState<Diagnosis|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const request=useRef(0);
 useEffect(()=>()=>{request.current++;},[]);
 function change(index:number,patch:Partial<TraceStep>){
  request.current++;setDiagnosis(null);setError('');
  onStepsChange(steps.map((item,i)=>i===index?{...item,...patch}:item));
 }
 async function check(){
  const n=++request.current;setBusy(true);setError('');setDiagnosis(null);
  try{
   const body={netlist,trace:{schema:'student-trace.v1',circuit_fingerprint:fingerprint,steps:steps.map(s=>({...s,transcription:s.transcription||`${s.operation} ${s.first} ${s.second}`}))}};
   const response=await fetch('api/diagnose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
   const result=await response.json() as Diagnosis & {message:string};
   if(!response.ok)throw new Error(result.message||'Controllo non riuscito.');
   if(result.circuit_fingerprint!==fingerprint)throw new Error('Il circuito è cambiato: ripeti il controllo.');
   if(n===request.current)setDiagnosis(result);
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}
  finally{if(n===request.current)setBusy(false);}
 }
 return <section className="student-trace" aria-label="Controlla il tuo procedimento">
  <h3>Controlla il tuo procedimento</h3>
  <p>Scrivi i passaggi nell’ordine. Posso verificare riduzioni, KCL, KVL e valori DC di corrente o tensione del circuito originale. Il verso predefinito di ogni ramo va dal primo al secondo morsetto nella netlist; per un valore puoi dichiarare anche il verso opposto, scrivendo i due nodi. Per KCL scrivi +R1,-R2,+R3: + se il verso esce dal nodo, − se entra. Per KVL indica un nodo della maglia e le tensioni orientate, per esempio +R1,+R2,-V1: + nel verso del ramo, − nel verso opposto. Una semplificazione incerta resta senza giudizio; il controllo del valore non certifica il metodo scritto.</p>
  {steps.map((s,i)=>{const numeric=s.operation==='corrente'||s.operation==='tensione',kcl=s.operation==='kcl',kvl=s.operation==='kvl',law=kcl||kvl;return <fieldset key={i}><legend>Il tuo passaggio {i+1}</legend>
   <label>Che cosa hai scritto? <input aria-label={`Testo passaggio ${i+1}`} value={s.transcription} onChange={e=>change(i,{transcription:e.target.value})}/></label>
   <label>Operazione <select aria-label={`Operazione passaggio ${i+1}`} value={s.operation} onChange={e=>{const operation=e.target.value;change(i,{operation,first:['kcl','kvl'].includes(operation)?'':s.first,second:['corrente','tensione','kcl','kvl'].includes(operation)?'':s.second,claimed_value:['kcl','kvl'].includes(operation)?null:s.claimed_value});}}><option value="serie">Serie</option><option value="parallelo">Parallelo</option><option value="kcl">KCL al nodo</option><option value="kvl">KVL alla maglia</option><option value="corrente">Corrente di un componente</option><option value="tensione">Tensione di un componente</option><option value="altro">Altro metodo</option></select></label>
   <label>{kcl?'Nodo':kvl?'Nodo della maglia':numeric?'Componente':'Primo componente'} <input aria-label={`Primo componente passaggio ${i+1}`} value={s.first} onChange={e=>change(i,{first:e.target.value})}/></label>
   {numeric?<label>Verso di riferimento (facoltativo: nodo1,nodo2) <input aria-label={`Verso passaggio ${i+1}`} value={s.second} onChange={e=>change(i,{second:e.target.value})}/></label>:<label>{kcl?'Correnti orientate (somma = 0)':kvl?'Tensioni orientate (somma = 0)':'Secondo componente'} <input aria-label={`Secondo componente passaggio ${i+1}`} value={s.second} onChange={e=>change(i,{second:e.target.value})}/></label>}
   {!law?<label>{numeric?`Valore ${s.operation} in ${s.operation==='corrente'?'A':'V'}`:'Valore equivalente in ohm, se scritto'} <input aria-label={`Valore passaggio ${i+1}`} value={s.claimed_value??''} onChange={e=>change(i,{claimed_value:e.target.value||null})}/></label>:null}
   <label>Lettura <select aria-label={`Lettura passaggio ${i+1}`} value={s.reading} onChange={e=>change(i,{reading:e.target.value})}><option value="clear">Letto chiaramente</option><option value="ambiguous">Controlla questo</option><option value="unreadable">Non sono sicuro</option></select></label>
  </fieldset>})}
  <div className="student-dialog-actions"><button disabled={busy||steps.length>=32} onClick={()=>{request.current++;setDiagnosis(null);onStepsChange([...steps,blankTraceStep()]);}}>Aggiungi passaggio</button><button disabled={busy||steps.length===1} onClick={()=>{request.current++;setDiagnosis(null);onStepsChange(steps.slice(0,-1));}}>Togli ultimo</button><button className="student-primary" disabled={busy} onClick={()=>void check()}>{busy?'Controllo…':'Controlla i passaggi'}</button></div>
  {error?<p role="alert" className="student-error">{error}</p>:null}
  {diagnosis?<div role="status" className={`student-trace-result ${diagnosis.outcome}`}><strong>{diagnosis.outcome==='first_invalid'?(diagnosis.step===1?'Il primo passaggio va rivisto. Qui cambia il ragionamento.':`I passaggi fino al ${diagnosis.step!-1} sono validi. Qui cambia il ragionamento.`):diagnosis.outcome==='valid_so_far'?'Passaggi controllati validi fin qui.':'Non posso stabilire se questo passaggio è errato.'}</strong><p>{diagnosis.message}</p>{diagnosis.focus.length?<p>Elementi da rivedere sul circuito: {diagnosis.focus.filter(Boolean).join(' · ')}</p>:null}</div>:null}
 </section>;
}
