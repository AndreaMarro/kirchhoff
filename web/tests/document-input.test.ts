import {expect,it} from 'vitest';
import {validateCrop,wholePage} from '../src/student/documentInput';
it('conserva il riferimento normalizzato al ritaglio della fonte',()=>{
 expect(validateCrop({x:.2,y:.1,width:.7,height:.6})).toEqual({x:.2,y:.1,width:.7,height:.6});
 expect(validateCrop(wholePage)).toEqual({x:0,y:0,width:1,height:1});
});
it('rifiuta ritagli vuoti, fuori pagina o con coordinate non finite',()=>{
 for(const crop of [{x:-.1,y:0,width:1,height:1},{x:0,y:0,width:0,height:1},{x:.5,y:0,width:.8,height:1},{x:NaN,y:0,width:1,height:1}])
  expect(()=>validateCrop(crop)).toThrow('pagina');
});
