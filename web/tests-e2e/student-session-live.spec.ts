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

test('un valore ricavato con KCL riceve un controllo numerico locale senza giudicare il metodo',async({page})=>{
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
});
