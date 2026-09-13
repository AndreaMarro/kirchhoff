/// <reference types="vite/client" />
// Integrazione di Excalidraw 0.18.1 già impiegato da MAESTRO-Studio/Room.tsx.
// Scena e foto passano solo al parent della stessa origine, mai a un servizio remoto.
import React, {useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Excalidraw,exportToBlob,serializeAsJSON} from '@excalidraw/excalidraw';
import type {ExcalidrawImperativeAPI} from '@excalidraw/excalidraw/types';
import '@excalidraw/excalidraw/index.css';
import './style.css';
window.EXCALIDRAW_ASSET_PATH=new URL('./',location.href).href;
declare global {interface Window {EXCALIDRAW_ASSET_PATH:string}}
const origin=location.origin;
function download(blob:Blob,name:string){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function Board(){
 const api=useRef<ExcalidrawImperativeAPI|null>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null);
 const [initial,setInitial]=useState<object|null|undefined>(undefined),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{
  function receive(e:MessageEvent){if(e.origin!==origin||e.source!==parent||e.data?.type!=='kirchhoff:board-init')return;try{const scene=e.data.scene?JSON.parse(e.data.scene):null;if(scene&&!Array.isArray(scene.elements))throw Error();setInitial(scene);}catch{setError('Scena non interpretabile. Apri il disegno salvato dal menu.');setInitial(null);}}
  window.addEventListener('message',receive);
  if(parent===window)setInitial(null);else parent.postMessage({type:'kirchhoff:board-ready'},origin);
  return()=>{window.removeEventListener('message',receive);if(timer.current)clearTimeout(timer.current);};
 },[]);
 function snapshot(){if(!api.current)return '';return serializeAsJSON(api.current.getSceneElements(),api.current.getAppState(),api.current.getFiles(),'local');}
 function changed(){if(timer.current)clearTimeout(timer.current);timer.current=setTimeout(()=>{const scene=snapshot();if(scene.length<=10000000)parent.postMessage({type:'kirchhoff:board-state',scene},origin);},400);}
 async function useDrawing(){
  if(!api.current)return;
  if(!api.current.getSceneElements().length){setError('Disegna il circuito o trascina una foto prima di continuare.');return;}
  setBusy(true);setError('');
  try{
   const options={elements:api.current.getSceneElements(),appState:{...api.current.getAppState(),exportBackground:true,viewBackgroundColor:'#ffffff',exportWithDarkMode:false},files:api.current.getFiles(),maxWidthOrHeight:1800,exportPadding:35};
   let blob=await exportToBlob(options);if(blob.size>2000000)blob=await exportToBlob({...options,mimeType:'image/jpeg',quality:.88});
   if(blob.size>2000000)throw Error('Il disegno è troppo grande: riduci le immagini inserite.');
   const dataURL=await new Promise<string>((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result));r.onerror=()=>reject(Error('Esportazione immagine fallita.'));r.readAsDataURL(blob);});
   const scene=snapshot();if(scene.length<=10000000)parent.postMessage({type:'kirchhoff:board-state',scene},origin);
   if(parent===window)download(blob,blob.type==='image/jpeg'?'circuito.jpg':'circuito.png');else parent.postMessage({type:'kirchhoff:board-image',image:dataURL},origin);
  }catch(e){setError(e instanceof Error?e.message:'Esportazione non riuscita.');}finally{setBusy(false);}
 }
 return <main className="board-shell"><header><div><strong>La tua lavagna</strong><span>Disegna, scrivi i valori, indica la domanda.</span></div><button disabled={busy} onClick={()=>download(new Blob([snapshot()],{type:'application/json'}),'circuito.excalidraw')}>Salva disegno</button><button className="primary" disabled={busy} onClick={()=>void useDrawing()}>{busy?'Preparo l’immagine…':'Usa questo disegno →'}</button></header>{error?<p role="alert">{error}</p>:null}<section aria-label="Lavagna Excalidraw">{initial!==undefined?<Excalidraw initialData={initial??{appState:{currentItemStrokeColor:'#202b37',currentItemRoughness:0,currentItemFontFamily:2,viewBackgroundColor:'#ffffff'}}} excalidrawAPI={value=>{api.current=value;}} onChange={changed} langCode="it-IT" theme="light" aiEnabled={false} validateEmbeddable={()=>false} UIOptions={{canvasActions:{export:false,saveAsImage:false}}}/>:<p>Preparo la lavagna…</p>}</section><footer>Il disegno resta in questa pagina. “Usa questo disegno” prepara una foto da controllare e trascrivere prima del calcolo. <a href="./THIRD-PARTY-NOTICES.txt" target="_blank" rel="noreferrer">Excalidraw · licenze</a></footer></main>;
}
createRoot(document.getElementById('root')!).render(<Board/>);
