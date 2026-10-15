import {expect,test} from '@playwright/test';
import {createHash} from 'node:crypto';

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
test.skip(!base,'Richiede il server Kirchhoff locale reale.');
const netlist='V1 b 0 12 volt\nR1 b a 1000 ohm\nR2 a 0 2000 ohm\n? current R1';
const bundle=Buffer.from(JSON.stringify({
 schema:'kirchhoff-portable-session.v2',netlist,method:'auto',
 circuitFingerprint:createHash('sha256').update(netlist).digest('hex'),answerExact:'1/250',
 engineRevision:'precedente',selectedStep:4,showOriginal:false,boardScene:'',
 traceSteps:[{transcription:'',operation:'serie',first:'',second:'',claimed_value:null,reading:'clear'}],
 priorImageSha256:null,
}));
const file={name:'quaderno.json',mimeType:'application/json',buffer:bundle};

test('la prima apertura attende capabilities reali ancora in arrivo',async({page})=>{
 let release=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;});
 let arrived=()=>{};const capabilitiesArrived=new Promise<void>(resolve=>{arrived=resolve;});
 let solves=0;page.on('request',request=>{if(request.url().endsWith('/api/solve')&&request.method()==='POST')solves++;});
 await page.route('**/api/capabilities',async route=>{
  const response=await route.fetch();expect(response.status()).toBe(200);
  arrived();await gate;await route.fulfill({response});
 });
 try{
  await page.goto(base!,{waitUntil:'domcontentloaded'});
  await capabilitiesArrived;
  await page.locator('.student-lesson[aria-busy=false]').waitFor();
  await page.locator('input[type=file][accept*="application/json"]').setInputFiles(file);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','true');
  expect(solves).toBe(0);
  release();
  await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
  await expect(page.locator('.student-result')).toContainText('1/250');
  expect(solves).toBe(1);
 }finally{release();}
});

test('un server indisponibile è dichiarato e un nuovo tentativo può recuperare',async({page})=>{
 let checks=0,solves=0;
 page.on('request',request=>{if(request.url().endsWith('/api/solve')&&request.method()==='POST')solves++;});
 await page.route('**/api/capabilities',async route=>{checks++;await route.fulfill({status:503,contentType:'application/json',body:'{}'});});
 await page.goto(base!);
 await page.locator('.student-lesson[aria-busy=false]').waitFor();
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles(file);
 await expect(page.getByRole('alert')).toContainText('Per riaprire un quaderno serve il server Kirchhoff.');
 expect(checks).toBeGreaterThan(0);expect(solves).toBe(0);
 await page.unroute('**/api/capabilities');
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles(file);
 await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
 await expect(page.locator('.student-result')).toContainText('1/250');
 expect(solves).toBe(1);
});

test('un catalogo iniziale in ritardo non sostituisce il quaderno scelto',async({page})=>{
 let releaseCapabilities=()=>{},releaseCatalog=()=>{},capabilitiesArrived=()=>{},catalogArrived=()=>{};
 const capabilitiesGate=new Promise<void>(resolve=>{releaseCapabilities=resolve;});
 const catalogGate=new Promise<void>(resolve=>{releaseCatalog=resolve;});
 const capabilityResponse=new Promise<void>(resolve=>{capabilitiesArrived=resolve;});
 const catalogResponse=new Promise<void>(resolve=>{catalogArrived=resolve;});
 let solves=0;page.on('request',request=>{if(request.url().endsWith('/api/solve')&&request.method()==='POST')solves++;});
 await page.route('**/api/capabilities',async route=>{const response=await route.fetch();capabilitiesArrived();await capabilitiesGate;await route.fulfill({response});});
 await page.route('**/lessons/index.json',async route=>{const response=await route.fetch();catalogArrived();await catalogGate;await route.fulfill({response});});
 try{
  await page.goto(base!,{waitUntil:'domcontentloaded'});
  await Promise.all([capabilityResponse,catalogResponse]);
  await page.locator('input[type=file][accept*="application/json"]').setInputFiles(file);
  releaseCatalog();
  await expect(page.getByRole('option',{name:'Una sorgente, due resistori',exact:true})).toBeAttached();
  releaseCapabilities();
  await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
  await expect(page.locator('.student-result')).toContainText('1/250');
  expect(solves).toBe(1);
 }finally{releaseCapabilities();releaseCatalog();}
});

for(const source of ['file','editor'] as const)test(`una nuova fonte ${source} annulla l’apertura in attesa e libera il comando di calcolo`,async({page})=>{
 let release=()=>{},arrived=()=>{};
 const gate=new Promise<void>(resolve=>{release=resolve;});
 const capabilitiesArrived=new Promise<void>(resolve=>{arrived=resolve;});
 const solves:string[]=[];
 page.on('request',request=>{if(request.url().endsWith('/api/solve')&&request.method()==='POST')solves.push(request.postDataJSON().netlist);});
 await page.route('**/api/capabilities',async route=>{const response=await route.fetch();arrived();await gate;await route.fulfill({response});});
 try{
  await page.goto(base!,{waitUntil:'domcontentloaded'});await capabilitiesArrived;
  await page.locator('.student-lesson[aria-busy=false]').waitFor();
  await page.locator('input[type=file][accept*="application/json"]').setInputFiles(file);
  await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','true');
  await page.getByRole('button',{name:/Il tuo circuito/}).click();
  const newNetlist=source==='file'?netlist.replace('12 volt','24 volt'):'V1 n0 0 12 volt\nR1 n0 0 100 ohm\n? voltage R1';
  if(source==='file'){
   await page.getByRole('button',{name:'Foto o file',exact:true}).click();
   await page.locator('input[type=file][accept*=".net"]').setInputFiles({name:'nuovo.net',mimeType:'text/plain',buffer:Buffer.from(newNetlist)});
  }else{
   await page.getByRole('button',{name:'Schema a componenti',exact:true}).click();
   const node=async(index:number)=>{await page.getByRole('button',{name:new RegExp(`^Nodo ${index}(?: |$)`)}).click();};
   await page.getByRole('button',{name:'Tensione',exact:true}).click();await node(0);await node(8);
   await page.getByRole('button',{name:'Resistore',exact:true}).click();await node(3);await node(11);
   await page.getByRole('button',{name:'Filo',exact:true}).click();await node(0);await node(3);await node(8);await node(11);
   await page.getByRole('button',{name:/Usa il circuito disegnato/}).click();
  }
  if(!await page.getByRole('textbox',{name:'Circuito da risolvere'}).isVisible())await page.getByText('Vista esperta: testo del circuito',{exact:true}).click();
  await expect(page.getByRole('textbox',{name:'Circuito da risolvere'})).toHaveValue(newNetlist);
  release();
  await expect(page.getByText('Puoi risolvere circuiti nuovi: il server locale è collegato.')).toBeAttached();
  await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeEnabled();
  expect(solves).toEqual([]);
  await page.getByRole('button',{name:/Risolvi e spiega/}).click();
  await expect(page.getByRole('heading',{name:'Leggiamo il circuito e la domanda'})).toBeVisible();
  expect(solves).toEqual([newNetlist]);
  await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toHaveCount(0);
 }finally{release();}
});
