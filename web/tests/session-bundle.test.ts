import {describe,it,expect} from 'vitest';
import {boardSceneSha256,makeSessionBundle,readSessionBundle,MAX_SESSION_BYTES} from '../src/student/sessionBundle.ts';
import {makeSourceArtifact} from '../src/student/sourceArtifact.ts';

const netlist='V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2';
const board=JSON.stringify({type:'excalidraw',version:2,elements:[{id:'board-mark'}],files:{}});
const fields={netlist,method:'auto',answerExact:'33/4',engineRevision:'abc123',selectedStep:2,
 showOriginal:true,boardScene:board,traceSteps:[{transcription:'R1 + R2',operation:'serie',first:'R1',second:'R2',claimed_value:'320',reading:'clear'}],priorImageSha256:null};

describe('quaderno portabile',()=>{
 it('riapre la versione 1 e conserva una fonte nella versione 2 senza ripristinare la conferma',async()=>{
  const legacy={...await makeSessionBundle(fields),schema:'kirchhoff-portable-session.v1'};
  expect((await readSessionBundle(JSON.stringify(legacy))).netlist).toBe(netlist);
  const image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==';
  const source=await makeSourceArtifact(image,'image');
  const bundle=await makeSessionBundle({...fields,sourceArtifact:source,priorImageSha256:source.prepared.sha256});
  expect((await readSessionBundle(JSON.stringify(bundle))).sourceArtifact).toEqual(source);
  await expect(readSessionBundle(JSON.stringify({...bundle,priorImageSha256:'a'.repeat(64)}))).rejects.toThrow('revisione fotografica');
  await expect(readSessionBundle(JSON.stringify({...bundle,schema:legacy.schema}))).rejects.toThrow('versione 2');
  await expect(readSessionBundle(JSON.stringify({...bundle,sourceArtifact:{...source,kind:'board'}}))).rejects.toThrow('tratti');
 });
 it.each(['rms','peak','unspecified'])('conserva la dichiarazione AC %s e rileva modifiche alla sua revisione',async amplitude=>{
  const ac=`@ac 100 rad/s\n@amplitude ${amplitude}\nV1 a 0 10 volt 30deg\nR1 a 0 5 ohm\n? current R1`;
  const bundle=await makeSessionBundle({...fields,netlist:ac,method:'phasor',answerExact:'(sqrt(3)) + j*(1)'});
  expect((await readSessionBundle(JSON.stringify(bundle))).netlist).toBe(ac);
  await expect(readSessionBundle(JSON.stringify({...bundle,netlist:ac.replace(`@amplitude ${amplitude}`,`@amplitude ${amplitude==='rms'?'peak':'rms'}`)}))).rejects.toThrow('modificato');
 });
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
 it('conserva la scena sorgente e i tratti scelti come provenienza storica, senza foto privata',async()=>{
  const source={sceneSha256:await boardSceneSha256(board),selectedElementIds:['board-mark'],selectionOnly:true};
  const bundle=await makeSessionBundle({...fields,priorImageSha256:'a'.repeat(64),boardSource:source});
  expect((await readSessionBundle(JSON.stringify(bundle))).boardSource).toEqual(source);
  expect(JSON.stringify(bundle)).not.toContain('data:image/');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardSource:{...source,selectedElementIds:['board-mark','board-mark']}}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,priorImageSha256:null}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardScene:''}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardSource:{...source,sceneSha256:'invalid'}}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardSource:{...source,sceneSha256:'b'.repeat(64)}}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardSource:{...source,selectedElementIds:['another-mark']}}))).rejects.toThrow('provenienza');
  await expect(readSessionBundle(JSON.stringify({...bundle,boardScene:JSON.stringify({type:'excalidraw',version:2,elements:[{id:'board-mark'},{id:'second-mark'}],files:{}}),boardSource:{...source,selectionOnly:false}}))).rejects.toThrow('provenienza');
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
  await expect(readSessionBundle(' '.repeat(MAX_SESSION_BYTES+1))).rejects.toThrow('42 MB');
 });
});
