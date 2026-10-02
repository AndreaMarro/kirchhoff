import {useEffect,useRef,useState} from 'react';
import {CircuitEditor} from './CircuitEditor.tsx';
import {StudentTracePanel,blankTraceStep} from './StudentTracePanel.tsx';
import type {TraceStep} from './StudentTracePanel.tsx';
import {makeSessionBundle,readSessionBundle} from './sessionBundle.ts';
import './student.css';
import {prepareCircuitImage} from './imageInput.ts';
import {readBoardMessage} from './boardProtocol.ts';
import {safeSvg} from './safeSvg.ts';

type Step={title:string;explanation:string;svg:string;equations:string[];focus:string[]};
type Lesson={schema:string;outcome:'solved';title:string;netlist:string;method:string;available:string[];original:string;steps:Step[];answer:{exact:string;decimal:string;unit:string;reference:string};fingerprint:string;source_sha:string;input_provenance?:{source_kind:string;source_sha256:string;circuit_sha256:string;confirmed_at_unix:number}};
type Example={id:string;title:string;netlist:string;methods:Record<string,string>};
type ImageObservation={line:string;region:{x1:number;y1:number;x2:number;y2:number}};
type ImageCandidate={netlist:string;observations:ImageObservation[];uncertainties:string[];model_reported_complete:boolean};
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
export function StudentApp(){
 const [examples,setExamples]=useState<Example[]>([]),[example,setExample]=useState(''),[lesson,setLesson]=useState<Lesson|null>(null);
 const [step,setStep]=useState(0),[showOriginal,setShowOriginal]=useState(false),[method,setMethod]=useState('auto'),[expanded,setExpanded]=useState(false),[compare,setCompare]=useState(false),[zoom,setZoom]=useState(100);
 const [netlist,setNetlist]=useState(''),[draft,setDraft]=useState(''),[panel,setPanel]=useState(false),[tab,setTab]=useState('text');
 const [lessonImage,setLessonImage]=useState<string|null>(null);
 const [photoConfirmationToken,setPhotoConfirmationToken]=useState<string|null>(null);
 const [image,setImage]=useState<string|null>(null),[imageFromBoard,setImageFromBoard]=useState(false),[uncertainties,setUncertainties]=useState<string[]>([]),[confirmed,setConfirmed]=useState(false);
 const [observations,setObservations]=useState<ImageObservation[]>([]),[selectedObservation,setSelectedObservation]=useState(0),[modelReportedComplete,setModelReportedComplete]=useState<boolean|null>(null);
 const [candidates,setCandidates]=useState<ImageCandidate[]>([]);
 const [api,setApi]=useState(false),[vision,setVision]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [scope,setScope]=useState('');
 const request=useRef(0),stage=useRef<HTMLDivElement>(null),board=useRef<HTMLIFrameElement>(null),boardScene=useRef(''),boardOwner=useRef<string|null>(null);
 const sessionInput=useRef<HTMLInputElement>(null),boardSnapshot=useRef(new Map<string,{resolve:(scene:string)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}>());
 const [boardOpened,setBoardOpened]=useState(false);
 const [boardEpoch,setBoardEpoch]=useState(0),[sessionEpoch,setSessionEpoch]=useState(0);
 const [traceState,setTraceState]=useState<{fingerprint:string;steps:TraceStep[]}>({fingerprint:'',steps:[blankTraceStep()]});
 const entry=useRef(new URLSearchParams(location.hash.slice(1)));
 const restoreStep=useRef(true);
 const current=lesson?.steps[step];
 useEffect(()=>{if(step===0)setCompare(false);},[step]);
 useEffect(()=>{
  function receive(e:MessageEvent){
   const message=readBoardMessage(e,board.current?.contentWindow,location.origin);if(!message)return;
   if(message.type==='kirchhoff:board-ready')board.current?.contentWindow?.postMessage({type:'kirchhoff:board-init',scene:boardScene.current},location.origin);
   if(message.type==='kirchhoff:board-state')boardScene.current=message.scene;
   if(message.type==='kirchhoff:board-snapshot'){
    const pending=boardSnapshot.current.get(message.requestId);
    if(pending){clearTimeout(pending.timer);boardSnapshot.current.delete(message.requestId);boardScene.current=message.scene;pending.resolve(message.scene);}
   }
   if(message.type==='kirchhoff:board-image'){request.current++;boardOwner.current=null;setImage(message.image);setImageFromBoard(true);setDraft('');setUncertainties([]);setObservations([]);setCandidates([]);setModelReportedComplete(null);setConfirmed(false);setTab('photo');setError('');}
  }
  window.addEventListener('message',receive);return()=>{
   window.removeEventListener('message',receive);
   for(const pending of boardSnapshot.current.values()){clearTimeout(pending.timer);pending.reject(new Error('La pagina è stata chiusa prima del salvataggio.'));}
   boardSnapshot.current.clear();
  };
 },[]);
 useEffect(()=>{
  fetch('api/capabilities').then(r=>r.ok?r.json():null).then(v=>{setApi(Boolean(v?.solve));setVision(Boolean(v?.vision));setScope(typeof v?.scope==='string'?v.scope:'');}).catch(()=>undefined);
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
 async function solve(text=draft,chosen=method,sourceImageOverride?:string|null,existingToken?:string|null){
  const n=++request.current;setBusy(true);setError('');setNotice('');
  try{
   if(!api)throw new Error('Per risolvere un nuovo circuito serve il server Kirchhoff. Il catalogo resta disponibile; questa pagina statica non contiene il solutore.');
   const sourceImage=sourceImageOverride===undefined?image:sourceImageOverride;
   let confirmationToken=existingToken??null;
   if(sourceImage&&!confirmationToken){
    if(!confirmed)throw new Error('Confronta la foto con il circuito e conferma questa revisione prima del calcolo.');
    const source=await response(await fetch('api/source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:sourceImage})})) as {source_token:string};
    if(n!==request.current)return;
    const approval=await response(await fetch('api/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_token:source.source_token,netlist:text,confirmed:true})})) as {confirmation_token:string};
    if(n!==request.current)return;confirmationToken=approval.confirmation_token;
   }
   const value=parseLesson(await response(await fetch('api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist:text,method:chosen,source_kind:sourceImage?'image':'netlist',confirmation_token:confirmationToken})})));
   if(n!==request.current)return;if(imageFromBoard&&sourceImage)boardOwner.current=value.fingerprint;
   setLesson(value);setLessonImage(sourceImage);setPhotoConfirmationToken(confirmationToken);setExample('');history.replaceState(null,'',location.pathname+location.search);setNetlist(text);setDraft(text);setMethod(chosen);setStep(0);setShowOriginal(false);setCompare(false);setZoom(100);setPanel(false);
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}finally{if(n===request.current)setBusy(false);}
 }
 async function file(file:File|undefined){
  if(!file)return;const n=++request.current;setError('');setConfirmed(false);setUncertainties([]);setObservations([]);setCandidates([]);setModelReportedComplete(null);
  if(file.type.startsWith('image/')){
   try{const value=await prepareCircuitImage(file);if(n!==request.current)return;setImage(value);setImageFromBoard(false);setDraft('');setTab('photo');}catch(e){if(n===request.current)setError(e instanceof Error?e.message:'Foto non leggibile.');}
  }else{
   if(file.size>16000){setError('Il file circuito supera 16000 caratteri.');return;}
   try{
    let value=await file.text();if(n!==request.current)return;
    if(/\.(cir|spice|sp)$/i.test(file.name)){
     if(!api)throw new Error('Per importare SPICE serve il server Kirchhoff.');
     const imported=await response(await fetch('api/spice/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spice:value})})) as {netlist:string};
     value=imported.netlist;
    }
    if(n!==request.current)return;setDraft(value);setImage(null);setImageFromBoard(false);setTab('text');
   }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}
  }
 }
 async function recognize(){
  if(!image)return;const n=++request.current;setBusy(true);setError('');
  try{const v=await response(await fetch('api/recognize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image})})) as {netlist:string;uncertainties:string[];observations:ImageObservation[];model_reported_complete:boolean;candidates?:ImageCandidate[]};if(n!==request.current)return;if(typeof v.netlist!=='string'||typeof v.model_reported_complete!=='boolean'||!Array.isArray(v.uncertainties)||!Array.isArray(v.observations)||!Array.isArray(v.candidates??[]))throw new Error('Trascrizione non interpretabile. Ricostruisci il circuito manualmente.');setDraft(v.netlist);setUncertainties(v.uncertainties);setObservations(v.observations);setCandidates(v.candidates??[]);setSelectedObservation(0);setModelReportedComplete(v.model_reported_complete);setConfirmed(false);}
  catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}finally{if(n===request.current)setBusy(false);}
 }
 async function pdf(){
  if(!lesson)return;setBusy(true);setError('');
  try{
   const ex=examples.find(e=>e.id===example);
   const res=ex?await fetch(`lessons/${ex.methods[method]??ex.methods.auto}.pdf`):await fetch('api/pdf',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist,method,source_kind:lessonImage?'image':'netlist',confirmation_token:photoConfirmationToken})});
   if(!res.ok){await response(res);return;}
   if(!res.headers.get('Content-Type')?.includes('application/pdf'))throw new Error('Documento PDF non disponibile.');
   const url=URL.createObjectURL(await res.blob()),a=document.createElement('a');a.href=url;a.download='Kirchhoff-circuito-passo-passo.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
 }
 async function spice(){
  if(!lesson||!api)return;setBusy(true);setError('');
  try{
   const value=await response(await fetch('api/spice/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist:lesson.netlist})})) as {spice:string};
   const url=URL.createObjectURL(new Blob([value.spice],{type:'text/plain'})),a=document.createElement('a');a.href=url;a.download='circuito-DC.cir';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
 }
 async function circuitikz(){
  if(!lesson||!api)return;setBusy(true);setError('');
  try{
   const value=await response(await fetch('api/circuitikz/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({netlist:lesson.netlist})})) as {tex:string};
   const url=URL.createObjectURL(new Blob([value.tex],{type:'text/plain'})),a=document.createElement('a');a.href=url;a.download='circuito-kirchhoff.tex';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
 }
 async function currentBoardScene():Promise<string>{
  if(!boardOpened)return boardScene.current;
  const frame=board.current?.contentWindow;
  if(!frame)throw new Error('Lavagna non pronta: attendi che si apra e riprova.');
  const requestId=crypto.randomUUID();
  return new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>{boardSnapshot.current.delete(requestId);reject(new Error('La lavagna non ha risposto: il quaderno non è stato salvato.'));},2500);
   boardSnapshot.current.set(requestId,{resolve,reject,timer});
   frame.postMessage({type:'kirchhoff:board-snapshot-request',requestId},location.origin);
  });
 }
 async function saveSession(){
  if(!lesson)return;const n=request.current;setBusy(true);setError('');setNotice('');
  try{
   let scene=await currentBoardScene();
   if(n!==request.current)return;
   if(scene){
    const parsed=JSON.parse(scene) as {elements?:unknown[]};
    if(parsed.elements?.length&&boardOwner.current!==lesson.fingerprint)
     throw new Error('La lavagna appartiene a un’altra revisione: aprila e associala esplicitamente alla lezione corrente.');
    if(!parsed.elements?.length)scene='';
   }
   const bundle=await makeSessionBundle({netlist:lesson.netlist,method,answerExact:lesson.answer.exact,
    engineRevision:lesson.source_sha,selectedStep:step,showOriginal,boardScene:scene,
    traceSteps:traceState.fingerprint===lesson.fingerprint?traceState.steps:[blankTraceStep()],
    priorImageSha256:lesson.input_provenance?.source_sha256??null});
   if(n!==request.current)return;
   const data=JSON.stringify(bundle);
   if(data.length>10_500_000)throw new Error('Il quaderno supera 10 MB. Riduci le immagini nella lavagna.');
   const url=URL.createObjectURL(new Blob([data],{type:'application/json'})),a=document.createElement('a');
   a.href=url;a.download='quaderno-kirchhoff.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
   setNotice('Quaderno salvato sul tuo dispositivo. Alla riapertura la soluzione sarà ricalcolata.');
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}finally{if(n===request.current)setBusy(false);}
 }
 async function openSession(file:File|undefined){
  if(!file)return;const n=++request.current;setBusy(true);setError('');setNotice('');
  try{
   if(!api)throw new Error('Per riaprire un quaderno serve il server Kirchhoff.');
   if(file.size>10_500_000)throw new Error('Il quaderno supera 10 MB.');
   const bundle=await readSessionBundle(await file.text());if(n!==request.current)return;
   const value=parseLesson(await response(await fetch('api/solve',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({netlist:bundle.netlist,method:bundle.method,source_kind:'netlist'})})));
   if(n!==request.current)return;
   if(value.fingerprint!==bundle.circuitFingerprint||value.answer.exact!==bundle.answerExact)
    throw new Error('Il risultato salvato non coincide con la nuova verifica: il quaderno resta chiuso.');
   boardScene.current=bundle.boardScene;boardOwner.current=bundle.boardScene?value.fingerprint:null;setBoardEpoch(x=>x+1);if(bundle.boardScene)setBoardOpened(true);
   setTraceState({fingerprint:value.fingerprint,steps:bundle.traceSteps});setSessionEpoch(x=>x+1);
   setLesson(value);setLessonImage(null);setPhotoConfirmationToken(null);setImage(null);setImageFromBoard(false);setConfirmed(false);setUncertainties([]);setObservations([]);setCandidates([]);setModelReportedComplete(null);
   setExample('');setNetlist(bundle.netlist);setDraft(bundle.netlist);setMethod(bundle.method);setStep(Math.min(bundle.selectedStep,value.steps.length-1));
   setShowOriginal(bundle.showOriginal);setCompare(false);setZoom(100);setPanel(false);
   const revisionNotice=bundle.engineRevision!==value.source_sha?' Il motore è cambiato; la soluzione mostrata è quella appena ricalcolata.':'';
   setNotice((bundle.priorImageSha256?'Quaderno riaperto e soluzione ricalcolata. La foto originale non è inclusa: la vecchia conferma fotografica non è stata ripristinata.':'Quaderno riaperto e soluzione ricalcolata dal circuito salvato.')+revisionNotice);
  }catch(e){if(n===request.current)setError(e instanceof Error?e.message:String(e));}finally{if(n===request.current)setBusy(false);}
 }
 function navigate(n:number){setStep(n);setShowOriginal(false);}
 return <div className="student-app">
  <header className="student-header"><a href="#" className="student-brand">Kirchhoff<span>con Andrea Marro</span></a><span className="student-tag">Capire il circuito, un passaggio alla volta</span><button onClick={()=>{setTab('photo');setPanel(true);setError('');}}>Il tuo circuito <span aria-hidden="true">＋</span></button></header>
  <main className="student-main">
   <div className="student-heading"><div><p className="student-eyebrow">Il laboratorio dei circuiti</p><h1>Il circuito, passo per passo.</h1></div><p>Scegli una strada. Segui i disegni. Torna all’originale quando serve.</p></div>
   <div className="student-toolbar student-picker"><label>Esercizio <select aria-label="Scegli un circuito" value={example} disabled={busy} onChange={e=>{const ex=examples.find(x=>x.id===e.target.value);if(ex){setMethod('auto');setExample(ex.id);setNetlist(ex.netlist);setDraft(ex.netlist);setImage(null);setImageFromBoard(false);setLessonImage(null);setPhotoConfirmationToken(null);}}}>{!example?<option value="">Il tuo circuito</option>:null}{examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label><label>Metodo <select aria-label="Scegli il metodo" value={method} disabled={busy||!lesson} onChange={e=>{if(example)setMethod(e.target.value);else void solve(netlist,e.target.value,lessonImage,photoConfirmationToken);}}>{(lesson?.available??['auto']).map(m=><option key={m} value={m}>{names[m]}</option>)}</select></label><button disabled={busy||!lesson||!api} onClick={()=>void circuitikz()}>Scarica CircuitikZ ↓</button><button disabled={busy||!lesson||!api} onClick={()=>void spice()}>Scarica SPICE ↓</button><button disabled={busy||!lesson} onClick={()=>void pdf()}>Scarica PDF ↓</button></div>
   <div className="student-toolbar student-session-actions"><button disabled={busy||!lesson} onClick={()=>void saveSession()}>Salva quaderno ↓</button><button disabled={busy} onClick={()=>sessionInput.current?.click()}>Apri quaderno ↑</button><input ref={sessionInput} type="file" accept=".json,application/json" hidden onChange={e=>{void openSession(e.target.files?.[0]);e.target.value='';}}/></div>
   {error?<div className="student-error" role="alert">{error}</div>:null}
   {notice?<p role="status">{notice}</p>:null}
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
   {lesson&&api?<StudentTracePanel key={`${lesson.fingerprint}:${sessionEpoch}`} netlist={lesson.netlist} fingerprint={lesson.fingerprint} steps={traceState.fingerprint===lesson.fingerprint?traceState.steps:[blankTraceStep()]} onStepsChange={steps=>setTraceState({fingerprint:lesson.fingerprint,steps})}/>:null}
   <details className="student-scope"><summary>Cosa puoi risolvere in questa versione</summary><p>{scope||'Circuiti resistivi in continua con sorgenti indipendenti. AC e transitori non sono ancora coperti dalla lezione.'}</p><p>{api?'Puoi risolvere circuiti nuovi: il server locale è collegato.':'Stai usando il catalogo statico. Per risolvere circuiti nuovi occorre collegare il server Kirchhoff.'}</p></details>
   <details className="student-scope"><summary>Controllo del risultato e provenienza</summary><p>Il risultato elettrico proviene dal nucleo verificato; le derivazioni didattiche vengono confrontate in aritmetica esatta. Questa verifica del risultato non certifica da sola ogni scelta grafica e didattica.</p><p>Versione del motore: <code>{lesson?.source_sha}</code></p>{lesson?.input_provenance?<><p>Immagine preparata per l’analisi: <code>{lesson.input_provenance.source_sha256}</code></p><p>Circuito corretto e confermato: <code>{lesson.input_provenance.circuit_sha256}</code></p><p>Confermato il {new Date(lesson.input_provenance.confirmed_at_unix*1000).toLocaleString('it-IT')}.</p><p>La conferma lega questa revisione all’immagine preparata; non certifica che la trascrizione sia fedele.</p></>:null}<p><a href={`?view=proof${location.hash}`}>Apri gli strumenti tecnici di verifica ↗</a></p></details>
  </main>
  {panel||boardOpened?<div className="student-overlay" hidden={!panel}><section role="dialog" aria-modal="true" aria-labelledby="input-title" className="student-dialog" onPaste={e=>{const photo=[...e.clipboardData.files].find(f=>f.type.startsWith('image/'));if(photo){e.preventDefault();void file(photo);}}}><header><h2 id="input-title">Partiamo dal tuo circuito</h2><button aria-label="Chiudi ingresso circuito" onClick={()=>setPanel(false)}>Chiudi ×</button></header><div className="student-toolbar">{[['text','Testo del circuito'],['photo','Foto o file'],['draw','Schema a componenti'],['free','Lavagna libera']].map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>{setTab(id);if(id==='free'){if(!boardScene.current)boardOwner.current=lesson?.fingerprint??null;setBoardOpened(true);}}}>{label}</button>)}</div>
   {error?<p role="alert" className="student-error">{error}</p>:null}
  {boardOpened?<div className="student-free-board" hidden={tab!=='free'}><iframe key={boardEpoch} ref={board} title="Lavagna libera Excalidraw" src="board/index.html"/></div>:null}
   {tab==='free'?<div className="student-dialog-actions"><button disabled={!lesson} onClick={()=>{if(lesson){boardOwner.current=lesson.fingerprint;setNotice('Lavagna associata alla revisione corrente della lezione.');}}}>Associa lavagna alla lezione corrente</button></div>:tab==='draw'?<CircuitEditor onUse={text=>{request.current++;setDraft(text);setImage(null);setImageFromBoard(false);setUncertainties([]);setObservations([]);setModelReportedComplete(null);setConfirmed(false);setTab('text');}}/>:<>
    {tab==='photo'?<div className="student-upload" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();void file(e.dataTransfer.files[0]);}}><label>Trascina o incolla una foto, oppure scegli un file circuito<span className="student-file-help">PNG, JPEG o WebP fino a 20 MB; netlist .net/.txt o SPICE DC .cir/.spice.</span><input type="file" accept="image/png,image/jpeg,image/webp,.txt,.net,.cir,.sp,.spice" onChange={e=>void file(e.target.files?.[0])}/></label>{image?<div style={{position:'relative',display:'inline-block',maxWidth:'100%',margin:'15px 0',lineHeight:0}}><img src={image} alt="Il circuito caricato da confrontare con la ricostruzione" style={{display:'block',maxWidth:'100%',margin:0}}/>{observations[selectedObservation]?<span aria-hidden="true" data-source-region={selectedObservation} style={{position:'absolute',left:`${observations[selectedObservation].region.x1/10}%`,top:`${observations[selectedObservation].region.y1/10}%`,width:`${(observations[selectedObservation].region.x2-observations[selectedObservation].region.x1)/10}%`,height:`${(observations[selectedObservation].region.y2-observations[selectedObservation].region.y1)/10}%`,border:'2px solid #c25332',background:'rgba(194,83,50,.15)',boxSizing:'border-box',pointerEvents:'none'}}/>:null}</div>:null}{image?<><p>La foto resta sul dispositivo fino a quando scegli di inviarla per la trascrizione. Prima del calcolo controlla sempre valori, collegamenti e domanda.</p><button disabled={!vision||busy} onClick={()=>void recognize()}>Invia a OpenAI e trascrivi</button>{!vision?<p>Riconoscimento automatico non configurato. Ricostruisci il circuito con “Schema a componenti” oppure nel campo qui sotto. Il disegno libero e la foto richiedono una trascrizione confermata.</p>:null}</>:null}</div>:null}
    {observations.length?<section aria-label="Origine delle righe lette"><p>Posizioni proposte dal modello: seleziona una riga e confrontala con la zona evidenziata nella foto. Non dimostrano che il circuito sia completo.</p><ol>{observations.map((item,i)=><li key={i}><button type="button" aria-pressed={selectedObservation===i} onClick={()=>setSelectedObservation(i)}>{item.line}</button></li>)}</ol></section>:null}
    {candidates.length>1?<section aria-label="Letture alternative della foto"><p>Le letture non coincidono. Seleziona un'ipotesi, confrontala con la foto e correggi il testo.</p>{candidates.map((candidate,i)=><button key={i} type="button" onClick={()=>{request.current++;setDraft(candidate.netlist);setObservations(candidate.observations);setSelectedObservation(0);setModelReportedComplete(false);setConfirmed(false);}}>Lettura {i+1}</button>)}</section>:null}
    {modelReportedComplete===false?<p role="status">La lettura è incompleta o discordante. Correggi il circuito dalla foto prima di confermare.</p>:null}
    <label className="student-netlist">Componenti, nodi e domanda<textarea aria-label="Circuito da risolvere" spellCheck={false} value={draft} onChange={e=>{request.current++;setDraft(e.target.value);setObservations([]);setCandidates([]);setUncertainties([]);setModelReportedComplete(null);setConfirmed(false);}} placeholder={'V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2'}/></label><details><summary>Come leggere e modificare il circuito</summary><p>Ogni riga contiene nome, primo nodo, secondo nodo, valore e unità. R = resistore (ohm), V = sorgente di tensione (volt), I = sorgente di corrente (ampere). Il nodo 0 è il riferimento. Valori decimali o frazioni sono esatti. L’ultima riga indica la domanda: <code>? voltage R2</code> oppure <code>? current R2</code>. SPICE: questa versione importa solo R/C/L, V/I DC, E/G, .op e .end; una direttiva sconosciuta viene rifiutata.</p></details>
    {uncertainties.length?<ul>{uncertainties.map((u,i)=><li key={i}>{u}</li>)}</ul>:null}
    {image?<label className="student-confirm"><input type="checkbox" checked={confirmed} disabled={modelReportedComplete===false} onChange={e=>{request.current++;setConfirmed(e.target.checked);}}/>Ho confrontato con la foto e corretto valori, nodi, versi e domanda.</label>:null}
    <div className="student-dialog-actions"><button className="student-primary" disabled={busy||!draft.trim()||Boolean(image&&(!confirmed||modelReportedComplete===false))} onClick={()=>void solve(draft,'auto')}>{busy?'Preparo i passaggi…':'Risolvi e spiega →'}</button><button onClick={()=>{const url=URL.createObjectURL(new Blob([draft],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='circuito.net';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}>Salva circuito</button></div>
   </>}
  </section></div>:null}
 </div>;
}
