import {it,expect} from 'vitest';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {offlineReaderPlugin} from '../vite.config.ts';

it('cambiare il contenuto pubblico a parità di nome produce una nuova revisione offline',async()=>{
 const directory=mkdtempSync(join(tmpdir(),'kirchhoff-public-'));
 try{
  async function worker(){
   const plugin=offlineReaderPlugin(directory);let source='';
   const hook=plugin.generateBundle!;
   const generate=typeof hook==='function'?hook:hook.handler;
   await generate.call({emitFile(asset:{source:string}){source=asset.source;}} as never,{} as never,{},false);
   return source;
  }
  writeFileSync(join(directory,'lesson.json'),'prima versione');const before=await worker();
  writeFileSync(join(directory,'lesson.json'),'seconda versione');const after=await worker();
  expect(after).not.toBe(before);
  expect(after).toContain('lesson.json');
 }finally{rmSync(directory,{recursive:true,force:true});}
});
