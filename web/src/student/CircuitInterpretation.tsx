import {useEffect,useRef,useState} from 'react';
import {CircuitInputEditor} from './CircuitInputEditor';
import {parseCircuitInputNetlist} from './circuitInputModel';
import type {CircuitInputModel} from './circuitInputModel';

function interpret(text:string):CircuitInputModel|null {
 try{return parseCircuitInputNetlist(text);}catch{return null;}
}
/** The expert text is a projection. Incomplete visual edits cannot solve an older draft. */
export function CircuitInterpretation({text,onChange,disabled=false}:{text:string;onChange:(text:string)=>void;disabled?:boolean}){
 const [model,setModel]=useState(()=>interpret(text));
 const [expert,setExpert]=useState(false);
 const delivered=useRef(text);
 useEffect(()=>{
  if(delivered.current===text)return;
  delivered.current=text;setModel(interpret(text));
 },[text]);
 return <section aria-label="Revisione del circuito">
  {model?<CircuitInputEditor value={model} disabled={disabled} onChange={(next,netlist)=>{
   setModel(next);delivered.current=netlist??'';onChange(netlist??'');
  }}/>:<p role="status">Questo circuito contiene righe non rappresentabili nell’editor attuale. Il testo completo è conservato nella vista esperta.</p>}
  <details open={expert||model===null} onToggle={e=>setExpert(e.currentTarget.open)}>
   <summary>Vista esperta: testo del circuito</summary>
   <label className="student-netlist">Componenti, nodi e domanda<textarea aria-label="Circuito da risolvere" disabled={disabled} spellCheck={false} value={text} onChange={e=>{
    delivered.current=e.target.value;setModel(interpret(e.target.value));onChange(e.target.value);
   }} placeholder={'V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2'}/></label>
  </details>
 </section>;
}
