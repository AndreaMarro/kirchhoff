import {defineConfig} from 'vite';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const required=['web/mcp-app-template.html','web/src/mcp-app.ts','web/src/student/safeSvg.ts','web/src/student/lessonMath.ts',
 'web/package.json','web/package-lock.json','web/vite.mcp.config.ts'];
const hash=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');

export default defineConfig({
 plugins:[{
  name:'kirchhoff-mcp-app-provenance',
  writeBundle(){
   const sources=new Set(required);
   for(const id of this.getModuleIds()){
    const path=relative(root,id);
    if(path.startsWith('web/src/')&&!path.includes('?'))sources.add(path);
   }
   const manifest={schema:'kirchhoff-mcp-app-build.v1',
    bundle_sha256:hash(readFileSync(resolve(root,'web/dist/mcp/kirchhoff-mcp-app.iife.js'))),
    sources:Object.fromEntries([...sources].sort().map(path=>[path,hash(readFileSync(resolve(root,path)))]))};
   writeFileSync(resolve(root,'web/dist/mcp/build-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  },
 }],
 build:{
  outDir:'dist/mcp',emptyOutDir:false,target:'es2022',sourcemap:false,
  lib:{entry:'src/mcp-app.ts',name:'KirchhoffMcpApp',formats:['iife'],fileName:'kirchhoff-mcp-app'},
 },
});
