import {describe,it,expect} from 'vitest';
import {readBoardMessage} from '../src/student/boardProtocol.ts';
const frame={} as Window,origin='http://127.0.0.1:43921';
const event=(data:unknown)=>({origin,source:frame,data});
const scene=JSON.stringify({elements:[{id:'stroke-1',isDeleted:false},{id:'stroke-2',isDeleted:false},{id:'erased',isDeleted:true}],files:{}});
const imageMessage={type:'kirchhoff:board-image',image:'data:image/png;base64,YQ==',scene,selectedElementIds:['stroke-1'],selectionOnly:true};
describe('confine della lavagna riutilizzata',()=>{
 it('accetta immagine, scena e tratti scelti dalla sola lavagna attesa',()=>{expect(readBoardMessage(event(imageMessage),frame,origin)).toEqual(imageMessage);});
 it('rifiuta un mittente estraneo anche alla stessa origine',()=>{expect(readBoardMessage({...event({type:'kirchhoff:board-ready'}),source:{} as Window},frame,origin)).toBeNull();});
 it('rifiuta un’altra origine e l’assenza dell’iframe',()=>{expect(readBoardMessage({...event({type:'kirchhoff:board-ready'}),origin:'https://example.com'},frame,origin)).toBeNull();expect(readBoardMessage(event({type:'kirchhoff:board-ready'}),null,origin)).toBeNull();});
 it.each(['javascript:alert(1)','data:image/svg+xml;base64,YQ==','https://example.com/photo.png','data:image/png;base64,<script>'])('rifiuta immagini attive o remote: %s',image=>{expect(readBoardMessage(event({...imageMessage,image}),frame,origin)).toBeNull();});
 it('rifiuta provenienze di tratti assenti, cancellati o non selezionati',()=>{
  for(const payload of [
   {...imageMessage,selectedElementIds:['missing']},
   {...imageMessage,selectedElementIds:['erased']},
   {...imageMessage,selectedElementIds:['stroke-1','stroke-1']},
   {...imageMessage,selectionOnly:false},
   {...imageMessage,scene:'{"elements":[],"files":{}}'},
   {type:'kirchhoff:board-image',image:imageMessage.image},
  ])expect(readBoardMessage(event(payload),frame,origin)).toBeNull();
 });
 it('rifiuta payload malformati e troppo grandi',()=>{for(const data of [null,{},'ready',{type:'kirchhoff:board-state',scene:42},{...imageMessage,image:'data:image/png;base64,'+'a'.repeat(2800000)},{type:'kirchhoff:board-state',scene:'a'.repeat(10000001)}])expect(readBoardMessage(event(data),frame,origin)).toBeNull();});
 it('mantiene i byte della scena e il messaggio ready',()=>{const scene='{"elements":[]}';expect(readBoardMessage(event({type:'kirchhoff:board-state',scene}),frame,origin)).toEqual({type:'kirchhoff:board-state',scene});expect(readBoardMessage(event({type:'kirchhoff:board-ready'}),frame,origin)).toEqual({type:'kirchhoff:board-ready'});});
 it('accetta uno snapshot identificato solo dall’iframe corretto',()=>{const requestId='7cc2bfb8-32b5-450f-bb22-d7c22da6e671',scene='{"elements":[],"files":{}}';expect(readBoardMessage(event({type:'kirchhoff:board-snapshot',requestId,scene}),frame,origin)).toEqual({type:'kirchhoff:board-snapshot',requestId,scene});expect(readBoardMessage(event({type:'kirchhoff:board-snapshot',requestId:'bad',scene}),frame,origin)).toBeNull();});
});
