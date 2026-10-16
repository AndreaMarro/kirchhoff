import {useEffect, useRef, useState} from 'react';
import {checkTrace,describeTraceStep,traceOutcome,MAX_TRACE_ATTEMPTS,readTraceHistory,storedTraceHistory} from './traceHistory.ts';
import type {TraceStep,Diagnosis,TraceAttempt} from './traceHistory.ts';

export type {TraceStep} from './traceHistory.ts';
export const blankTraceStep = ():TraceStep => ({transcription:'',operation:'serie',first:'',second:'',claimed_value:null,reading:'clear'});

export function StudentTracePanel({netlist,fingerprint,steps,history,disabled,onStepsChange,onAttempt,onCheckingChange}:{netlist:string;fingerprint:string;steps:TraceStep[];history:TraceAttempt[];disabled:boolean;onStepsChange:(steps:TraceStep[])=>void;onAttempt:(attempt:TraceAttempt)=>void;onCheckingChange:(checking:boolean)=>void}) {
 const [diagnosis,setDiagnosis]=useState<Diagnosis|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const request=useRef(0);
 const disabledNow=useRef(disabled);disabledNow.current=disabled;
 useEffect(()=>()=>{request.current++;},[]);
 useEffect(()=>{onCheckingChange(busy);return()=>onCheckingChange(false);},[busy,onCheckingChange]);
 useEffect(()=>{if(disabled){request.current++;setBusy(false);}},[disabled]);
 function change(index:number,patch:Partial<TraceStep>){
  request.current++;setBusy(false);setDiagnosis(null);setError('');
  onStepsChange(steps.map((item,i)=>i===index?{...item,...patch}:item));
 }
 async function check(){
  if(disabled||history.length>=MAX_TRACE_ATTEMPTS)return;
  const n=++request.current;setBusy(true);setError('');setDiagnosis(null);
  try{
   const submitted=steps.map(s=>({...s,transcription:s.transcription||`${s.operation} ${s.first} ${s.second}`}));
   readTraceHistory([...storedTraceHistory(history),{steps:submitted,engineRevision:'0'.repeat(40),circuitFingerprint:fingerprint}],fingerprint);
   const result=await checkTrace(netlist,fingerprint,submitted);
   if(n===request.current&&!disabledNow.current){setDiagnosis(result);onAttempt({steps:submitted,engineRevision:result.engine_revision,circuitFingerprint:fingerprint,diagnosis:result});}
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}
  finally{if(n===request.current)setBusy(false);}
 }
 return <section className="student-trace" aria-label="Controlla il tuo procedimento">
  <h3>Controlla il tuo procedimento</h3>
  <p>Scrivi i passaggi nell’ordine. Posso verificare riduzioni, KCL, KVL e valori DC di corrente o tensione del circuito originale. Con Tensione da Ohm controlli V(X) = I(X) × R(Y): indica X e la resistenza Y usata nel prodotto. La corrente I(X) viene verificata sul circuito originale; per controllare anche un tuo valore di corrente aggiungi prima un passaggio Corrente. Il verso predefinito di ogni ramo va dal primo al secondo morsetto nella netlist; per un valore puoi dichiarare anche il verso opposto, scrivendo i due nodi. Per KCL scrivi +R1,-R2,+R3: + se il verso esce dal nodo, − se entra. Per KVL indica un nodo della maglia e le tensioni orientate, per esempio +R1,+R2,-V1: + nel verso del ramo, − nel verso opposto. Una semplificazione incerta resta senza giudizio; il controllo del valore non certifica il metodo scritto.</p>
  {steps.map((s,i)=>{const numeric=s.operation==='corrente'||s.operation==='tensione',ohm=s.operation==='ohm-tensione',kcl=s.operation==='kcl',kvl=s.operation==='kvl',law=kcl||kvl;return <fieldset key={i} disabled={disabled}><legend>Il tuo passaggio {i+1}</legend>
   <label>Che cosa hai scritto? <input aria-label={`Testo passaggio ${i+1}`} value={s.transcription} onChange={e=>change(i,{transcription:e.target.value})}/></label>
   <label>Operazione <select aria-label={`Operazione passaggio ${i+1}`} value={s.operation} onChange={e=>{const operation=e.target.value;change(i,{operation,first:['kcl','kvl'].includes(operation)?'':s.first,second:['corrente','tensione','ohm-tensione','kcl','kvl'].includes(operation)?'':s.second,claimed_value:['kcl','kvl'].includes(operation)?null:s.claimed_value});}}><option value="serie">Serie</option><option value="parallelo">Parallelo</option><option value="kcl">KCL al nodo</option><option value="kvl">KVL alla maglia</option><option value="corrente">Corrente di un componente</option><option value="tensione">Tensione di un componente</option><option value="ohm-tensione">Tensione da Ohm: corrente × resistenza</option><option value="altro">Altro metodo</option></select></label>
   <label>{kcl?'Nodo':kvl?'Nodo della maglia':ohm?'Resistore della tensione':numeric?'Componente':'Primo componente'} <input aria-label={`Primo componente passaggio ${i+1}`} value={s.first} onChange={e=>change(i,{first:e.target.value})}/></label>
   {numeric?<label>Verso di riferimento (facoltativo: nodo1,nodo2) <input aria-label={`Verso passaggio ${i+1}`} value={s.second} onChange={e=>change(i,{second:e.target.value})}/></label>:<label>{kcl?'Correnti orientate (somma = 0)':kvl?'Tensioni orientate (somma = 0)':ohm?'Resistenza usata nel prodotto':'Secondo componente'} <input aria-label={`Secondo componente passaggio ${i+1}`} value={s.second} onChange={e=>change(i,{second:e.target.value})}/></label>}
   {!law?<label>{ohm?'Valore della tensione in V':numeric?`Valore ${s.operation} in ${s.operation==='corrente'?'A':'V'}`:'Valore equivalente in ohm, se scritto'} <input aria-label={`Valore passaggio ${i+1}`} value={s.claimed_value??''} onChange={e=>change(i,{claimed_value:e.target.value||null})}/></label>:null}
   <label>Lettura <select aria-label={`Lettura passaggio ${i+1}`} value={s.reading} onChange={e=>change(i,{reading:e.target.value})}><option value="clear">Letto chiaramente</option><option value="ambiguous">Controlla questo</option><option value="unreadable">Non sono sicuro</option></select></label>
  </fieldset>})}
  <div className="student-dialog-actions"><button disabled={disabled||busy||steps.length>=32} onClick={()=>{request.current++;setDiagnosis(null);onStepsChange([...steps,blankTraceStep()]);}}>Aggiungi passaggio</button><button disabled={disabled||busy||steps.length===1} onClick={()=>{request.current++;setDiagnosis(null);onStepsChange(steps.slice(0,-1));}}>Togli ultimo</button><button className="student-primary" disabled={disabled||busy||history.length>=MAX_TRACE_ATTEMPTS} onClick={()=>void check()}>{busy?'Controllo…':'Controlla i passaggi'}</button></div>
  {history.length>=MAX_TRACE_ATTEMPTS?<p role="status">Raggiunto il limite di 32 controlli. La cronologia è conservata senza sovrascritture: salva il quaderno.</p>:null}
  {error?<p role="alert" className="student-error">{error}</p>:null}
  {diagnosis?<div role="status" className={`student-trace-result ${diagnosis.outcome}`}><strong>{diagnosis.outcome==='first_invalid'?(diagnosis.step===1?'Il primo passaggio va rivisto. Qui cambia il ragionamento.':`I passaggi fino al ${diagnosis.step!-1} sono validi. Qui cambia il ragionamento.`):diagnosis.outcome==='valid_so_far'?'Passaggi controllati validi fin qui.':'Non posso stabilire se questo passaggio è errato.'}</strong><p>{diagnosis.message}</p>{diagnosis.focus.length?<p>Elementi da rivedere sul circuito: {diagnosis.focus.filter(Boolean).join(' · ')}</p>:null}</div>:null}
  {history.length?<section className="student-trace-history" aria-label="Tentativi e correzioni"><h4>Tentativi e correzioni</h4>
   <p>Controlli in ordine, conservati in questa pagina. Usa Salva quaderno per mantenerli sul dispositivo. Gli esiti sono ricalcolati quando riapri il quaderno e nel PDF; il testo libero non viene certificato.</p>
   <ol>{history.map((attempt,index)=><li key={index}><details><summary>Tentativo {index+1} — {traceOutcome(attempt.diagnosis)}</summary>
    <p>{attempt.diagnosis.message}</p><ol>{attempt.steps.map((s,i)=><li key={i}><p>{s.transcription}</p><p>{describeTraceStep(s)}</p></li>)}</ol>
    <p>Motore del controllo conservato: <code>{attempt.engineRevision.slice(0,12)}</code>. Esito ricalcolato con: <code>{attempt.diagnosis.engine_revision.slice(0,12)}</code>.</p>
    <button disabled={disabled} onClick={()=>{request.current++;setBusy(false);setDiagnosis(null);setError('');onStepsChange(attempt.steps.map(s=>({...s})));}}>Riprendi tentativo {index+1}</button>
   </details></li>)}</ol></section>:null}
 </section>;
}
