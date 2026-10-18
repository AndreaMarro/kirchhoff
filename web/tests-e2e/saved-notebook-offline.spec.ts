import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

async function savedFile(page:import('@playwright/test').Page){
 await page.goto('/');await page.locator('.student-lesson[aria-busy=false]').waitFor();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Salva quaderno ↓',exact:true}).click();
 return await readFile(await(await download).path());
}

test('un errore HTTP delle capability rimane visibile e non apre la copia',async({page})=>{
 const bytes=await savedFile(page);
 await page.route('**/api/capabilities',route=>route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({message:'Capability temporaneamente in errore'})}));
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:bytes});
 await expect(page.getByRole('alert')).toContainText('Capability temporaneamente in errore');
 await expect(page.getByRole('heading',{name:'Copia salvata · sola lettura'})).toHaveCount(0);
});

test('chiudere la copia invalida un ricalcolo ancora in attesa',async({page})=>{
 const bytes=await savedFile(page);
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:bytes});
 await expect(page.getByRole('heading',{name:'Copia salvata · sola lettura'})).toBeVisible();
 await page.route('**/api/capabilities',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({solve:true,vision:false})}));
 let release!:()=>void;const gate=new Promise<void>(resolve=>{release=resolve;});
 let arrived!:()=>void;const started=new Promise<void>(resolve=>{arrived=resolve;});
 await page.route('**/api/solve',async route=>{arrived();await gate;await route.abort('failed');});
 try{
  await page.getByRole('button',{name:'Riapri con ricalcolo',exact:true}).click();await started;
  await page.getByRole('button',{name:'Torna al laboratorio',exact:true}).click();
  await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
  const failed=page.waitForEvent('requestfailed',request=>request.url().endsWith('/api/solve'));
  release();await failed;
  await expect(page.getByRole('heading',{name:'Il circuito, passo per passo.'})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Copia salvata · sola lettura'})).toHaveCount(0);
 }finally{release();}
});

test('quaderno: chiusura pagina, riapertura senza rete e copia in sola lettura senza nuovi giudizi',async({page,context,baseURL},info)=>{
 await page.goto('/');
 await page.locator('.student-lesson[aria-busy=false]').waitFor();
 await expect(page.getByText(/Spiegazioni DRAFT/)).toBeVisible();
 await page.screenshot({path:info.outputPath('online-draft.png'),fullPage:true});
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Salva quaderno ↓',exact:true}).click();
 const bytes=await readFile(await(await download).path());
 const bundle=JSON.parse(bytes.toString());expect(bundle.savedLesson.view.contentStatus).toBe('DRAFT');
 await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller));
 const keys=await page.evaluate(async()=>{
  const names=(await caches.keys()).filter(name=>name.startsWith('kirchhoff-reader-'));
  return(await Promise.all(names.map(async name=>(await(await caches.open(name)).keys()).map(r=>new URL(r.url).pathname)))).flat();
 });
 expect(keys.length).toBeGreaterThan(0);expect(keys.some(path=>path.includes('/api/'))).toBe(false);
 await page.close();await context.setOffline(true);
 const cold=await context.newPage();await cold.goto(baseURL!);
 let solves=0;cold.on('request',r=>{if(r.url().endsWith('/api/solve'))solves++;});
 await cold.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:bytes});
 await expect(cold.getByRole('heading',{name:'Copia salvata · sola lettura'})).toBeVisible();
 await expect(cold.getByText(/non sono ricontrollati/)).toBeVisible();
 await expect(cold.locator('.saved-notebook .student-drawing svg')).toHaveCount(1);
 const next=cold.getByRole('button',{name:'Passo successivo',exact:true});
 if(await next.isEnabled()){await next.click();await expect(cold.locator('.saved-notebook [aria-current=step]')).toHaveCount(1);}
 await expect(cold.getByRole('button',{name:'Controlla i passaggi',exact:true})).toHaveCount(0);
 expect(solves).toBe(0);
 await cold.screenshot({path:info.outputPath('offline-saved.png'),fullPage:true});
 const exported=cold.waitForEvent('download');await cold.getByRole('button',{name:'Conserva questo quaderno',exact:true}).click();
 expect(JSON.parse((await readFile(await(await exported).path())).toString())).toEqual(bundle);
});

test('l’attivazione offline non cancella la cache di un altro scope sulla stessa origine',async({page,baseURL})=>{
 await page.route('**/__cache-probe',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Fixture cache</title>'}));
 await page.goto('/__cache-probe');
 const name='kirchhoff-reader-'+encodeURIComponent(new URL('other/',baseURL).href)+'-legacy';
 await page.evaluate(async name=>{const cache=await caches.open(name);await cache.put('/other/sentinel',new Response('conservato'));},name);
 await page.goto('/');await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller));
 expect(await page.evaluate(async name=>(await(await caches.open(name)).match('/other/sentinel'))?.text(),name)).toBe('conservato');
});
