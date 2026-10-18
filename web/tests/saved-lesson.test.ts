import {expect,it} from 'vitest';
import {makeSessionBundle,readSessionBundle,makeSavedLesson,boardSceneSha256} from '../src/student/sessionBundle.ts';

const netlist='V1 b 0 12 volt\nR1 b a 2000 ohm\nR2 a 0 1000 ohm\n? voltage R2';
const fields={netlist,method:'auto',answerExact:'4',engineRevision:'a'.repeat(40),selectedStep:0,showOriginal:false,
 boardScene:'',traceSteps:[{transcription:'',operation:'serie',first:'',second:'',claimed_value:null,reading:'clear'}],priorImageSha256:null};
const view={title:'Tensione di R2',method:'nodal',original:'<svg xmlns="http://www.w3.org/2000/svg"/>',
 steps:[{title:'KCL',explanation:'Il nodo ha due rami.',equations:['(12-v)/2000=v/1000'],focus:['R2'],svg:'<svg xmlns="http://www.w3.org/2000/svg"/>'}],
 answer:{exact:'4',unit:'V',reference:'a → 0'}};

it('conserva i passaggi visuali DRAFT senza assegnare una certificazione al salvataggio',async()=>{
 const savedLesson=await makeSavedLesson(view,fields);
 const bundle=await makeSessionBundle({...fields,savedLesson});
 const restored=await readSessionBundle(JSON.stringify(bundle));
 expect(restored.savedLesson?.view.steps[0].equations).toEqual(['(12-v)/2000=v/1000']);
 expect(restored.savedLesson?.view.contentStatus).toBe('DRAFT');
 expect(restored.savedLesson?.view).not.toHaveProperty('verification');
 expect(restored.traceHistory).toEqual([]);
});

it('rifiuta una copia alterata o associata a un altro circuito prima della visualizzazione',async()=>{
 const bundle=await makeSessionBundle({...fields,savedLesson:await makeSavedLesson(view,fields)});
 const modified=structuredClone(bundle);modified.savedLesson!.view.answer.exact='999';
 await expect(readSessionBundle(JSON.stringify(modified))).rejects.toThrow('copia');
 const replacement=fields.netlist.replace('2000','3000');
 await expect(readSessionBundle(JSON.stringify({...bundle,netlist:replacement,circuitFingerprint:await boardSceneSha256(replacement)}))).rejects.toThrow('copia');
});

it('non accetta APPROVED o un badge di verifica nemmeno con hash ricalcolato',async()=>{
 const saved=await makeSavedLesson(view,fields);
 for(const extra of [{contentStatus:'APPROVED'},{verification:{electrical_claim:'VERIFIED'}}]){
  const forged={...saved,view:{...saved.view,...extra}};
  forged.sha256=await boardSceneSha256(JSON.stringify({netlist,method:fields.method,answerExact:'4',engineRevision:fields.engineRevision,view:forged.view}));
  await expect(readSessionBundle(JSON.stringify({...await makeSessionBundle(fields),savedLesson:forged}))).rejects.toThrow('copia');
 }
});

it('mantiene leggibili i vecchi quaderni e rifiuta una copia priva di schema o sovradimensionata',async()=>{
 const legacy=await makeSessionBundle(fields);
 expect((await readSessionBundle(JSON.stringify(legacy))).savedLesson).toBeUndefined();
 const saved=await makeSavedLesson(view,fields);
 await expect(readSessionBundle(JSON.stringify({...legacy,savedLesson:{...saved,schema:'future'}}))).rejects.toThrow('copia');
 await expect(makeSavedLesson({...view,original:'x'.repeat(4_000_001)},fields)).rejects.toThrow('copia');
});
