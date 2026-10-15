import {useEffect,useRef,useState} from 'react';
import {cropSourceImage,openPdfSource,validateCrop,wholePage} from './documentInput';
import type {Crop} from './documentInput';
import {preserveImageFile} from './sourceArtifact';
import type {SourceArtifact,SourceFile,SourceSelection} from './sourceArtifact';

export type PreparedSource={image:string;original:SourceFile;kind:SourceArtifact['kind'];selection:SourceSelection};
export function SourcePagePicker({file,onUse,onCancel}:{file:File;onUse:(source:PreparedSource)=>void;onCancel:()=>void}){
 const [page,setPage]=useState(1),[total,setTotal]=useState(0),[preview,setPreview]=useState(''),[crop,setCrop]=useState<Crop>(wholePage);
 const [busy,setBusy]=useState(true),[error,setError]=useState('');
 const document=useRef<Awaited<ReturnType<typeof openPdfSource>>|null>(null),original=useRef<SourceFile|null>(null),request=useRef(0);
 const isPdf=file.type==='application/pdf';
 useEffect(()=>{
  let active=true;setBusy(true);setError('');setPage(1);setTotal(0);setPreview('');setCrop(wholePage);
  const preserved=preserveImageFile(file);
  const opened=isPdf?openPdfSource(file):Promise.resolve(null);
  void Promise.all([preserved,opened]).then(async([source,openedDocument])=>{
   if(!active){await openedDocument?.dispose();return;}
   original.current=source;document.current=openedDocument;
   if(openedDocument)setTotal(openedDocument.pdf.numPages);
   else{setPreview(source.dataURL);setBusy(false);}
  }).catch(e=>{void opened.then(d=>d?.dispose()).catch(()=>undefined);if(active){setError(e instanceof Error?e.message:'Documento non leggibile.');setBusy(false);}});
  return()=>{active=false;request.current++;void document.current?.dispose();document.current=null;};
 },[file,isPdf]);
 useEffect(()=>{
  const owner=document.current;if(!owner||!total)return;
  const n=++request.current;setBusy(true);setError('');setCrop(wholePage);
  void owner.pdf.getPage(page).then(async pdfPage=>{
   const unscaled=pdfPage.getViewport({scale:1});
   const viewport=pdfPage.getViewport({scale:Math.min(2,2000/Math.max(unscaled.width,unscaled.height))});
   const canvas=window.document.createElement('canvas');canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
   await pdfPage.render({canvas,viewport}).promise;
   if(n===request.current){setPreview(canvas.toDataURL('image/png'));setBusy(false);}
   pdfPage.cleanup();
  }).catch(e=>{if(n===request.current){setError(e instanceof Error?e.message:'Pagina non leggibile.');setBusy(false);}});
 },[page,total]);
 async function useSource(){
  if(!original.current||!preview)return;const n=++request.current;setBusy(true);setError('');
  try{const image=await cropSourceImage(preview,crop);if(n===request.current)onUse({image,original:original.current,kind:isPdf?'pdf':'image',selection:{page:isPdf?page:null,totalPages:isPdf?total:null,crop}});}
  catch(e){if(n===request.current){setError(e instanceof Error?e.message:'Ritaglio non disponibile.');setBusy(false);}}
 }
 let valid=true;try{validateCrop(crop);}catch{valid=false;}
 return <section aria-label="Pagina e ritaglio della fonte">
  <h3>{file.name}</h3><p>Il documento resta locale. Scegli la pagina e la zona che contiene il circuito e la domanda.</p>
  {isPdf&&total>0?<label>Pagina del PDF <input aria-label="Pagina del PDF" type="number" min={1} max={total} value={page} disabled={busy} onChange={e=>{const p=Number(e.target.value);if(Number.isInteger(p)&&p>=1&&p<=total)setPage(p);}}/> di {total}</label>:null}
  {preview?<div style={{position:'relative',maxWidth:600,margin:'12px auto'}}><img src={preview} alt="Pagina originale da ritagliare" style={{display:'block',width:'100%'}}/>{valid?<div aria-hidden="true" style={{position:'absolute',left:`${crop.x*100}%`,top:`${crop.y*100}%`,width:`${crop.width*100}%`,height:`${crop.height*100}%`,border:'2px solid #294bd3',background:'rgba(41,75,211,.08)',boxSizing:'border-box',pointerEvents:'none'}}/>:null}</div>:null}
  <fieldset disabled={busy} style={{display:'flex',gap:12,flexWrap:'wrap'}}><legend>Ritaglio (% della pagina)</legend>{([['x','Da sinistra'],['y','Dall’alto'],['width','Larghezza'],['height','Altezza']] as const).map(([key,label])=><label key={key}>{label}<input aria-label={`${label} ritaglio percentuale`} style={{width:80,display:'block'}} type="number" min={0} max={100} value={Math.round(crop[key]*10000)/100} onChange={e=>setCrop({...crop,[key]:Number(e.target.value)/100})}/></label>)}</fieldset>
  {!valid?<p role="alert">Il ritaglio deve restare dentro la pagina.</p>:null}{error?<p role="alert">{error}</p>:null}
  <div className="student-dialog-actions"><button type="button" disabled={busy||!preview||!valid} onClick={()=>void useSource()}>{busy?'Preparo la pagina…':'Usa pagina e ritaglio'}</button><button type="button" onClick={onCancel}>Annulla scelta della fonte</button></div>
 </section>;
}
