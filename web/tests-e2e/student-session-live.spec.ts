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
