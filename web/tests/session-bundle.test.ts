import {describe,it,expect} from 'vitest';
import {makeSessionBundle,readSessionBundle} from '../src/student/sessionBundle.ts';

const netlist='V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2';
const board=JSON.stringify({type:'excalidraw',version:2,elements:[{id:'board-mark'}],files:{}});
const fields={netlist,method:'auto',answerExact:'33/4',engineRevision:'abc123',selectedStep:2,
 showOriginal:true,boardScene:board,traceSteps:[{transcription:'R1 + R2',operation:'serie',first:'R1',second:'R2',claimed_value:'320',reading:'clear'}],priorImageSha256:null};

describe('quaderno portabile',()=>{
 it('conserva circuito, lavagna e tentativo ma richiede ricalcolo della soluzione',async()=>{
  const bundle=await makeSessionBundle(fields);
  expect(await readSessionBundle(JSON.stringify(bundle))).toEqual(bundle);
  expect('proof' in bundle).toBe(false);
  expect('image' in bundle).toBe(false);
 });
 it('riapre un valore misurato con un metodo alternativo senza promuovere il testo a prova',async()=>{
  const numeric={...fields.traceSteps[0],operation:'tensione',first:'R2',second:'',claimed_value:'33/4',transcription:'KCL al nodo a'};
  const bundle=await makeSessionBundle({...fields,traceSteps:[numeric]});
  expect((await readSessionBundle(JSON.stringify(bundle))).traceSteps).toEqual([numeric]);
 });
 it('conserva una KCL strutturata nel quaderno',async()=>{
  const kcl={...fields.traceSteps[0],operation:'kcl',first:'a',second:'-R1,+R2',claimed_value:null,transcription:'KCL al nodo a'};
  const bundle=await makeSessionBundle({...fields,traceSteps:[kcl]});
  expect((await readSessionBundle(JSON.stringify(bundle))).traceSteps).toEqual([kcl]);
 });
 it('conserva una KVL strutturata e i versi dei rami nel quaderno',async()=>{
  const kvl={...fields.traceSteps[0],operation:'kvl',first:'b',second:'+R1,+R2,-V1',claimed_value:null,transcription:'KVL alla maglia'};
  const bundle=await makeSessionBundle({...fields,traceSteps:[kvl]});
  expect((await readSessionBundle(JSON.stringify(bundle))).traceSteps).toEqual([kvl]);
 });
 it('rifiuta una netlist sostituita a revisione invariata',async()=>{
  const bundle=await makeSessionBundle(fields);
  await expect(readSessionBundle(JSON.stringify({...bundle,netlist:netlist.replace('220','221')}))).rejects.toThrow('modificato');
 });
 it('rifiuta scene e procedimenti corrotti prima del caricamento della lavagna',async()=>{
  const bundle=await makeSessionBundle(fields);
  await expect(readSessionBundle(JSON.stringify({...bundle,boardScene:'{"elements":42}'}))).rejects.toThrow('lavagna');
  await expect(readSessionBundle(JSON.stringify({...bundle,traceSteps:[{...fields.traceSteps[0],operation:'esegui-istruzioni'}]}))).rejects.toThrow('procedimento');
 });
 it('rifiuta versioni non supportate e file troppo grandi',async()=>{
  const bundle=await makeSessionBundle(fields);
  await expect(readSessionBundle(JSON.stringify({...bundle,schema:'future'}))).rejects.toThrow('Versione');
  await expect(readSessionBundle(' '.repeat(10_500_001))).rejects.toThrow('10 MB');
 });
});
