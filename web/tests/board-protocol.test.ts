import {describe,it,expect} from 'vitest';
import {readBoardMessage} from '../src/student/boardProtocol.ts';
const frame={} as Window,origin='http://127.0.0.1:43921';
const event=(data:unknown)=>({origin,source:frame,data});
describe('confine della lavagna riutilizzata',()=>{
 it('accetta il trasferimento dalla sola lavagna attesa',()=>{expect(readBoardMessage(event({type:'kirchhoff:board-image',image:'data:image/png;base64,YQ=='}),frame,origin)?.type).toBe('kirchhoff:board-image');});
 it('rifiuta un mittente estraneo anche alla stessa origine',()=>{expect(readBoardMessage({...event({type:'kirchhoff:board-ready'}),source:{} as Window},frame,origin)).toBeNull();});
 it('rifiuta un’altra origine e l’assenza dell’iframe',()=>{expect(readBoardMessage({...event({type:'kirchhoff:board-ready'}),origin:'https://example.com'},frame,origin)).toBeNull();expect(readBoardMessage(event({type:'kirchhoff:board-ready'}),null,origin)).toBeNull();});
 it.each(['javascript:alert(1)','data:image/svg+xml;base64,YQ==','https://example.com/photo.png','data:image/png;base64,<script>'])('rifiuta immagini attive o remote: %s',image=>{expect(readBoardMessage(event({type:'kirchhoff:board-image',image}),frame,origin)).toBeNull();});
 it('rifiuta payload malformati e troppo grandi',()=>{for(const data of [null,{},'ready',{type:'kirchhoff:board-state',scene:42},{type:'kirchhoff:board-image',image:'data:image/png;base64,'+'a'.repeat(2800000)},{type:'kirchhoff:board-state',scene:'a'.repeat(10000001)}])expect(readBoardMessage(event(data),frame,origin)).toBeNull();});
 it('mantiene i byte della scena e il messaggio ready',()=>{const scene='{"elements":[]}';expect(readBoardMessage(event({type:'kirchhoff:board-state',scene}),frame,origin)).toEqual({type:'kirchhoff:board-state',scene});expect(readBoardMessage(event({type:'kirchhoff:board-ready'}),frame,origin)).toEqual({type:'kirchhoff:board-ready'});});
});
