import {expect,test} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const netlist='V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2';
const trace=[{transcription:'R1+R2=320',operation:'serie',first:'R1',second:'R2',claimed_value:'320',reading:'clear'}];
const bundle={schema:'kirchhoff-portable-session.v1',netlist,method:'auto',circuitFingerprint:createHash('sha256').update(netlist).digest('hex'),
 answerExact:'33/4',engineRevision:'saved-revision',selectedStep:2,showOriginal:true,boardScene:'',traceSteps:trace,priorImageSha256:null};

test('il quaderno si riapre dopo un ricalcolo e conserva il tentativo',async({page})=>{
 const lesson=await readFile(new URL('../public/lessons/partitore-d1-auto.json',import.meta.url),'utf8');
 let solved=0;
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:false}}));
 await page.route('**/api/solve',route=>{solved++;return route.fulfill({body:lesson,contentType:'application/json'});});
 await page.goto('/');
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
 await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata dal circuito salvato/)).toBeVisible();
 await expect(page.getByRole('textbox',{name:'Testo passaggio 1'})).toHaveValue('R1+R2=320');
 await expect(page.locator('.student-outline button[aria-current="step"]')).toContainText('Usiamo il partitore');
 expect(solved).toBe(1);
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8'));
 expect(saved.traceSteps).toEqual(trace);
 expect(saved.circuitFingerprint).toBe(bundle.circuitFingerprint);
 expect(saved.method).toBe('auto');
 expect(saved.selectedStep).toBe(2);
});

test('un quaderno alterato è fermato prima del ricalcolo',async({page})=>{
 let solved=0;
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:false}}));
 await page.route('**/api/solve',route=>{solved++;return route.fulfill({status:500,json:{message:'non chiamare'}});});
 await page.goto('/');
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'alterato.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({...bundle,netlist:netlist.replace('220','221')}))});
 await expect(page.getByRole('alert').first()).toContainText('modificato');
 expect(solved).toBe(0);
});

test('il salvataggio attende uno snapshot attuale della lavagna libera',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Lavagna libera'}).click();
 await expect(page.frameLocator('iframe[title="Lavagna libera Excalidraw"]').getByRole('button',{name:'Salva disegno'})).toBeVisible();
 await expect(page.frameLocator('iframe[title="Lavagna libera Excalidraw"]').getByRole('button',{name:'Usa selezione →'})).toBeVisible();
 await page.getByRole('button',{name:'Chiudi ingresso circuito'}).click();
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8'));
 expect(saved.boardScene).toBe('');
 await expect(page.getByRole('alert')).toHaveCount(0);
});
