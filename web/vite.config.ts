import { defineConfig } from "vitest/config";
import type {Plugin} from 'vite';
import {createHash} from 'node:crypto';
import {readdirSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';

function publicFiles(directory:string,prefix=''):string[]{
 return readdirSync(directory,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?publicFiles(resolve(directory,entry.name),prefix+entry.name+'/'):entry.isFile()?[prefix+entry.name]:[]);
}

export function offlineReaderPlugin(publicDirectory:string):Plugin{
 return {
    name:'kirchhoff-offline-reader',
    generateBundle(_options,bundle){
      const core=['index.html',...Object.keys(bundle).filter(path=>path!=='index.html'&&!path.endsWith('.map'))].sort();
      const files=publicFiles(publicDirectory).sort();
      const allowed=[...new Set([...core,...files])];
      const digest=createHash('sha256').update(JSON.stringify(allowed));
      for(const path of files)digest.update(JSON.stringify(path)).update(readFileSync(resolve(publicDirectory,path)));
      for(const path of Object.keys(bundle).sort()){
       const item=bundle[path];digest.update(JSON.stringify(path)).update(item.type==='chunk'?item.code:item.source);
      }
      const revision=digest.digest('hex').slice(0,20);
      this.emitFile({type:'asset',fileName:'offline-sw.js',source:`
const PREFIX='kirchhoff-reader-'+encodeURIComponent(self.registration.scope)+'-';
const CACHE=PREFIX+${JSON.stringify(revision)};
const CORE=${JSON.stringify(core)};
const ALLOWED=new Set(${JSON.stringify(allowed)}.map(path=>new URL(path,self.registration.scope).href));
const INDEX=new URL('index.html',self.registration.scope).href;
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE.map(path=>new URL(path,self.registration.scope).href)))));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const name of await caches.keys())if(name.startsWith(PREFIX)&&name!==CACHE)await caches.delete(name);
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url),scope=new URL(self.registration.scope);
 if(request.method!=='GET'||url.origin!==scope.origin||url.pathname.startsWith(scope.pathname+'api/'))return;
 if(request.mode==='navigate'&&(url.pathname===scope.pathname||url.href.split('?')[0]===INDEX)){
  event.respondWith(fetch(request).catch(async()=>{const saved=await caches.match(INDEX,{cacheName:CACHE});if(!saved)throw new Error('Pagina offline non disponibile');return saved;}));return;
 }
 url.search='';url.hash='';if(!ALLOWED.has(url.href))return;
 event.respondWith((async()=>{
  const cache=await caches.open(CACHE);
  try{const response=await fetch(request);if(response.ok&&response.type!=='opaque')await cache.put(url.href,response.clone());return response;}
  catch(error){const saved=await cache.match(url.href);if(saved)return saved;throw error;}
 })());
});`});
    },
  };
}

export default defineConfig({
  plugins:[offlineReaderPlugin(resolve(import.meta.dirname,'public'))],
  base: "./",
  publicDir: "public",
  build: {
    outDir: "dist",
    sourcemap: false,
    target: "es2022",
  },
  server: {
    port: 5173,
  },
  test: {
    // Solo unit test: le specifiche Playwright vivono in tests-e2e/
    // e le esegue `npm run test:e2e`, non vitest.
    include: ["tests/**/*.test.ts"],
  },
});
