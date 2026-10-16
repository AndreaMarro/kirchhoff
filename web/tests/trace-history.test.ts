import {describe,it,expect} from 'vitest';
import fixture from './fixtures/student-history.json';
import {makeSessionBundle,readSessionBundle} from '../src/student/sessionBundle.ts';

const fields={netlist:fixture.netlist,method:'auto',answerExact:'8',engineRevision:'b'.repeat(40),selectedStep:0,
 showOriginal:false,boardScene:'',traceSteps:fixture.attempts[2].steps,priorImageSha256:null};

describe('cronologia del quaderno',()=>{
 it('conserva tutte le revisioni precedenti e il draft corrente in versione3',async()=>{
  const bundle=await makeSessionBundle({...fields,traceHistory:fixture.attempts});
  expect(bundle.schema).toBe('kirchhoff-portable-session.v3');
  const reopened=await readSessionBundle(JSON.stringify(bundle));
  expect(reopened.traceHistory).toEqual(fixture.attempts);
  expect(reopened.traceSteps).toEqual(fixture.attempts[2].steps);
  expect(JSON.stringify(reopened.traceHistory)).not.toContain('diagnosis');
 });
 it.each(['kirchhoff-portable-session.v1','kirchhoff-portable-session.v2'])('legge %s senza inventare passato e rifiuta downgrade con storia',async schema=>{
  const current=await makeSessionBundle(fields);
  const {traceHistory:_,...legacy}=current;
  expect((await readSessionBundle(JSON.stringify({...legacy,schema}))).traceHistory).toEqual([]);
  await expect(readSessionBundle(JSON.stringify({...legacy,schema,traceHistory:fixture.attempts}))).rejects.toThrow('cronologia');
 });
 it.each([
  [{...fixture.attempts[0],engineRevision:'unknown'}],
  [{...fixture.attempts[0],steps:[]}],
  [{...fixture.attempts[0],steps:[{...fixture.attempts[0].steps[0],reading:'certified'}]}],
  [{...fixture.attempts[0],diagnosis:{outcome:'valid_so_far'}}],
  [{...fixture.attempts[0],circuitFingerprint:'0'.repeat(64)}],
  [{...fixture.attempts[0],steps:[{...fixture.attempts[0].steps[0],diagnosis:'valid'}]}],
  [{...fixture.attempts[0],steps:[{...fixture.attempts[0].steps[0],operation:['serie']}]}],
  [{...fixture.attempts[0],steps:[{...fixture.attempts[0].steps[0],reading:['clear']}]}],
  Array(33).fill(fixture.attempts[0]),
 ])('rifiuta record corrotti o prove esterne prima di aprire il quaderno',async traceHistory=>{
  const bundle=await makeSessionBundle(fields);
  await expect(readSessionBundle(JSON.stringify({...bundle,traceHistory}))).rejects.toThrow('cronologia');
 });
});
