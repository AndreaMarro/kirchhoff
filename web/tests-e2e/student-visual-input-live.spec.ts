import {expect,test} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
test.skip(!base,'Richiede il vero server Kirchhoff locale.');
// A tiny image exercises the upload/byte contract; this is not an OCR or physical-pen acceptance.
const bytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==','base64');

test('foto, componenti modificabili, conferma e quaderno riaperto senza scrivere una netlist',async({page,browser})=>{
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'fonte.png',mimeType:'image/png',buffer:bytes});
 await page.getByRole('button',{name:'Aggiungi generatore di tensione',exact:true}).click();
 await page.getByRole('textbox',{name:'Valore V1',exact:true}).fill('12');
 await page.getByLabel('Primo morsetto V1',{exact:true}).fill('a');
 await page.getByLabel('Secondo morsetto V1',{exact:true}).fill('0');
 await page.getByRole('button',{name:'Aggiungi resistore',exact:true}).click();
 await page.getByRole('textbox',{name:'Valore R1',exact:true}).fill('6');
 await page.getByLabel('Primo morsetto R1',{exact:true}).fill('a');
 await page.getByLabel('Secondo morsetto R1',{exact:true}).fill('0');
 await page.getByRole('combobox',{name:'Grandezza da trovare',exact:true}).selectOption('current');
 await page.getByRole('combobox',{name:'Componente della domanda',exact:true}).selectOption('R1');
 const confirmation=page.getByRole('checkbox',{name:/Ho confrontato/});
 await confirmation.check();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeEnabled();
 await page.getByRole('textbox',{name:'Valore R1',exact:true}).fill('');
 await expect(confirmation).not.toBeChecked();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
 await page.getByRole('textbox',{name:'Valore R1',exact:true}).fill('6');
 await confirmation.check();
 await expect(page.getByRole('textbox',{name:'Circuito da risolvere',exact:true})).not.toBeVisible();
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
 await expect(page.getByRole('dialog')).toBeHidden();
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const saved=JSON.parse(await readFile(await (await download).path(),'utf8'));
 expect(saved.schema).toBe('kirchhoff-portable-session.v2');
 expect(saved.answerExact).toBe('2');
 expect(saved.sourceArtifact.original.sha256).toBe(createHash('sha256').update(bytes).digest('hex'));
 expect(Buffer.from(saved.sourceArtifact.original.dataURL.split(',')[1],'base64')).toEqual(bytes);
 expect(saved.sourceArtifact.prepared.sha256).toBe(saved.priorImageSha256);
 expect(saved).not.toHaveProperty('confirmation_token');
 // A pending source B must not replace the source A of the solved lesson.
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 const other=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=2;c.height=2;const ctx=c.getContext('2d')!;ctx.fillStyle='#123456';ctx.fillRect(0,0,2,2);return c.toDataURL('image/png');});
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'altra-fonte.png',mimeType:'image/png',buffer:Buffer.from(other.split(',')[1],'base64')});
 await expect(page.getByRole('img',{name:'Il circuito caricato da confrontare con la ricostruzione'})).toHaveAttribute('src',other);
 await page.getByRole('button',{name:'Chiudi ingresso circuito'}).click();
 await page.getByRole('combobox',{name:'Scegli il metodo'}).selectOption('nodal');
 await expect(page.locator('.student-lesson')).toHaveAttribute('aria-busy','false');
 const switched=page.waitForEvent('download');await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const changedMethod=JSON.parse(await readFile(await (await switched).path(),'utf8'));
 expect(changedMethod.sourceArtifact.original).toEqual(saved.sourceArtifact.original);

 const context=await browser.newContext();
 const reopened=await context.newPage();
 try{
  await reopened.goto(base!);
  await reopened.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'quaderno.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});
  await expect(reopened.getByText(/Quaderno riaperto e soluzione ricalcolata con la fonte conservata/)).toBeVisible();
  const second=reopened.waitForEvent('download');await reopened.getByRole('button',{name:'Salva quaderno ↓'}).click();
  const roundtrip=JSON.parse(await readFile(await (await second).path(),'utf8'));
  expect(roundtrip.sourceArtifact).toEqual(saved.sourceArtifact);
  await reopened.getByRole('button',{name:/Il tuo circuito/}).click();
  await expect(reopened.getByRole('img',{name:'Il circuito caricato da confrontare con la ricostruzione'})).toBeVisible();
  await expect(reopened.getByRole('checkbox',{name:/Ho confrontato/})).not.toBeChecked();
  await expect(reopened.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
 }finally{await context.close();}
});
