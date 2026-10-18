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

test('la KVL della maglia arriva al controllo con nodo e versi strutturati',async({page})=>{
 const lesson=await readFile(new URL('../public/lessons/partitore-d1-auto.json',import.meta.url),'utf8');
 let received:unknown;
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:false}}));
 await page.route('**/api/solve',route=>route.fulfill({body:lesson,contentType:'application/json'}));
 await page.route('**/api/diagnose',async route=>{
  received=route.request().postDataJSON();
  await route.fulfill({json:{schema:"student-diagnosis.v1",engine_revision:"a".repeat(40),outcome:'valid_so_far',step:null,category:null,message:'Maglia verificata.',focus:[],circuit_fingerprint:bundle.circuitFingerprint}});
 });
 await page.goto('/');
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
 await page.getByRole('combobox',{name:'Operazione passaggio 1'}).selectOption('kvl');
 await page.getByRole('textbox',{name:'Primo componente passaggio 1'}).fill('b');
 await page.getByRole('textbox',{name:'Secondo componente passaggio 1'}).fill('+R1,+R2,-V1');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result').getByText('Maglia verificata.')).toBeVisible();
 expect((received as {trace:{steps:{operation:string;first:string;second:string}[]}}).trace.steps[0]).toMatchObject({operation:'kvl',first:'b',second:'+R1,+R2,-V1'});
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


test('modificare un passaggio in attesa permette un nuovo controllo senza esiti superati',async({page})=>{
 const lesson=await readFile(new URL('../public/lessons/partitore-d1-auto.json',import.meta.url),'utf8');
 let calls=0;
 let releaseOld!:()=>void,releaseNew!:()=>void;
 const oldGate=new Promise<void>(resolve=>{releaseOld=resolve;});
 const newGate=new Promise<void>(resolve=>{releaseNew=resolve;});
 const bodies:Array<{trace:{steps:{transcription:string}[]}}>=[];
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:false}}));
 await page.route('**/api/solve',route=>route.fulfill({body:lesson,contentType:'application/json'}));
 await page.route('**/api/diagnose',async route=>{
  bodies.push(route.request().postDataJSON());
  const n=++calls;
  await (n===1?oldGate:newGate);
  await route.fulfill({json:{schema:"student-diagnosis.v1",engine_revision:"a".repeat(40),outcome:'valid_so_far',step:null,category:null,
   message:n===1?'Esito precedente da ignorare.':'Esito del passaggio modificato.',
   focus:[],circuit_fingerprint:bundle.circuitFingerprint}});
 });
 try{
  await page.goto('/');
  await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
  await expect(page.getByRole('textbox',{name:'Testo passaggio 1'})).toHaveValue('R1+R2=320');
  await page.getByRole('button',{name:'Controlla i passaggi'}).click();
  await expect.poll(()=>calls).toBe(1);
  await expect(page.getByRole('button',{name:'Controllo…'})).toBeDisabled();
  await page.getByRole('textbox',{name:'Testo passaggio 1'}).fill('R1 e R2 sommano 320 ohm');
  await expect(page.getByRole('button',{name:'Controlla i passaggi'})).toBeEnabled();
  await expect(page.getByRole('button',{name:'Aggiungi passaggio'})).toBeEnabled();
  await page.getByRole('button',{name:'Controlla i passaggi'}).click();
  await expect.poll(()=>calls).toBe(2);
  expect(bodies[1].trace.steps[0].transcription).toBe('R1 e R2 sommano 320 ohm');
  const oldDone=page.waitForResponse(response=>response.url().endsWith('/api/diagnose')&&response.request().postDataJSON().trace.steps[0].transcription==='R1+R2=320');
  releaseOld();await (await oldDone).finished();
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  await expect(page.getByRole('button',{name:'Controllo…'})).toBeDisabled();
  await expect(page.locator('.student-trace-result')).toHaveCount(0);
  releaseNew();
  await expect(page.locator('.student-trace-result')).toContainText('Esito del passaggio modificato.');
  await expect(page.locator('.student-trace-result')).not.toContainText('Esito precedente');
  await expect(page.getByRole('button',{name:'Controlla i passaggi'})).toBeEnabled();
 }finally{releaseOld();releaseNew();await page.unrouteAll({behavior:'wait'});}
});

test('prima del salvataggio il quaderno dichiara la fonte originale realmente inclusa',async({page})=>{
 const lesson=await readFile(new URL('../public/lessons/partitore-d1-auto.json',import.meta.url),'utf8');
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:false}}));
 await page.route('**/api/solve',route=>route.fulfill({body:lesson,contentType:'application/json'}));
 await page.goto('/');
 const input=page.locator('input[type=file][accept*="application/json"]');
 await input.setInputFiles({name:'testo.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
 await expect(page.getByRole('textbox',{name:'Testo passaggio 1'})).toHaveValue('R1+R2=320');
 const save=page.getByRole('button',{name:'Salva quaderno ↓'});
 await expect(save).not.toHaveAccessibleDescription(/file originale|immagine della fonte/);
 const plainDownload=page.waitForEvent('download');await save.click();
 const plain=JSON.parse(await readFile(await (await plainDownload).path(),'utf8'));
 expect(plain.sourceArtifact??null).toBeNull();
 const bytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC','base64');
 const sha256=createHash('sha256').update(bytes).digest('hex');
 const dataURL='data:image/png;base64,'+bytes.toString('base64');
 const sourceArtifact={schema:'kirchhoff-source.v1',kind:'image',
  original:{name:'fonte-di-prova.png',mediaType:'image/png',dataURL,sha256},prepared:{dataURL,sha256}};
 const withSource={...bundle,schema:'kirchhoff-portable-session.v2',priorImageSha256:sha256,sourceArtifact};
 await input.setInputFiles({name:'con-fonte.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(withSource))});
 await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata con la fonte conservata/)).toBeVisible();
 await expect(save).toHaveAccessibleDescription(/file originale.*fonte-di-prova\.png.*immagine della fonte/i);
 const sourceDownload=page.waitForEvent('download');await save.click();
 const saved=JSON.parse(await readFile(await (await sourceDownload).path(),'utf8'));
 expect(saved.sourceArtifact.original.name).toBe('fonte-di-prova.png');
 expect(Buffer.from(saved.sourceArtifact.original.dataURL.split(',')[1],'base64')).toEqual(bytes);
 expect(saved.sourceArtifact.prepared.dataURL).toBe(dataURL);
});
