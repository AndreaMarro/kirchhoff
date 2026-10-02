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
 it('un incrocio interno di due fili non crea una giunzione elettrica',()=>{
  const parts:Part[]=[{kind:'W',a:4,b:7,id:'W1',value:'0'},{kind:'W',a:1,b:9,id:'W2',value:'0'},{kind:'R',a:7,b:8,id:'R1',value:'100'},{kind:'R',a:9,b:8,id:'R2',value:'200'}];
  const lines=buildNetlist(parts,8).split('\n');
  expect(lines.find(x=>x.startsWith('R1 '))?.split(' ')[1]).not.toBe(lines.find(x=>x.startsWith('R2 '))?.split(' ')[1]);
 });
 it('una giunzione esplicita collega i fili che si incrociano',()=>{
  const parts:Part[]=[{kind:'W',a:4,b:7,id:'W1',value:'0'},{kind:'W',a:1,b:9,id:'W2',value:'0'},{kind:'J',a:5,b:5,id:'J1',value:'0'},{kind:'R',a:7,b:8,id:'R1',value:'100'},{kind:'R',a:9,b:8,id:'R2',value:'200'}];
  const lines=buildNetlist(parts,8).split('\n');
  expect(lines.find(x=>x.startsWith('R1 '))?.split(' ')[1]).toBe(lines.find(x=>x.startsWith('R2 '))?.split(' ')[1]);
  expect(lines.some(x=>x.startsWith('J1 '))).toBe(false);
 });
 it('la fine di un filo sul tratto di un altro crea una derivazione a T',()=>{
  const parts:Part[]=[{kind:'W',a:4,b:7,id:'W1',value:'0'},{kind:'W',a:1,b:5,id:'W2',value:'0'},{kind:'R',a:7,b:8,id:'R1',value:'100'},{kind:'R',a:1,b:8,id:'R2',value:'200'}];
  const lines=buildNetlist(parts,8).split('\n');
  expect(lines.find(x=>x.startsWith('R1 '))?.split(' ')[1]).toBe(lines.find(x=>x.startsWith('R2 '))?.split(' ')[1]);
 });
 it('rifiuta la lavagna vuota',()=>expect(()=>buildNetlist([],8)).toThrow());
 it('mantiene la domanda scelta sul componente esatto',()=>{
  const parts:Part[]=[{kind:'V',a:0,b:8,id:'V1',value:'12'},{kind:'R',a:0,b:8,id:'R1',value:'100'},{kind:'R',a:4,b:8,id:'R2',value:'200'}];
  expect(buildNetlist(parts,8,{quantity:'current',target:'R2'})).toMatch(/\? current R2$/);
  expect(buildNetlist(parts,8,{quantity:'voltage',target:'V1'})).toMatch(/\? voltage V1$/);
  expect(()=>buildNetlist(parts,8,{quantity:'power',target:'R2'})).toThrow(/grandezza/i);
  expect(()=>buildNetlist(parts,8,{quantity:'current',target:'R3'})).toThrow(/componente/i);
 });
});
