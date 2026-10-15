import {App, PostMessageTransport} from '@modelcontextprotocol/ext-apps';
import {safeSvg} from './student/safeSvg.ts';
import {lessonMathMarkup,lessonExpressionMarkup} from './student/lessonMath.ts';
import {verificationDescription,decimalForReading,answerPrefix,isLaplaceLesson} from './student/lessonPresentation.ts';
import type {Verification} from './student/lessonPresentation.ts';

type Step={math?:unknown;title:string;explanation:string;svg:string;equations:string[]};
type Lesson={schema:string;outcome:string;method:string;verification:Verification;netlist:string;title:string;steps:Step[];answer:{math?:unknown;display_exact?:string;exact:string;decimal?:string;unit:string;reference:string;quantity?:string};fingerprint:string;conventions?:{domain?:string};message?:string};
const app=new App({name:'Kirchhoff CircuitCheck',version:'0.1.0'},{});
const input=document.querySelector<HTMLTextAreaElement>('#circuit')!;
const status=document.querySelector<HTMLElement>('#status')!;
const scope=document.querySelector<HTMLElement>('#scope')!;
const title=document.querySelector<HTMLElement>('#step-title')!;
const drawing=document.querySelector<HTMLElement>('#drawing')!;
const explanation=document.querySelector<HTMLElement>('#explanation')!;
const equations=document.querySelector<HTMLElement>('#equations')!;
const progress=document.querySelector<HTMLElement>('#progress')!;
const answer=document.querySelector<HTMLElement>('#answer')!;
const previous=document.querySelector<HTMLButtonElement>('#previous')!;
const next=document.querySelector<HTMLButtonElement>('#next')!;
const solve=document.querySelector<HTMLButtonElement>('#solve')!;
let lesson:Lesson|null=null,position=0,connected=false;

function show(){
 const step=lesson?.steps[position];
 title.textContent=step?.title??'Il circuito';
 drawing.innerHTML=step?safeSvg(step.svg):'';
 explanation.textContent=step?.explanation??'';
 const math=lessonMathMarkup(step?.math);
 if(math)equations.innerHTML=math;
 else equations.replaceChildren(...(step?.equations??[]).map(text=>{const p=document.createElement('p');p.textContent=text;return p;}));
 progress.textContent=step?`${position+1} / ${lesson!.steps.length}`:'';
 const answerNote=lesson ? isLaplaceLesson(lesson)?`${lesson.answer.unit} · Trasformata unilaterale; stato iniziale a t = 0−.`:`${lesson.answer.unit} · ≈ ${decimalForReading(lesson.answer.decimal??lesson.answer.exact)} ${lesson.answer.unit}` : '';
 answer.textContent=step&&position===lesson!.steps.length-1?`${answerPrefix(lesson!.answer.quantity,lesson!.conventions?.domain)}${lesson!.answer.display_exact??lesson!.answer.exact} ${answerNote} · ${lesson!.answer.reference}`:'';
 if(step&&position===lesson!.steps.length-1){
  const exact=lessonExpressionMarkup(lesson!.answer.math);
  if(exact){
   const composed=document.createElement('span');composed.innerHTML=exact;
   answer.replaceChildren(document.createTextNode(answerPrefix(lesson!.answer.quantity,lesson!.conventions?.domain)),composed,
    document.createTextNode(` ${answerNote} · ${lesson!.answer.reference}`));
  }
 }
 previous.disabled=!step||position===0;
 next.disabled=!step||position===lesson!.steps.length-1;
}
function receive(raw:unknown){
 let data=raw as Lesson;
 if(!data||typeof data!=='object')return;
 if(data.outcome!=='solved'){status.textContent=data.message??'Circuito non risolto: controlla i dati e le condizioni.';lesson=null;show();return;}
 if(data.schema!=='circuit-lesson.v1'||!Array.isArray(data.steps)||!data.steps.length||!data.answer){status.textContent='Risultato non interpretabile.';lesson=null;show();return;}
 lesson=data;input.value=data.netlist;position=0;status.textContent=verificationDescription(data);show();
}
function fromResult(result:{isError?:boolean;structuredContent?:unknown;content?:Array<{type:string;text?:string}>}){
 if(result.isError){status.textContent=result.content?.find(c=>c.type==='text')?.text??'Il motore ha rifiutato il circuito.';return;}
 const structured=result.structuredContent;
 if(structured&&typeof structured==='object'&&'outcome' in structured){receive(structured);return;}
 const text=result.content?.find(c=>c.type==='text')?.text;
 if(text){try{receive(JSON.parse(text));}catch{status.textContent='Risultato non interpretabile.';}}
}
app.ontoolinput=params=>{const value=params.arguments?.netlist;if(typeof value==='string')input.value=value;};
app.ontoolresult=fromResult;
previous.addEventListener('click',()=>{position=Math.max(0,position-1);show();});
next.addEventListener('click',()=>{position=Math.min((lesson?.steps.length??1)-1,position+1);show();});
input.addEventListener('input',()=>{lesson=null;status.textContent='Circuito modificato: la derivazione precedente non si applica più.';show();});
solve.addEventListener('click',async()=>{
 if(!connected){status.textContent='Host MCP non collegato.';return;}
 solve.disabled=true;status.textContent='Verifica in corso…';
 try{const result=await app.callServerTool({name:'solve_circuit',arguments:{netlist:input.value,method:'auto'}});fromResult(result);}
 catch(e){status.textContent=e instanceof Error?e.message:'Verifica non disponibile.';}
 finally{solve.disabled=false;}
});
show();
app.connect(new PostMessageTransport(window.parent,window.parent)).then(async()=>{
 connected=true;status.textContent='Host collegato. Controlla il circuito e avvia la verifica.';
 try{
  const result=await app.callServerTool({name:'circuit_capabilities',arguments:{}});
  const value=result.structuredContent as {scope?:unknown}|undefined;
  if(typeof value?.scope==='string')scope.textContent=value.scope;
 }catch{scope.textContent='';}
}).catch(()=>{status.textContent='Host MCP non collegato.';});
