import { useState } from 'react';

export type Part = {kind:string; a:number; b:number; value:string; id:string};
const points = Array.from({length:12},(_,i)=>({x:65+(i%4)*150,y:50+Math.floor(i/4)*110}));
export function coveredPoints(part:Pick<Part,'a'|'b'>){
 const a=points[part.a],b=points[part.b];
 return points.flatMap((p,i)=>(a.x===b.x&&p.x===a.x&&p.y>=Math.min(a.y,b.y)&&p.y<=Math.max(a.y,b.y))||(a.y===b.y&&p.y===a.y&&p.x>=Math.min(a.x,b.x)&&p.x<=Math.max(a.x,b.x))?[i]:[]);
}
export function buildNetlist(parts:Part[],ground:number,question?:{quantity:string;target:string}){
 const wires=parts.filter(p=>p.kind==='W');
 const parent=Array.from({length:points.length+wires.length},(_,i)=>i);
 const root=(a:number):number=>parent[a]===a?a:root(parent[a]);
 const join=(a:number,b:number)=>{const x=root(a),y=root(b);if(x!==y)parent[Math.max(x,y)]=Math.min(x,y);};
 // A crossing joins only when a wire ends there, a terminal is placed there,
 // or the student explicitly marks a junction. Interior crossings stay apart.
 const junctions=new Set([ground]);
 for(const p of parts){
  if(p.kind==='W'){junctions.add(p.a);junctions.add(p.b);}
  else if(p.kind==='J')junctions.add(p.a);
  else {junctions.add(p.a);junctions.add(p.b);}
 }
 wires.forEach((wire,index)=>{
  for(const i of coveredPoints(wire))if(junctions.has(i))join(points.length+index,i);
 });
 const node=(n:number)=>root(n)===root(ground)?'0':`n${root(n)}`;
 const components=parts.filter(p=>p.kind!=='W'&&p.kind!=='J');
 if(!components.length)throw new Error('Disegna almeno una sorgente e un resistore.');
 const quantity=question?.quantity??'voltage';
 const target=question?.target??(components.find(p=>p.kind==='R')?.id??components[0].id);
 if(!['voltage','current'].includes(quantity))throw new Error('Scegli tensione o corrente come grandezza richiesta.');
 if(!components.some(p=>p.id===target))throw new Error('Il componente richiesto non è presente nel circuito.');
 const net=components.map(p=>`${p.id} ${node(p.a)} ${node(p.b)} ${p.value} ${{R:'ohm',V:'volt',I:'ampere'}[p.kind]}`).join('\n');
 return net+`\n? ${quantity} ${target}`;
}
export function CircuitEditor({onUse}:{onUse:(text:string)=>void}) {
 const [parts,setParts]=useState<Part[]>([]),[kind,setKind]=useState('R'),[value,setValue]=useState('100'),[start,setStart]=useState<number|null>(null),[ground,setGround]=useState(8),[notice,setNotice]=useState('');
 const [questionQuantity,setQuestionQuantity]=useState('voltage'),[questionTarget,setQuestionTarget]=useState('');
 const components=parts.filter(p=>p.kind!=='W'&&p.kind!=='J');
 const selectedTarget=components.some(p=>p.id===questionTarget)?questionTarget:(components.find(p=>p.kind==='R')?.id??components[0]?.id??'');
 function add(a:number,b:number,k=kind) {
  if(a===b)return;
  if(points[a].x!==points[b].x&&points[a].y!==points[b].y){setNotice('Collega punti sulla stessa riga o colonna.');return;}
  const newPoints=coveredPoints({a,b});
  if(newPoints.some(i=>blocked(i))||(k!=='W'&&parts.some(p=>p.kind!=='J'&&newPoints.slice(1,-1).some(i=>p.a===i||p.b===i)))){setNotice('Questo tratto attraversa un componente o un morsetto già usato. Scegli un percorso libero.');return;}
  const id=k+(parts.filter(p=>p.kind===k).length+1);
  setParts([...parts,{kind:k,a,b,value,id}]);setStart(null);setNotice('');
 }
 function toggleJunction(i:number){
  const existing=parts.findIndex(p=>p.kind==='J'&&p.a===i);
  setParts(existing<0?[...parts,{kind:'J',a:i,b:i,id:`J${i}`,value:'0'}]:parts.filter((_,n)=>n!==existing));
  setStart(null);setNotice(existing<0?'Giunzione aggiunta: i fili qui sono collegati.':'Giunzione rimossa: un incrocio interno resta separato.');
 }
 function blocked(i:number){return parts.some(p=>p.kind!=='W'&&p.kind!=='J'&&i!==p.a&&i!==p.b&&coveredPoints(p).includes(i));}
 const junctions=new Set(parts.filter(p=>p.kind==='J').map(p=>p.a));
 const wires=parts.filter(p=>p.kind==='W');
 const crossingPoints=points.flatMap((point,i)=>{
  const horizontal=wires.some(w=>points[w.a].y===points[w.b].y&&coveredPoints(w).includes(i)&&w.a!==i&&w.b!==i);
  const vertical=wires.some(w=>points[w.a].x===points[w.b].x&&coveredPoints(w).includes(i)&&w.a!==i&&w.b!==i);
  const endpoint=parts.some(p=>p.kind!=='J'&&(p.a===i||p.b===i));
  return horizontal&&vertical&&!endpoint&&!junctions.has(i)&&ground!==i?[point]:[];
 });
 function useCircuit() {
  try{onUse(buildNetlist(parts,ground,{quantity:questionQuantity,target:selectedTarget}));}catch(e){setNotice((e as Error).message);}
 }
 return <section className="circuit-editor" aria-label="Lavagna circuitale">
  <p>Scegli un componente e tocca i suoi due morsetti. I fili che si incrociano restano separati: usa Giunzione per collegarli. La fine di un filo su un altro crea una derivazione. Per i generatori il primo morsetto è il positivo (V) o l’origine della freccia (I). Puoi anche trascinare un componente sulla griglia.</p>
  <div className="student-toolbar">{[['R','Resistore'],['V','Tensione'],['I','Corrente'],['W','Filo'],['J','Giunzione'],['G','Massa']].map(([k,label])=><button type="button" draggable={k!=='G'&&k!=='J'} onDragStart={e=>e.dataTransfer.setData('text/plain',k)} aria-pressed={kind===k} key={k} onClick={()=>{setKind(k);setStart(null);if(k==='V')setValue('12');if(k==='I')setValue('1');if(k==='R')setValue('100');}}>{label}</button>)}
   <label>Valore SI <input value={value} onChange={e=>setValue(e.target.value)} aria-label="Valore del componente" /></label>
   <button type="button" disabled={!parts.length} onClick={()=>{setParts(parts.slice(0,-1));setStart(null);}}>Annulla ultimo</button>
  </div>
  <div className="student-toolbar"><label>Grandezza richiesta <select aria-label="Grandezza richiesta" value={questionQuantity} onChange={e=>setQuestionQuantity(e.target.value)}><option value="voltage">Tensione</option><option value="current">Corrente</option></select></label><label>Componente richiesto <select aria-label="Componente richiesto" value={selectedTarget} onChange={e=>setQuestionTarget(e.target.value)} disabled={!components.length}>{!components.length?<option value="">Disegna un componente</option>:components.map(p=><option value={p.id} key={p.id}>{p.id}</option>)}</select></label></div>
  <svg viewBox="0 0 610 330" aria-label="Griglia per disegnare il circuito" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();const k=e.dataTransfer.getData('text/plain');if(!['R','V','I','W'].includes(k))return;const b=e.currentTarget.getBoundingClientRect();const x=(e.clientX-b.left)*610/b.width,y=(e.clientY-b.top)*330/b.height;const n=points.reduce((best,p,i)=>Math.hypot(p.x-x,p.y-y)<Math.hypot(points[best].x-x,points[best].y-y)?i:best,0);add(n,n%4===3?n-1:n+1,k);}}>
   {parts.filter(p=>p.kind!=='J').map((p,i)=>{const a=points[p.a],b=points[p.b],x=(a.x+b.x)/2,y=(a.y+b.y)/2,dx=Math.sign(b.x-a.x),dy=Math.sign(b.y-a.y);return <g key={i} stroke="#24334b" strokeWidth="2" fill="white"><path d={`M${a.x} ${a.y}L${b.x} ${b.y}`}/>{p.kind==='R'?<rect x={x-22} y={y-10} width="44" height="20" transform={a.x===b.x?`rotate(90 ${x} ${y})`:undefined}/>:p.kind!=='W'?<><circle cx={x} cy={y} r="19"/>{p.kind==='V'?<><text x={x-dx*9} y={y-dy*9+5} stroke="none" fill="#24334b" textAnchor="middle">+</text><text x={x+dx*9} y={y+dy*9+5} stroke="none" fill="#24334b" textAnchor="middle">−</text></>:<text x={x} y={y+5} stroke="none" fill="#24334b" textAnchor="middle">{dx===1?'→':dx===-1?'←':dy===1?'↓':'↑'}</text>}</>:null}{p.kind!=='W'?<text x={x+28} y={y-15} fill="#24334b" stroke="none" fontSize="14">{p.id} · {p.value}</text>:null}</g>;})}
   {crossingPoints.map((p,i)=><g key={`cross-${i}`} aria-label="Incrocio senza giunzione"><path d={`M${p.x} ${p.y-12}L${p.x} ${p.y+12}`} stroke="white" strokeWidth="6"/><path d={`M${p.x} ${p.y-12}L${p.x} ${p.y-8}C${p.x+12} ${p.y-8} ${p.x+12} ${p.y+8} ${p.x} ${p.y+8}L${p.x} ${p.y+12}`} stroke="white" strokeWidth="6" fill="none"/><path d={`M${p.x} ${p.y-12}L${p.x} ${p.y-8}C${p.x+12} ${p.y-8} ${p.x+12} ${p.y+8} ${p.x} ${p.y+8}L${p.x} ${p.y+12}`} stroke="#24334b" strokeWidth="2" fill="none"/></g>)}
   {points.map((p,i)=>blocked(i)?null:<g key={i} role="button" tabIndex={0} aria-label={`Nodo ${i}${i===ground?' massa':''}${junctions.has(i)?' giunzione':''}`} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();if(kind==='G')setGround(i);else if(kind==='J')toggleJunction(i);else if(start===null)setStart(i);else add(start,i);}}} onClick={()=>{if(kind==='G')setGround(i);else if(kind==='J')toggleJunction(i);else if(start===null)setStart(i);else add(start,i);}}><circle cx={p.x} cy={p.y} r="16" fill={start===i?'#dce4ff':'transparent'}/><circle cx={p.x} cy={p.y} r="5" stroke="#294bd3" strokeWidth="2" fill={junctions.has(i)||i===ground||parts.some(part=>part.kind!=='J'&&(part.a===i||part.b===i))?'#294bd3':'white'}/><text x={p.x-10} y={p.y+25} fontSize="14">{i===ground?'0 ⏚':`n${i}`}</text></g>)}
  </svg>
  <p role="status">{notice || (start!==null?'Scegli il secondo morsetto.':'Punto pieno: collegamento. Punto vuoto: incrocio senza giunzione; tocca Giunzione per cambiarlo.')}</p>
  <button type="button" className="student-primary" onClick={useCircuit}>Usa il circuito disegnato →</button>
 </section>;
}
