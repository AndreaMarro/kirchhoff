import { useState } from 'react';

export type Part = {kind:string; a:number; b:number; value:string; id:string};
const points = Array.from({length:12},(_,i)=>({x:65+(i%4)*150,y:50+Math.floor(i/4)*110}));
export function coveredPoints(part:Pick<Part,'a'|'b'>){
 const a=points[part.a],b=points[part.b];
 return points.flatMap((p,i)=>(a.x===b.x&&p.x===a.x&&p.y>=Math.min(a.y,b.y)&&p.y<=Math.max(a.y,b.y))||(a.y===b.y&&p.y===a.y&&p.x>=Math.min(a.x,b.x)&&p.x<=Math.max(a.x,b.x))?[i]:[]);
}
export function buildNetlist(parts:Part[],ground:number){
 const parent=points.map((_,i)=>i);
 const root=(a:number):number=>parent[a]===a?a:root(parent[a]);
 for(const p of parts.filter(p=>p.kind==='W'))for(const i of coveredPoints(p))parent[root(i)]=root(p.a);
 const node=(n:number)=>root(n)===root(ground)?'0':`n${root(n)}`;
 const components=parts.filter(p=>p.kind!=='W');
 if(!components.length)throw new Error('Disegna almeno una sorgente e un resistore.');
 const net=components.map(p=>`${p.id} ${node(p.a)} ${node(p.b)} ${p.value} ${{R:'ohm',V:'volt',I:'ampere'}[p.kind]}`).join('\n');
 return net+`\n? voltage ${components.find(p=>p.kind==='R')?.id??components[0].id}`;
}
export function CircuitEditor({onUse}:{onUse:(text:string)=>void}) {
 const [parts,setParts]=useState<Part[]>([]),[kind,setKind]=useState('R'),[value,setValue]=useState('100'),[start,setStart]=useState<number|null>(null),[ground,setGround]=useState(8),[notice,setNotice]=useState('');
 function add(a:number,b:number,k=kind) {
  if(a===b)return;
  if(points[a].x!==points[b].x&&points[a].y!==points[b].y){setNotice('Collega punti sulla stessa riga o colonna.');return;}
  const newPoints=coveredPoints({a,b});
  if(newPoints.some(i=>blocked(i))||(k!=='W'&&parts.some(p=>newPoints.slice(1,-1).some(i=>p.a===i||p.b===i)))){setNotice('Questo tratto attraversa un componente o un morsetto già usato. Scegli un percorso libero.');return;}
  const id=k+(parts.filter(p=>p.kind===k).length+1);
  setParts([...parts,{kind:k,a,b,value,id}]);setStart(null);setNotice('');
 }
 function blocked(i:number){return parts.some(p=>p.kind!=='W'&&i!==p.a&&i!==p.b&&coveredPoints(p).includes(i));}
 function useCircuit() {
  try{onUse(buildNetlist(parts,ground));}catch(e){setNotice((e as Error).message);}
 }
 return <section className="circuit-editor" aria-label="Lavagna circuitale">
  <p>Scegli un componente e tocca i suoi due morsetti. I fili uniscono i nodi. Per i generatori il primo morsetto è il positivo (V) o l’origine della freccia (I). Puoi anche trascinare un componente sulla griglia.</p>
  <div className="student-toolbar">{[['R','Resistore'],['V','Tensione'],['I','Corrente'],['W','Filo'],['G','Massa']].map(([k,label])=><button type="button" draggable={k!=='G'} onDragStart={e=>e.dataTransfer.setData('text/plain',k)} aria-pressed={kind===k} key={k} onClick={()=>{setKind(k);setStart(null);if(k==='V')setValue('12');if(k==='I')setValue('1');if(k==='R')setValue('100');}}>{label}</button>)}
   <label>Valore SI <input value={value} onChange={e=>setValue(e.target.value)} aria-label="Valore del componente" /></label>
   <button type="button" disabled={!parts.length} onClick={()=>{setParts(parts.slice(0,-1));setStart(null);}}>Annulla ultimo</button>
  </div>
  <svg viewBox="0 0 610 330" aria-label="Griglia per disegnare il circuito" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();const k=e.dataTransfer.getData('text/plain');if(!['R','V','I','W'].includes(k))return;const b=e.currentTarget.getBoundingClientRect();const x=(e.clientX-b.left)*610/b.width,y=(e.clientY-b.top)*330/b.height;const n=points.reduce((best,p,i)=>Math.hypot(p.x-x,p.y-y)<Math.hypot(points[best].x-x,points[best].y-y)?i:best,0);add(n,n%4===3?n-1:n+1,k);}}>
   {parts.map((p,i)=>{const a=points[p.a],b=points[p.b],x=(a.x+b.x)/2,y=(a.y+b.y)/2,dx=Math.sign(b.x-a.x),dy=Math.sign(b.y-a.y);return <g key={i} stroke="#24334b" strokeWidth="2" fill="white"><path d={`M${a.x} ${a.y}L${b.x} ${b.y}`}/>{p.kind==='R'?<rect x={x-22} y={y-10} width="44" height="20" transform={a.x===b.x?`rotate(90 ${x} ${y})`:undefined}/>:p.kind!=='W'?<><circle cx={x} cy={y} r="19"/>{p.kind==='V'?<><text x={x-dx*9} y={y-dy*9+5} stroke="none" fill="#24334b" textAnchor="middle">+</text><text x={x+dx*9} y={y+dy*9+5} stroke="none" fill="#24334b" textAnchor="middle">−</text></>:<text x={x} y={y+5} stroke="none" fill="#24334b" textAnchor="middle">{dx===1?'→':dx===-1?'←':dy===1?'↓':'↑'}</text>}</>:null}{p.kind!=='W'?<text x={x+28} y={y-15} fill="#24334b" stroke="none" fontSize="14">{p.id} · {p.value}</text>:null}</g>;})}
   {points.map((p,i)=>blocked(i)?null:<g key={i} role="button" tabIndex={0} aria-label={`Nodo ${i}${i===ground?' massa':''}`} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();if(kind==='G')setGround(i);else if(start===null)setStart(i);else add(start,i);}}} onClick={()=>{if(kind==='G')setGround(i);else if(start===null)setStart(i);else add(start,i);}}><circle cx={p.x} cy={p.y} r="16" fill={start===i?'#dce4ff':'transparent'}/><circle cx={p.x} cy={p.y} r="5" fill="#294bd3"/><text x={p.x-10} y={p.y+25} fontSize="14">{i===ground?'0 ⏚':`n${i}`}</text></g>)}
  </svg>
  <p role="status">{notice || (start!==null?'Scegli il secondo morsetto.':'I pallini blu sono punti di collegamento espliciti.')}</p>
  <button type="button" className="student-primary" onClick={useCircuit}>Usa il circuito disegnato →</button>
 </section>;
}
