import {describe,expect,it} from 'vitest';
import {elementsForInterpretation} from '../../companion-board/selection.ts';

describe('selezione dei tratti da interpretare',()=>{
 const elements=[{id:'circuit',isDeleted:false},{id:'equation',isDeleted:false},{id:'erased',isDeleted:true}];
 it('invia solo i tratti selezionati e vivi',()=>{
  expect(elementsForInterpretation(elements,{equation:true,erased:true},true).map(x=>x.id)).toEqual(['equation']);
 });
 it('mantiene il disegno intero solo su scelta esplicita',()=>{
  expect(elementsForInterpretation(elements,{equation:true},false).map(x=>x.id)).toEqual(['circuit','equation']);
 });
 it('rifiuta una selezione vuota senza ripiegare silenziosamente sul disegno intero',()=>{
  expect(()=>elementsForInterpretation(elements,{erased:true},true)).toThrow(/Seleziona/);
 });
});
