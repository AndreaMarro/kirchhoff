import {describe,it,expect} from 'vitest';
import {buildNetlist,coveredPoints,type Part} from '../src/student/CircuitEditor.tsx';
describe('Lavagna: connessioni elettriche esplicite',()=>{
 it('un filo unisce anche il punto intermedio visibile',()=>{
  const parts:Part[]=[{kind:'W',a:8,b:10,id:'W1',value:'0'},{kind:'V',a:0,b:8,id:'V1',value:'12'},{kind:'R',a:0,b:9,id:'R1',value:'100'}];
  const text=buildNetlist(parts,8);expect(text).toContain('V1 n0 0 12 volt');expect(text).toContain('R1 n0 0 100 ohm');
 });
 it('un corpo di componente non unisce il nodo intermedio',()=>{
  const text=buildNetlist([{kind:'R',a:0,b:8,id:'R1',value:'100'},{kind:'V',a:4,b:8,id:'V1',value:'5'}],8);
  expect(text).toContain('V1 n4 0 5 volt');expect(text).toContain('R1 n0 0 100 ohm');
 });
 it('preserva il verso del generatore e le frazioni',()=>{
  const text=buildNetlist([{kind:'I',a:8,b:0,id:'I1',value:'1/3'},{kind:'R',a:0,b:8,id:'R1',value:'6'}],8);
  expect(text).toContain('I1 0 n0 1/3 ampere');expect(text).toContain('? voltage R1');
 });
 it('copre il tratto geometrico in entrambe le direzioni',()=>{
  expect(coveredPoints({a:0,b:8})).toEqual([0,4,8]);expect(coveredPoints({a:8,b:0})).toEqual([0,4,8]);
  expect(coveredPoints({a:8,b:10})).toEqual([8,9,10]);expect(coveredPoints({a:0,b:5})).toEqual([]);
 });
 it('rifiuta la lavagna vuota',()=>expect(()=>buildNetlist([],8)).toThrow());
});
