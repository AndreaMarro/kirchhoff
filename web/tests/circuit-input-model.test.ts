import {describe,expect,it} from 'vitest';
import {circuitInputNetlist,parseCircuitInputNetlist,readCircuitInput,circuitInputValueUnit} from '../src/student/circuitInputModel';

const circuit='@ac 2 rad/s\n@amplitude unspecified\nV1 e 0 20 volt 0deg\nR1 e A 3 ohm\nR2 A b 2 ohm\nL1 b 0 1 henry\n? impedance A 0';

describe('impedenza di porta nell’editor di componenti',()=>{
 it('conserva i morsetti, la pulsazione e i valori senza chiedere RMS o picco',()=>{
  const model=parseCircuitInputNetlist(circuit);
  expect(model.request).toEqual({quantity:'impedance',from:'A',to:'0',target:''});
  expect(circuitInputNetlist(model)).toBe(circuit);
 });
 it('impedisce che la domanda AC diventi silenziosamente una resistenza DC',()=>{
  const model=parseCircuitInputNetlist(circuit);model.domain='dc';model.components=model.components.filter(c=>c.kind!=='L');
  expect(()=>circuitInputNetlist(model)).toThrow(/impedenza di porta richiede il regime sinusoidale/);
 });
 it('rifiuta morsetti assenti o coincidenti e non inventa il collegamento',()=>{
  const model=parseCircuitInputNetlist(circuit);
  for(const to of ['missing','A'])expect(()=>circuitInputNetlist({...model,request:{...model.request,to}})).toThrow(/morsetti presenti e distinti/);
 });
 it('conserva richieste di resistenza e la loro restrizione al regime continuo',()=>{
  const model=parseCircuitInputNetlist('V1 a 0 12 volt\nR1 a 0 6 ohm\n? resistance a 0');
  expect(circuitInputNetlist(model)).toContain('? resistance a 0');
  model.domain='ac';model.omega='2';model.components[0].phase='0';
  expect(()=>circuitInputNetlist(model)).toThrow(/resistenza di porta richiede il regime continuo/);
 });
});

describe('Laplace: forma delle sorgenti, unità e stato iniziale',()=>{
 const rc='@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 3 farad\n@initial C1 voltage -4 volt\n? voltage C1';
 it('riapre un gradino e conserva lo stato iniziale firmato senza chiedere testo esperto',()=>{
  const model=parseCircuitInputNetlist(rc);
  expect(model.domain).toBe('laplace');expect(model.components[0].waveform).toBe('step');
  expect(model.components[2].initial).toBe('-4');expect(circuitInputNetlist(model)).toBe(rc);
  expect(readCircuitInput(JSON.parse(JSON.stringify(model)))).toEqual(model);
 });
 it('distingue area impulsiva e ampiezza e non cambia il valore inserito',()=>{
  const model=parseCircuitInputNetlist(rc.replace('10 volt step','7/3 volt*s impulse'));
  expect(circuitInputValueUnit(model.components[0],'laplace')).toBe('volt*s');
  expect(circuitInputNetlist(model)).toContain('7/3 volt*s impulse');
  model.components[0].waveform='step';expect(circuitInputNetlist(model)).toContain('7/3 volt step');
  for(const bad of ['7/3 volt impulse','7/3 volt*s step','7/3 volt cosine','7/3 volt'])
   expect(()=>parseCircuitInputNetlist(rc.replace('10 volt step',bad))).toThrow();
 });
 it('richiede la dichiarazione anche degli stati nulli e di tutte le sorgenti',()=>{
  const model=parseCircuitInputNetlist(rc);delete model.components[2].initial;
  expect(()=>circuitInputNetlist(model)).toThrow(/stato iniziale/);
  model.components[2].initial='0';expect(circuitInputNetlist(model)).toContain('@initial C1 voltage 0 volt');
  delete model.components[0].waveform;expect(()=>circuitInputNetlist(model)).toThrow(/gradino o impulso/);
 });
 it('accetta gli stati prima dei componenti e conserva le correnti negative nell’induttore',()=>{
  const model=parseCircuitInputNetlist('@laplace\n@initial L1 current -2 ampere\nR1 a 0 3 ohm\nL1 a 0 2 henry\n? current L1');
  expect(circuitInputNetlist(model)).toContain('@initial L1 current -2 ampere');
 });
 it('rifiuta stati duplicati, riferimenti o unità discordanti e righe ignorate',()=>{
  for(const declaration of ['@initial C1 current 4 ampere','@initial C1 voltage 4 ampere','@initial R1 voltage 4 volt','@initial missing voltage 4 volt','@initial C1 voltage 4 volt\n@initial C1 voltage 5 volt'])
   expect(()=>parseCircuitInputNetlist(rc.replace('@initial C1 voltage -4 volt',declaration))).toThrow();
  expect(()=>parseCircuitInputNetlist(rc+'\n@initial C1 voltage 0 volt')).toThrow();
 });
 it('conserva gli stati al cambio di regime e rifiuta domande non disponibili',()=>{
  const model=parseCircuitInputNetlist(rc);model.domain='ac';model.omega='2';model.components[0].phase='0';
  expect(circuitInputNetlist(model)).not.toContain('@initial');model.domain='laplace';
  expect(circuitInputNetlist(model)).toBe(rc);
  model.request.quantity='power';expect(()=>circuitInputNetlist(model)).toThrow(/potenza richiede/);
 });
});
