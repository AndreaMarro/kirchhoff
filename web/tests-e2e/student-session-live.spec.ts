import {expect,test} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
test.skip(!base,'Avvia il server locale e imposta KIRCHHOFF_LIVE_BASE_URL per il gate reale.');

test('un quaderno non catalogato si riapre attraverso il server e si salva di nuovo',async({page})=>{
 const netlist='V1 p 0 14 volt\nR1 p q 4 ohm\nR2 q 0 6 ohm\n? voltage R2';
 const bundle={schema:'kirchhoff-portable-session.v1',netlist,method:'auto',
  circuitFingerprint:createHash('sha256').update(netlist).digest('hex'),answerExact:'42/5',engineRevision:'precedente',
  selectedStep:1,showOriginal:false,boardScene:'',traceSteps:[{transcription:'R1+R2=10',operation:'serie',first:'R1',second:'R2',claimed_value:'10',reading:'clear'}],priorImageSha256:null};
 await page.goto(base!);
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
 await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata dal circuito salvato/)).toBeVisible();
 await expect(page.getByRole('textbox',{name:'Testo passaggio 1'})).toHaveValue('R1+R2=10');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8'));
 expect(saved.netlist).toBe(netlist);
 expect(saved.method).toBe('auto');
 expect(saved.answerExact).toBe('42/5');
});

test('un ritaglio reale della lavagna conserva i tratti scelti nel quaderno dopo riapertura',async({page})=>{
 const netlist='V1 p 0 12 volt\nR1 p 0 6 ohm\n? current R1';
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Lavagna libera'}).click();
 const board=page.frameLocator('iframe[title="Lavagna libera Excalidraw"]');
 await board.locator('label:has(input[aria-label="Disegno"])').click();
 const canvas=board.locator('canvas').first();
 const box=await canvas.boundingBox();
 expect(box).not.toBeNull();
 await page.mouse.move(box!.x+box!.width/2-50,box!.y+box!.height/2);
 await page.mouse.down();
 await page.mouse.move(box!.x+box!.width/2+50,box!.y+box!.height/2,{steps:12});
 await page.mouse.up();
 await board.getByRole('button',{name:'Usa tutto il disegno →'}).click();
 await expect(page.getByText(/Ritaglio dalla lavagna: 1 tratto del disegno intero/)).toBeVisible();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist);
 await page.getByRole('checkbox',{name:/Ho confrontato con la foto/}).check();
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8')) as {
  boardScene:string;boardSource:{sceneSha256:string;selectedElementIds:string[];selectionOnly:boolean};priorImageSha256:string;
 };
 expect(saved.boardSource.selectedElementIds).toHaveLength(1);
 expect(saved.boardSource.selectionOnly).toBe(false);
 expect(saved.boardSource.sceneSha256).toBe(createHash('sha256').update(saved.boardScene).digest('hex'));
 expect(saved.priorImageSha256).toMatch(/^[a-f0-9]{64}$/);
 await page.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});
 await expect(page.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
 await page.getByText('Controllo del risultato e provenienza').click();
 await expect(page.getByText(/Ritaglio della lavagna: 1 tratto del disegno intero/)).toBeVisible();
 const secondDownload=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const reopened=JSON.parse(await readFile(await (await secondDownload).path(),'utf8')) as typeof saved;
 expect(reopened.boardSource).toEqual(saved.boardSource);
 expect(reopened.priorImageSha256).toBe(saved.priorImageSha256);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Lavagna libera'}).click();
 await page.frameLocator('iframe[title="Lavagna libera Excalidraw"]').getByRole('button',{name:'Salva disegno'}).waitFor();
 await page.getByRole('button',{name:'Chiudi ingresso circuito'}).click();
 const thirdDownload=page.waitForEvent('download',{timeout:5000});
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const viewed=JSON.parse(await readFile(await (await thirdDownload).path(),'utf8')) as typeof saved;
 expect(viewed.boardSource).toEqual(saved.boardSource);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Lavagna libera'}).click();
 const restoredBoard=page.frameLocator('iframe[title="Lavagna libera Excalidraw"]');
 await restoredBoard.locator('label:has(input[aria-label="Disegno"])').click();
 const restoredBox=await restoredBoard.locator('canvas').first().boundingBox();
 expect(restoredBox).not.toBeNull();
 await page.mouse.move(restoredBox!.x+restoredBox!.width/2-50,restoredBox!.y+restoredBox!.height/2+70);
 await page.mouse.down();
 await page.mouse.move(restoredBox!.x+restoredBox!.width/2+50,restoredBox!.y+restoredBox!.height/2+70,{steps:12});
 await page.mouse.up();
 await page.getByRole('button',{name:'Chiudi ingresso circuito'}).click();
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 await expect(page.getByRole('alert')).toContainText('La lavagna è cambiata dopo il ritaglio');
});

test('la selezione reale esporta un solo tratto e conserva il resto della scena',async({page})=>{
 const netlist='V1 p 0 12 volt\nR1 p 0 6 ohm\n? current R1';
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Lavagna libera'}).click();
 const board=page.frameLocator('iframe[title="Lavagna libera Excalidraw"]');
 await board.locator('label:has(input[aria-label="Disegno"])').click();
 const box=await board.locator('canvas').first().boundingBox();
 expect(box).not.toBeNull();
 const cx=box!.x+box!.width/2,cy=box!.y+box!.height/2;
 for(const y of [cy-45,cy+45]){
  await page.mouse.move(cx-50,y);await page.mouse.down();
  await page.mouse.move(cx+50,y,{steps:12});await page.mouse.up();
 }
 await board.locator('label:has(input[aria-label="Selezione"])').click();
 await page.mouse.click(cx,cy-45);
 await board.getByRole('button',{name:'Usa selezione →'}).click();
 await expect(page.getByText(/Ritaglio dalla lavagna: 1 tratto selezionato/)).toBeVisible();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist);
 await page.getByRole('checkbox',{name:/Ho confrontato con la foto/}).check();
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8')) as {
  boardScene:string;boardSource:{sceneSha256:string;selectedElementIds:string[];selectionOnly:boolean};
 };
 expect(saved.boardSource.selectionOnly).toBe(true);
 expect(saved.boardSource.selectedElementIds).toHaveLength(1);
 expect((JSON.parse(saved.boardScene) as {elements:unknown[]}).elements).toHaveLength(2);
 expect(saved.boardSource.sceneSha256).toBe(createHash('sha256').update(saved.boardScene).digest('hex'));
});

test('due sorgenti: la lezione servita mostra la differenza di tensione reale',async({page})=>{
 const netlist='V1 a 0 10 volt\nR1 a b 2 ohm\nV2 b 0 4 volt\n? current R1';
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist);
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.locator('.student-route-method')).toContainText('Millman');
 await page.getByRole('button',{name:/La tensione è già imposta/}).click();
 await expect(page.locator('.student-equations')).toContainText('(10 - (4)) / (2) = 3 A');
 await expect(page.locator('.student-equations')).not.toContainText('(10) / (2) = 3 A');
});

test('il perimetro visibile coincide con quello dichiarato dal server',async({page})=>{
 const declared=await fetch(`${base}/api/capabilities`).then(r=>r.json()) as {scope:string;controlled_sources:boolean;ac:boolean;transients:boolean};
 expect(declared.controlled_sources).toBe(false);
 expect(declared.ac).toBe(false);
 expect(declared.transients).toBe(false);
 await page.goto(base!);
 await page.getByText('Cosa puoi risolvere in questa versione').click();
 await expect(page.locator('.student-scope').first()).toContainText(declared.scope);
});

test('un valore e una KCL dello studente sono controllati fino al primo errore',async({page})=>{
 const netlist='V1 a 0 12 volt\nR1 a b 100 ohm\nR2 b 0 200 ohm\nR3 b 0 300 ohm\n? current R2';
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist);
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.getByRole('dialog')).toBeHidden();
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
 await page.getByRole('textbox',{name:'Testo passaggio 1'}).fill('KCL al nodo b: I_R2 = 9/275 A');
 await page.getByRole('combobox',{name:'Operazione passaggio 1'}).selectOption('corrente');
 await page.getByRole('textbox',{name:'Primo componente passaggio 1'}).fill('R2');
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill('9/275');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('Passaggi controllati validi fin qui');
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill('1/30');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('9/275 A, non 1/30 A');
 await expect(page.locator('.student-trace-result')).toContainText('metodo scritto non è giudicato');
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill('9/275');
 await page.getByRole('button',{name:'Aggiungi passaggio'}).click();
 await page.getByRole('combobox',{name:'Operazione passaggio 2'}).selectOption('kcl');
 await page.getByRole('textbox',{name:'Primo componente passaggio 2'}).fill('b');
 await page.getByRole('textbox',{name:'Secondo componente passaggio 2'}).fill('-R1,+R2');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('I passaggi fino al 1 sono validi');
 await expect(page.locator('.student-trace-result')).toContainText('non 0 A');
 await page.getByRole('textbox',{name:'Secondo componente passaggio 2'}).fill('-R1,+R2,+R3');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('Passaggi controllati validi fin qui');
});

test('il valore nel verso opposto dichiarato è controllato senza cambiare il circuito',async({page})=>{
 const netlist='V1 a 0 12 volt\nR1 a b 100 ohm\nR2 b 0 200 ohm\n? current R2';
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist);
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.getByRole('dialog')).toBeHidden();
 await page.getByRole('combobox',{name:'Operazione passaggio 1'}).selectOption('corrente');
 await page.getByRole('textbox',{name:'Primo componente passaggio 1'}).fill('R2');
 await page.getByRole('textbox',{name:'Verso passaggio 1'}).fill('0,b');
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill('-1/25');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('Passaggi controllati validi fin qui');
 await page.getByRole('textbox',{name:'Valore passaggio 1'}).fill('1/25');
 await page.getByRole('button',{name:'Controlla i passaggi'}).click();
 await expect(page.locator('.student-trace-result')).toContainText('0 → b: -1/25 A, non 1/25 A');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8'));
 expect(saved.traceSteps[0]).toMatchObject({operation:'corrente',first:'R2',second:'0,b',claimed_value:'1/25'});
});
