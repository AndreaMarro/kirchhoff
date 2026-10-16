import {afterEach,describe,it,expect,vi} from 'vitest';
import fixture from './fixtures/student-history.json';
import {checkTrace,readTraceHistory,storedTraceHistory} from '../src/student/traceHistory.ts';

const attempt=fixture.attempts[0];
const valid={schema:'student-diagnosis.v1',engine_revision:'b'.repeat(40),outcome:'first_invalid',step:1,
 category:'reference',message:'Rivedi il riferimento.',focus:['R2','R1'],circuit_fingerprint:attempt.circuitFingerprint};
afterEach(()=>vi.unstubAllGlobals());
describe('risposte del controllo',()=>{
 it('lega un esito interpretabile alla richiesta e conserva solo input portabili',async()=>{
  const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify(valid)));
  vi.stubGlobal('fetch',fetch);
  const result=await checkTrace(fixture.netlist,attempt.circuitFingerprint,attempt.steps);
  expect(result).toEqual(valid);
  expect(JSON.parse(fetch.mock.calls[0][1].body).trace.steps).toEqual(attempt.steps);
  const stored=storedTraceHistory([{...attempt,diagnosis:result}]);
  expect(stored).toEqual([attempt]);
  stored[0].steps[0].first='changed';
  expect(attempt.steps[0].first).toBe('R2');
 });
 it.each([
  {...valid,schema:'future'}, {...valid,engine_revision:'missing'}, {...valid,circuit_fingerprint:'0'.repeat(64)},
  {...valid,outcome:'certified'}, {...valid,step:33}, {...valid,focus:[42]}, {...valid,message:42},
  {...valid,step:null}, {...valid,outcome:'valid_so_far',step:1},
 ])('rifiuta risposte non interpretabili o riferite a un altro circuito',async result=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify(result))));
  await expect(checkTrace(fixture.netlist,attempt.circuitFingerprint,attempt.steps)).rejects.toThrow('Diagnosi');
 });
 it('propaga il rifiuto del backend senza produrre un controllo valido',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({message:'Rifiuto esplicito.'}),{status:422})));
  await expect(checkTrace(fixture.netlist,attempt.circuitFingerprint,attempt.steps)).rejects.toThrow('Rifiuto esplicito');
 });
 it('limita i byte UTF8 della cronologia prima della richiesta PDF',()=>{
  const step={...attempt.steps[0],transcription:'字'.repeat(500),first:'字'.repeat(500),second:'字'.repeat(500)};
  const large=Array(32).fill({...attempt,steps:Array(32).fill(step)});
  expect(()=>readTraceHistory(large,attempt.circuitFingerprint)).toThrow('2,5 MB');
 });
});
