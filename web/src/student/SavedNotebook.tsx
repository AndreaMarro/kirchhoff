import {useState} from 'react';
import type {SessionBundle,SavedLesson} from './sessionBundle.ts';
import {safeSvg} from './safeSvg.ts';
import {lessonMathMarkup,lessonExpressionMarkup} from './lessonMath.ts';
import {describeTraceStep} from './traceHistory.ts';

export function SavedNotebook({bundle,methodLabel,error,busy,onClose,onRecalculate}:{bundle:SessionBundle&{savedLesson:SavedLesson};methodLabel:string;error:string;busy:boolean;onClose:()=>void;onRecalculate:()=>void}){
 const view=bundle.savedLesson.view;
 const [step,setStep]=useState(Math.min(bundle.selectedStep,view.steps.length-1)),[original,setOriginal]=useState(bundle.showOriginal);
 const current=view.steps[step],math=lessonMathMarkup(current.math),answer=lessonExpressionMarkup(view.answer.math);
 function download(data:string,name:string){
  const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const a=document.createElement('a');
  a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
 }
 function navigate(index:number){setStep(index);setOriginal(false);}
 return <div className="student-app saved-notebook" data-notebook-mode="saved"><main className="student-main">
  <h1>Copia salvata · sola lettura</h1>
  <p role="status">I calcoli e i tentativi non sono ricontrollati in questa vista. Spiegazioni DRAFT: revisione docente non disponibile.</p>
  <p>Mostro i passaggi conservati nel file. L’impronta controlla l’integrità della copia, non è una firma né una nuova verifica scientifica.</p>
  <div className="student-toolbar"><button onClick={onClose}>Torna al laboratorio</button><button disabled={busy} onClick={onRecalculate}>{busy?'Riapertura…':'Riapri con ricalcolo'}</button><button onClick={()=>download(JSON.stringify(bundle),'quaderno-kirchhoff.json')}>Conserva questo quaderno</button></div>
  {error?<p className="student-error" role="alert">{error}</p>:null}
  <p>Metodo conservato: {methodLabel}. Circuito <code>{bundle.circuitFingerprint.slice(0,12)}</code> · motore della copia <code>{bundle.engineRevision.slice(0,12)}</code>.</p>
  <section className="student-lesson" aria-label="Passaggi salvati">
   <nav className="student-outline" aria-label="Percorso salvato"><ol>{view.steps.map((s,i)=><li key={i}><button aria-current={step===i?'step':undefined} onClick={()=>navigate(i)}>{i+1}. {s.title}</button></li>)}</ol></nav>
   <div className="student-stage-head"><div><p>{view.title} · {view.answer.reference}</p><h2>{original?'Schema originale salvato':current.title}</h2></div><button aria-pressed={original} onClick={()=>setOriginal(!original)}>{original?'Torna al passaggio':'Rivedi l’originale'}</button></div>
   <div className="student-schematics"><figure><div className="student-drawing" tabIndex={0} aria-label="Circuito salvato" dangerouslySetInnerHTML={{__html:safeSvg(original?view.original:current.svg)}}/></figure></div>
   <div className="student-navigation"><button aria-label="Passo precedente" disabled={step===0} onClick={()=>navigate(step-1)}>← Indietro</button><span>{step+1} / {view.steps.length}</span><button aria-label="Passo successivo" disabled={step===view.steps.length-1} onClick={()=>navigate(step+1)}>Avanti →</button></div>
   <div className="student-explanation"><p>{current.explanation}</p><div className="student-equations">{math?<div dangerouslySetInnerHTML={{__html:math}}/>:current.equations.map((e,i)=><p key={i}>{e}</p>)}</div>
    {step===view.steps.length-1?<p className="student-result">Risultato conservato: {answer?<span dangerouslySetInnerHTML={{__html:answer}}/>:view.answer.display_exact??view.answer.exact} {view.answer.unit}</p>:null}
   </div>
  </section>
  {bundle.sourceArtifact?<figure className="student-source-image"><img src={bundle.sourceArtifact.prepared.dataURL} alt="Fonte conservata nel quaderno"/><figcaption>Fonte storica; la conferma fotografica non viene ripristinata.</figcaption></figure>:null}
  <section className="student-trace"><h2>Tentativi conservati</h2><p>I testi sono quelli del quaderno. Per un nuovo controllo usa Riapri con ricalcolo.</p>
   {bundle.traceHistory.length?<ol>{bundle.traceHistory.map((attempt,i)=><li key={i}><details><summary>Tentativo {i+1} · da ricontrollare</summary>{attempt.steps.map((s,j)=><div key={j}><p>{s.transcription}</p><p>{describeTraceStep(s)}</p></div>)}</details></li>)}</ol>:<p>Nessun controllo precedente conservato.</p>}
   <details><summary>Ultima bozza del procedimento</summary>{bundle.traceSteps.map((s,i)=><div key={i}><p>{s.transcription}</p><p>{describeTraceStep(s)}</p></div>)}</details>
  </section>
  {bundle.boardScene?<section><h2>Lavagna conservata</h2><p>La scena originale è inclusa nel quaderno e rimane esportabile; questa copia non modifica i tratti.</p><button onClick={()=>download(bundle.boardScene,'lavagna.excalidraw')}>Esporta la scena della lavagna</button></section>:null}
  <details><summary>Circuito e provenienza della copia</summary><pre style={{whiteSpace:'pre-wrap'}}>{bundle.netlist}</pre><p>Impronta della copia: <code style={{overflowWrap:'anywhere'}}>{bundle.savedLesson.sha256}</code>. Dati e immagini restano nel browser; chi riceve il file può leggerli.</p></details>
 </main></div>;
}
