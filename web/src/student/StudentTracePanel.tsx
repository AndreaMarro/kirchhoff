import {useEffect, useRef, useState} from 'react';

type Step = {transcription:string;operation:string;first:string;second:string;claimed_value:string|null;reading:string};
type Diagnosis = {outcome:'first_invalid'|'valid_so_far'|'not_assessable';step:number|null;category:string|null;message:string;focus:string[];circuit_fingerprint:string};
const blank = ():Step => ({transcription:'',operation:'serie',first:'',second:'',claimed_value:null,reading:'clear'});

export function StudentTracePanel({netlist,fingerprint}:{netlist:string;fingerprint:string}) {
 const [steps,setSteps]=useState<Step[]>([blank()]);
 const [diagnosis,setDiagnosis]=useState<Diagnosis|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const request=useRef(0);
 useEffect(()=>()=>{request.current++;},[]);
 function change(index:number,patch:Partial<Step>){
  request.current++;setDiagnosis(null);setError('');
  setSteps(items=>items.map((item,i)=>i===index?{...item,...patch}:item));
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
  <p>Scrivi le riduzioni che hai fatto nell’ordine. Per ora posso verificare resistori in serie o in parallelo; altri metodi e passaggi incerti restano senza giudizio. Il controllo si ferma al primo passaggio che posso dimostrare non valido.</p>
  {steps.map((s,i)=><fieldset key={i}><legend>Il tuo passaggio {i+1}</legend>
   <label>Che cosa hai scritto? <input aria-label={`Testo passaggio ${i+1}`} value={s.transcription} onChange={e=>change(i,{transcription:e.target.value})}/></label>
   <label>Operazione <select aria-label={`Operazione passaggio ${i+1}`} value={s.operation} onChange={e=>change(i,{operation:e.target.value})}><option value="serie">Serie</option><option value="parallelo">Parallelo</option><option value="altro">Altro metodo</option></select></label>
   <label>Primo componente <input aria-label={`Primo componente passaggio ${i+1}`} value={s.first} onChange={e=>change(i,{first:e.target.value})}/></label>
   <label>Secondo componente <input aria-label={`Secondo componente passaggio ${i+1}`} value={s.second} onChange={e=>change(i,{second:e.target.value})}/></label>
   <label>Valore equivalente in ohm, se scritto <input aria-label={`Valore passaggio ${i+1}`} value={s.claimed_value??''} onChange={e=>change(i,{claimed_value:e.target.value||null})}/></label>
   <label>Lettura <select aria-label={`Lettura passaggio ${i+1}`} value={s.reading} onChange={e=>change(i,{reading:e.target.value})}><option value="clear">Letto chiaramente</option><option value="ambiguous">Controlla questo</option><option value="unreadable">Non sono sicuro</option></select></label>
  </fieldset>)}
  <div className="student-dialog-actions"><button disabled={busy||steps.length>=32} onClick={()=>{request.current++;setDiagnosis(null);setSteps(items=>[...items,blank()]);}}>Aggiungi passaggio</button><button disabled={busy||steps.length===1} onClick={()=>{request.current++;setDiagnosis(null);setSteps(items=>items.slice(0,-1));}}>Togli ultimo</button><button className="student-primary" disabled={busy} onClick={()=>void check()}>{busy?'Controllo…':'Controlla i passaggi'}</button></div>
  {error?<p role="alert" className="student-error">{error}</p>:null}
  {diagnosis?<div role="status" className={`student-trace-result ${diagnosis.outcome}`}><strong>{diagnosis.outcome==='first_invalid'?(diagnosis.step===1?'Il primo passaggio va rivisto. Qui cambia il ragionamento.':`I passaggi fino al ${diagnosis.step!-1} sono validi. Qui cambia il ragionamento.`):diagnosis.outcome==='valid_so_far'?'Passaggi controllati validi fin qui.':'Non posso stabilire se questo passaggio è errato.'}</strong><p>{diagnosis.message}</p>{diagnosis.focus.length?<p>Elementi da rivedere sul circuito: {diagnosis.focus.filter(Boolean).join(' · ')}</p>:null}</div>:null}
 </section>;
}
