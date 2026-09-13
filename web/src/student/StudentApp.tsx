import {useEffect,useRef,useState} from 'react';
import {CircuitEditor} from './CircuitEditor.tsx';
import './student.css';

type Step={title:string;explanation:string;svg:string;equations:string[];focus:string[]};
type Lesson={schema:string;outcome:'solved';title:string;netlist:string;method:string;available:string[];original:string;steps:Step[];answer:{exact:string;decimal:string;unit:string;reference:string};fingerprint:string;source_sha:string};
type Example={id:string;title:string;netlist:string;methods:Record<string,string>};
const names:Record<string,string>={auto:'Percorso consigliato',divider:'Partitore',current_divider:'Partitore di corrente',millman:'Millman',norton:'Trasformazioni Norton',thevenin:'Equivalente Thévenin',superposition:'Sovrapposizione',nodal:'Analisi nodale',star_delta:'Stella → triangolo'};

async function response(res:Response):Promise<unknown>{
 const value=await res.json() as {message?:string};if(!res.ok)throw new Error(value.message??`Richiesta non riuscita (${res.status})`);return value;
}
function parseLesson(value:unknown):Lesson {
 const x=value as Lesson & {message?:string};
 if(!x||x.outcome!=='solved')throw new Error(x?.message??'Il circuito non è risolto.');
 if(x.schema!=='circuit-lesson.v1'||!Array.isArray(x.steps)||!x.steps.length||typeof x.original!=='string'||!x.answer||!Array.isArray(x.available)||x.steps.some(s=>typeof s.svg!=='string'||typeof s.explanation!=='string'||!Array.isArray(s.equations)))throw new Error('Lezione non interpretabile.');
 return x;
}
/** Stessa origine del motore, ma il markup resta un confine esplicito. */
function safeSvg(svg:string):string {
 const doc=new DOMParser().parseFromString(svg,'image/svg+xml');
 if(doc.querySelector('parsererror')||doc.documentElement.localName!=='svg')return '';
 const allowed=new Set(['svg','g','path','rect','circle','text']);
 for(const el of [...doc.querySelectorAll('*')]){
  if(!allowed.has(el.localName)){el.remove();continue;}
  for(const attr of [...el.attributes])if(/^on/i.test(attr.name)||/href/i.test(attr.name)||(/url\s*\(/i.test(attr.value))||attr.name==='style')el.removeAttribute(attr.name);
 }
 return new XMLSerializer().serializeToString(doc.documentElement);
}

export function StudentApp(){
 const [examples,setExamples]=useState<Example[]>([]),[example,setExample]=useState(''),[lesson,setLesson]=useState<Lesson|null>(null);
 const [step,setStep]=useState(0),[showOriginal,setShowOriginal]=useState(false),[method,setMethod]=useState('auto'),[expanded,setExpanded]=useState(false),[compare,setCompare]=useState(false),[zoom,setZoom]=useState(100);
 const [netlist,setNetlist]=useState(''),[draft,setDraft]=useState(''),[panel,setPanel]=useState(false),[tab,setTab]=useState('text');
 const [lessonImage,setLessonImage]=useState<string|null>(null);
 const [image,setImage]=useState<string|null>(null),[uncertainties,setUncertainties]=useState<string[]>([]),[confirmed,setConfirmed]=useState(false);
 const [api,setApi]=useState(false),[vision,setVision]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const request=useRef(0),stage=useRef<HTMLDivElement>(null);
 const entry=useRef(new URLSearchParams(location.hash.slice(1)));
 const restoreStep=useRef(true);
 const current=lesson?.steps[step];
 useEffect(()=>{if(step===0)setCompare(false);},[step]);
 useEffect(()=>{
  fetch('api/capabilities').then(r=>r.ok?r.json():null).then(v=>{setApi(Boolean(v?.solve));setVision(Boolean(v?.vision));}).catch(()=>undefined);
  fetch('lessons/index.json').then(response).then(v=>{
   const list=v as Example[];setExamples(list);
   const hash=new URLSearchParams(location.hash.slice(1));
   const first=list.find(e=>e.id===hash.get('exercise'))??list[0];
   if(first){setExample(first.id);setNetlist(first.netlist);setDraft(first.netlist);const requested=entry.current.get('method')??'auto';setMethod(first.methods[requested]?requested:'auto');}
  }).catch(()=>setError('Non riesco a caricare il catalogo. Riprova ricaricando la pagina.'));
 },[]);
 useEffect(()=>{
  const ex=examples.find(e=>e.id===example);if(!ex)return;
  const n=++request.current;setBusy(true);setLesson(null);setError('');
  const selected=ex.methods[method]?method:'auto';
  fetch(`lessons/${ex.methods[selected]}.json`).then(response).then(parseLesson).then(v=>{if(n===request.current){setLesson(v);const position=Number(entry.current.get('step')??0);setStep(restoreStep.current&&Number.isInteger(position)?Math.max(0,Math.min(v.steps.length-1,position)):0);setShowOriginal(restoreStep.current&&entry.current.get('original')==='1');restoreStep.current=false;setCompare(false);setZoom(100);}}).catch(e=>{if(n===request.current)setError(String(e));}).finally(()=>{if(n===request.current)setBusy(false);});
 },[example,examples,method]);
 useEffect(()=>{
  if(!lesson||!example||examples.find(e=>e.id===example)?.netlist!==lesson.netlist)return;
  const params=new URLSearchParams({exercise:example,method,step:String(step)});if(showOriginal)params.set('original','1');
  history.replaceState(null,'',`${location.pathname}${location.search}#${params}`);
 },[lesson,example,examples,method,step,showOriginal]);
 useEffect(()=>{
  function key(e:KeyboardEvent){
   if(e.key==='Escape'&&expanded){setExpanded(false);return;}
   if(panel||e.ctrlKey||e.altKey||e.metaKey||(e.target as HTMLElement).closest('input,textarea,select,[contenteditable]'))return;
   if(e.key==='ArrowRight'){setStep(n=>Math.min((lesson?.steps.length??1)-1,n+1));setShowOriginal(false);e.preventDefault();}
   if(e.key==='ArrowLeft'){setStep(n=>Math.max(0,n-1));setShowOriginal(false);e.preventDefault();}
  }
  window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);
 },[panel,lesson,expanded]);
 useEffect(()=>{
  if(!expanded)return;
  const prior=document.activeElement as HTMLElement|null;
  const sheet=document.querySelector<HTMLElement>('.student-lesson.is-expanded');
  sheet?.querySelector<HTMLElement>('.student-stage-head button')?.focus();
  function focus(e:KeyboardEvent){
   if(e.key!=='Tab'||!sheet)return;
   const items=[...sheet.querySelectorAll<HTMLElement>('button:not(:disabled),[tabindex="0"]')].filter(el=>el.getClientRects().length>0);
   if(!sheet.contains(document.activeElement)||(e.shiftKey&&document.activeElement===items[0])||(!e.shiftKey&&document.activeElement===items.at(-1))){e.preventDefault();(e.shiftKey?items.at(-1):items[0])?.focus();}
  }
  document.addEventListener('keydown',focus);return()=>{document.removeEventListener('keydown',focus);prior?.focus();};
 },[expanded]);
 useEffect(()=>{
  if(!panel)return;
  const previous=document.activeElement as HTMLElement|null;
  const dialog=document.querySelector<HTMLElement>('.student-dialog');
  dialog?.querySelector<HTMLElement>('button')?.focus();
  function trap(e:KeyboardEvent){
   if(e.key==='Escape'){setPanel(false);return;}
   if(e.key!=='Tab'||!dialog)return;
   const items=[...dialog.querySelectorAll<HTMLElement>('button:not(:disabled),input,textarea,select,[tabindex="0"]')].filter(el=>el.getClientRects().length>0);
   if(e.shiftKey&&document.activeElement===items[0]){e.preventDefault();items.at(-1)?.focus();}
   if(!e.shiftKey&&document.activeElement===items.at(-1)){e.preventDefault();items[0]?.focus();}
  }
  document.addEventListener('keydown',trap);return()=>{document.removeEventListener('keydown',trap);previous?.focus();};
 },[panel]);
 async function solve(text=draft,chosen=method){
  const n=++request.current;setBusy(true);setError('');
  try{
   if(!api)throw new Error('Per risolvere un nuovo circuito serve il server Kirchhoff. Il catalogo resta disponibile; questa pagina statica non contiene il solutore.');
   const value=parseLesson(await response(await fetch('api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist:text,method:chosen})})));
   if(n!==request.current)return;setLesson(value);setLessonImage(image);setExample('');history.replaceState(null,'',location.pathname+location.search);setNetlist(text);setDraft(text);setMethod(chosen);setStep(0);setShowOriginal(false);setCompare(false);setZoom(100);setPanel(false);
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}finally{if(n===request.current)setBusy(false);}
 }
 async function file(file:File|undefined){
  if(!file)return;setError('');setConfirmed(false);setUncertainties([]);
  if(file.type.startsWith('image/')){
   if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>2000000){setError('Usa una foto PNG, JPEG o WebP entro 2 MB.');return;}
   const reader=new FileReader();reader.onload=()=>{setImage(String(reader.result));setDraft('');setTab('photo');};reader.readAsDataURL(file);
  }else{if(file.size>16000){setError('Il file circuito supera 16000 caratteri.');return;}setDraft(await file.text());setImage(null);setTab('text');}
 }
 async function recognize(){
  if(!image)return;setBusy(true);setError('');
  try{const v=await response(await fetch('api/recognize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image})})) as {netlist:string;uncertainties:string[]};setDraft(v.netlist);setUncertainties(v.uncertainties);setConfirmed(false);}
  catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
 }
 async function pdf(){
  if(!lesson)return;setBusy(true);setError('');
  try{
   const ex=examples.find(e=>e.id===example);
   const res=ex?await fetch(`lessons/${ex.methods[method]??ex.methods.auto}.pdf`):await fetch('api/pdf',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist,method})});
   if(!res.ok){await response(res);return;}
   if(!res.headers.get('Content-Type')?.includes('application/pdf'))throw new Error('Documento PDF non disponibile.');
   const url=URL.createObjectURL(await res.blob()),a=document.createElement('a');a.href=url;a.download='Kirchhoff-circuito-passo-passo.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
 }
 function navigate(n:number){setStep(n);setShowOriginal(false);}
 return <div className="student-app">
  <header className="student-header"><a href="#" className="student-brand">Kirchhoff<span>con Andrea Marro</span></a><span className="student-tag">Capire il circuito, un passaggio alla volta</span><button onClick={()=>{setDraft(netlist);setTab('photo');setPanel(true);setError('');}}>Il tuo circuito <span aria-hidden="true">＋</span></button></header>
  <main className="student-main">
   <div className="student-heading"><div><p className="student-eyebrow">Il laboratorio dei circuiti</p><h1>Il circuito, passo per passo.</h1></div><p>Scegli una strada. Segui i disegni. Torna all’originale quando serve.</p></div>
   <div className="student-toolbar student-picker"><label>Esercizio <select aria-label="Scegli un circuito" value={example} disabled={busy} onChange={e=>{const ex=examples.find(x=>x.id===e.target.value);if(ex){setMethod('auto');setExample(ex.id);setNetlist(ex.netlist);setDraft(ex.netlist);setImage(null);setLessonImage(null);}}}>{!example?<option value="">Il tuo circuito</option>:null}{examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label><label>Metodo <select aria-label="Scegli il metodo" value={method} disabled={busy||!lesson} onChange={e=>{if(example)setMethod(e.target.value);else void solve(netlist,e.target.value);}}>{(lesson?.available??['auto']).map(m=><option key={m} value={m}>{names[m]}</option>)}</select></label><button disabled={busy||!lesson} onClick={()=>void pdf()}>Scarica PDF ↓</button></div>
   {error?<div className="student-error" role="alert">{error}</div>:null}
   {lesson&&current?<section className={`student-lesson ${expanded?"is-expanded":""}`} aria-busy={busy}>
    <nav className="student-outline" aria-label="Percorso ragionato"><p className="student-eyebrow">Il percorso</p><p className="student-route-method">{names[lesson.method]}</p><ol>{lesson.steps.map((s,i)=><li key={i}><button disabled={busy} aria-current={step===i?'step':undefined} onClick={()=>navigate(i)}><span className="student-step-number">{String(i+1).padStart(2,'0')}</span><span>{s.title}</span></button></li>)}</ol><p className="student-route-note">Ogni equivalente conserva una relazione. La domanda resta sul circuito originale.</p></nav>
    <div className="student-stage-head"><div><span className="student-eyebrow">{lesson.title} · {lesson.answer.reference}</span><h2>{showOriginal?'Il circuito da cui siamo partiti':current.title}</h2></div><button onClick={()=>setExpanded(!expanded)}>{expanded?'Riduci ↙':'Ingrandisci ↗'}</button><button aria-pressed={showOriginal} onClick={()=>{setShowOriginal(!showOriginal);setCompare(false);}}>{showOriginal?'Torna al passaggio':'Rivedi l’originale'}</button></div>
    <div className="student-view-tools"><span className="student-view-label">{showOriginal?'Schema di partenza':`Passaggio ${String(step+1).padStart(2,'0')}`}</span><button disabled={step===0||busy} aria-pressed={compare} onClick={()=>{setCompare(!compare);setShowOriginal(false);setZoom(100);}}>Confronta il precedente</button><div className="student-zoom" aria-label="Ingrandimento dello schema"><button aria-label="Riduci lo schema" disabled={zoom<=100} onClick={()=>setZoom(z=>z-25)}>−</button><span>{zoom}%</span><button aria-label="Ingrandisci lo schema" disabled={zoom>=200} onClick={()=>setZoom(z=>z+25)}>+</button></div></div>
    <div className={`student-schematics ${compare&&step>0?'is-comparing':''}`}>
     {compare&&step>0?<figure><figcaption>Prima · {lesson.steps[step-1].title}</figcaption><div className="student-drawing" tabIndex={0} aria-label="Circuito del passaggio precedente" dangerouslySetInnerHTML={{__html:safeSvg(lesson.steps[step-1].svg)}}/></figure>:null}
     <figure>{compare&&step>0?<figcaption>Ora · {current.title}</figcaption>:null}<div className="student-drawing" ref={stage} tabIndex={0} aria-label={showOriginal?'Circuito originale':'Circuito del passaggio'}><div className="student-svg" data-zoom={zoom} style={{width:`${zoom}%`,minWidth:`${(compare?350:460)*zoom/100}px`,flexShrink:0}} dangerouslySetInnerHTML={{__html:safeSvg(showOriginal?lesson.original:current.svg)}}/></div></figure>
    </div>
    <p className="student-pan-hint">↔ Puoi scorrere lo schema in orizzontale.</p>{showOriginal&&lessonImage?<figure className="student-source-image"><img src={lessonImage} alt="Foto originale da confrontare con lo schema ricostruito"/><figcaption>Foto di partenza: confrontala con lo schema ricostruito.</figcaption></figure>:null}<div className="student-navigation"><button aria-label="Passo precedente" disabled={step===0||busy} onClick={()=>navigate(step-1)}>← Indietro</button><span aria-live="polite">{String(step+1).padStart(2,'0')} / {String(lesson.steps.length).padStart(2,'0')}</span><button className="student-primary" aria-label="Passo successivo" disabled={step===lesson.steps.length-1||busy} onClick={()=>navigate(step+1)}>Avanti →</button></div>
    <div className="student-progress" aria-label="Passaggi">{lesson.steps.map((s,i)=><button key={i} title={s.title} aria-label={`Passaggio ${i+1}: ${s.title}`} aria-current={step===i?'step':undefined} onClick={()=>navigate(i)}><span/></button>)}</div>
    <div className="student-explanation" aria-live="polite"><p className="student-eyebrow">{showOriginal?'Collega il passaggio all’originale':'Perché facciamo questo passaggio'}</p><p>{current.explanation}</p>{current.equations.length?<div className="student-equations"><span className="student-eyebrow">Il calcolo, con i riferimenti scelti</span>{current.equations.map((e,i)=><p key={i}>{e}</p>)}</div>:null}{step===lesson.steps.length-1?<p className="student-result">{lesson.answer.exact} <span>{lesson.answer.unit} · ≈ {lesson.answer.decimal.replace('.',',')} {lesson.answer.unit}</span></p>:null}</div>
   </section>:<p role="status">{busy?'Preparo la lezione…':error?'Nessuna nuova lezione disponibile.':'Caricamento…'}</p>}
   <details className="student-scope"><summary>Cosa puoi risolvere in questa versione</summary><p>Circuiti resistivi in continua con sorgenti indipendenti. I percorsi a due morsetti includono partitori, Millman, equivalenti Thévenin e Norton e sovrapposizione. Per i ponti resistivi puoi usare stella → triangolo quando la grandezza cercata resta esterna alla stella. Per altre topologie DC il nucleo usa l’analisi nodale. AC, transitori e quadripoli non sono ancora coperti dall’esperienza didattica.</p><p>{api?'Puoi risolvere circuiti nuovi: il server locale è collegato.':'Stai usando il catalogo statico. Per risolvere circuiti nuovi occorre collegare il server Kirchhoff.'}</p></details>
   <details className="student-scope"><summary>Controllo del risultato e provenienza</summary><p>Il risultato elettrico proviene dal nucleo verificato; le derivazioni didattiche vengono confrontate in aritmetica esatta. Questa verifica del risultato non certifica da sola ogni scelta grafica e didattica.</p><code>{lesson?.source_sha}</code><p><a href={`?view=proof${location.hash}`}>Apri gli strumenti tecnici di verifica ↗</a></p></details>
  </main>
  {panel?<div className="student-overlay"><section role="dialog" aria-modal="true" aria-labelledby="input-title" className="student-dialog"><header><h2 id="input-title">Partiamo dal tuo circuito</h2><button aria-label="Chiudi ingresso circuito" onClick={()=>setPanel(false)}>Chiudi ×</button></header><div className="student-toolbar">{[['text','Componenti e collegamenti'],['photo','Foto o file'],['draw','Disegna sulla lavagna']].map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
   {error?<p role="alert" className="student-error">{error}</p>:null}
   {tab==='draw'?<CircuitEditor onUse={text=>{setDraft(text);setConfirmed(false);setTab('text');}}/>:<>
    {tab==='photo'?<div className="student-upload" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();void file(e.dataTransfer.files[0]);}}><label>Trascina una foto o un file circuito, oppure scegli un file<input type="file" accept="image/png,image/jpeg,image/webp,.txt,.net,.cir" onChange={e=>void file(e.target.files?.[0])}/></label>{image?<img src={image} alt="Il circuito caricato da confrontare con la ricostruzione"/>:null}{image?<><p>La foto resta sul dispositivo fino a quando scegli di inviarla per la trascrizione. Prima del calcolo controlla sempre valori, collegamenti e domanda.</p><button disabled={!vision||busy} onClick={()=>void recognize()}>Invia a OpenAI e trascrivi</button>{!vision?<p>Riconoscimento automatico non configurato. Puoi ricostruire il circuito con la lavagna o nel campo qui sotto.</p>:null}</>:null}</div>:null}
    <label className="student-netlist">Componenti, nodi e domanda<textarea aria-label="Circuito da risolvere" spellCheck={false} value={draft} onChange={e=>{setDraft(e.target.value);setConfirmed(false);}} placeholder={'V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2'}/></label><details><summary>Come leggere e modificare il circuito</summary><p>Ogni riga contiene nome, primo nodo, secondo nodo, valore e unità. R = resistore (ohm), V = sorgente di tensione (volt), I = sorgente di corrente (ampere). Il nodo 0 è il riferimento. Valori decimali o frazioni sono esatti. L’ultima riga indica la domanda: <code>? voltage R2</code> oppure <code>? current R2</code>. I file SPICE completi non sono ancora accettati.</p></details>
    {uncertainties.length?<ul>{uncertainties.map((u,i)=><li key={i}>{u}</li>)}</ul>:null}
    {image?<label className="student-confirm"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>Ho confrontato con la foto e corretto valori, nodi, versi e domanda.</label>:null}
    <div className="student-dialog-actions"><button className="student-primary" disabled={busy||!draft.trim()||Boolean(image&&!confirmed)} onClick={()=>void solve(draft,'auto')}>{busy?'Preparo i passaggi…':'Risolvi e spiega →'}</button><button onClick={()=>{const url=URL.createObjectURL(new Blob([draft],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='circuito.net';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}>Salva circuito</button></div>
   </>}
  </section></div>:null}
 </div>;
}
