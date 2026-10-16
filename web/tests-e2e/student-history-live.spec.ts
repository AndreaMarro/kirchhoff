import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {readFileSync} from 'node:fs';
const fixture:{netlist:string;attempts:Array<{steps:Array<{transcription:string;operation:string;first:string;second:string;claimed_value:string;reading:string}>}>}=
 JSON.parse(readFileSync(new URL('../tests/fixtures/student-history.json',import.meta.url),'utf8'));

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
test.skip(!base,'Avvia il server reale e imposta KIRCHHOFF_LIVE_BASE_URL.');

async function ownCircuit(page:import('@playwright/test').Page){
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 if(!await page.getByRole('textbox',{name:'Circuito da risolvere'}).isVisible())
  await page.getByText('Vista esperta: testo del circuito',{exact:true}).click();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(fixture.netlist);
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.getByRole('dialog')).toBeHidden();
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
}
async function fill(page:import('@playwright/test').Page,index:number){
 const step=fixture.attempts[index].steps[0];
 await page.getByRole('textbox',{name:'Testo passaggio 1'}).fill(step.transcription);
 await page.getByRole('combobox',{name:'Operazione passaggio 1'}).selectOption(step.operation);
 await page.getByRole('textbox',{name:'Primo componente passaggio 1'}).fill(step.first);
 await page.getByRole('textbox',{name:'Secondo componente passaggio 1'}).fill(step.second);
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill(step.claimed_value);
 await page.getByRole('combobox',{name:'Lettura passaggio 1'}).selectOption(step.reading);
}

test('sequenza errore-correzione e illeggibile sopravvive a nuovo contesto e PDF reale',async({page,browser})=>{
 await ownCircuit(page);
 for(let i=0;i<4;i++){
  await fill(page,i);
  await page.getByRole('button',{name:'Controlla i passaggi'}).click();
  await expect(page.locator('.student-trace-history summary')).toHaveCount(i+1);
 }
 const summary=page.locator('.student-trace-history summary');
 await expect(summary.nth(0)).toContainText('riferimento');
 await expect(summary.nth(1)).toContainText('calcolo');
 await expect(summary.nth(2)).toContainText('validi');
 await expect(summary.nth(3)).toContainText('non valutabile');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const buffer=await readFile(await (await download).path());
 const saved=JSON.parse(buffer.toString());
 expect(saved.schema).toBe('kirchhoff-portable-session.v3');
 expect(saved.traceHistory.map((a:{steps:unknown})=>a.steps)).toEqual(fixture.attempts.map(a=>a.steps));
 expect(saved.traceHistory.every((a:object)=>!('diagnosis' in a))).toBe(true);
 const viewport=page.viewportSize()!;
 const cold=await browser.newContext({viewport});
 try{
  const reopened=await cold.newPage();await reopened.goto(base!);
  await reopened.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer});
  await expect(reopened.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
  await expect(reopened.locator('.student-trace-history summary')).toHaveCount(4);
  await expect(reopened.locator('.student-trace-history summary').nth(0)).toContainText('riferimento');
  await reopened.locator('.student-trace-history summary').nth(0).click();
  await reopened.getByRole('button',{name:'Riprendi tentativo 1'}).click();
  await reopened.getByRole('textbox',{name:'Secondo componente passaggio 1'}).fill('R2');
  await reopened.getByRole('textbox',{name:'Valore passaggio 1'}).fill('8');
  await reopened.getByRole('button',{name:'Controlla i passaggi'}).click();
  await expect(reopened.locator('.student-trace-history summary')).toHaveCount(5);
  await expect(reopened.locator('.student-trace-history summary').nth(4)).toContainText('validi');
  const resave=reopened.waitForEvent('download');await reopened.getByRole('button',{name:'Salva quaderno ↓'}).click();
  const updated=JSON.parse(await readFile(await (await resave).path(),'utf8'));
  expect(updated.traceHistory[0].steps[0].second).toBe('R1');
  expect(updated.traceHistory[4].steps[0].second).toBe('R2');
  const pdf=reopened.waitForEvent('download');await reopened.getByRole('button',{name:'Scarica PDF ↓'}).click();
  const bytes=await readFile(await (await pdf).path());
  expect(bytes.subarray(0,5).toString()).toBe('%PDF-');
  expect(bytes.toString('latin1')).toContain('Tentativo 5');
  expect(bytes.toString('latin1')).toContain('V_R2 = I_R2 * R1 = 4 V');
 }finally{await cold.close();}
});

test('PDF del catalogo include i controlli via API anziche ometterli nel documento statico',async({page})=>{
 await page.goto(base!);
 await expect(page.getByRole('heading',{name:'Controlla il tuo procedimento'})).toBeVisible();
 await fill(page,0);
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-history summary')).toHaveCount(1);
 let staticRequests=0;
 await page.route('**/lessons/*.pdf',route=>{staticRequests++;return route.continue();});
 const request=page.waitForRequest(r=>r.url().endsWith('/api/pdf'));
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Scarica PDF ↓'}).click();
 expect((await request).postDataJSON().trace_history).toHaveLength(1);
 expect((await readFile(await (await download).path())).toString('latin1')).toContain('Tentativo 1');
 expect(staticRequests).toBe(0);
});

test('rete assente, rifiuto e risposta superata non aggiungono tentativi',async({page})=>{
 await ownCircuit(page);await fill(page,0);
 await page.route('**/api/diagnose',route=>route.abort('connectionfailed'));
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace [role=alert]')).toBeVisible();
 await expect(page.locator('.student-trace-history summary')).toHaveCount(0);
 await page.unroute('**/api/diagnose');
 await page.route('**/api/diagnose',async route=>{
  const body=route.request().postDataJSON();body.trace.circuit_fingerprint='0'.repeat(64);
  const response=await route.fetch({postData:JSON.stringify(body)});await route.fulfill({response});
 });
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace [role=alert]')).toContainText('circuito è cambiato');
 await expect(page.locator('.student-trace-history summary')).toHaveCount(0);
 await page.unroute('**/api/diagnose');
 let release!:()=>void,ready!:()=>void;
 const gate=new Promise<void>(resolve=>{release=resolve;});
 const responseReady=new Promise<void>(resolve=>{ready=resolve;});
 await page.route('**/api/diagnose',async route=>{
  const response=await route.fetch();ready();await gate;await route.fulfill({response});
 });
 try{
  await page.getByRole('button',{name:'Controlla i passaggi'}).click();await responseReady;
  await expect(page.getByRole('button',{name:'Salva quaderno ↓'})).toBeDisabled();
  await page.getByRole('textbox',{name:'Testo passaggio 1'}).fill('Nuova bozza non controllata');
  const done=page.waitForResponse(r=>r.url().endsWith('/api/diagnose'));
  release();await (await done).finished();
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  await expect(page.locator('.student-trace-history summary')).toHaveCount(0);
  await expect(page.locator('.student-trace-result')).toHaveCount(0);
 }finally{release();await page.unrouteAll({behavior:'wait'});}
 await fill(page,2);await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-history summary')).toHaveCount(1);
 await expect(page.locator('.student-trace-history summary')).toContainText('validi');
});
