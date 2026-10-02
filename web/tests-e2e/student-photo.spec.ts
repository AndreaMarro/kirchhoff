import {expect,test} from '@playwright/test';

const image=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==','base64');

test('una modifica semantica dopo la conferma della foto invalida il consenso',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'sorgente.png',mimeType:'image/png',buffer:image});
 const circuit=page.getByRole('textbox',{name:'Circuito da risolvere'});
 await circuit.fill('V1 a 0 12 volt\nR1 a 0 100 ohm\n? voltage R1');
 const confirmation=page.getByRole('checkbox',{name:/Ho confrontato/});
 await confirmation.check();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeEnabled();
 await circuit.fill('V1 a 0 12 volt\nR1 a 0 200 ohm\n? voltage R1');
 await expect(confirmation).not.toBeChecked();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
});

test('la foto mostra la provenienza delle righe e perde le regioni quando il circuito cambia',async({page})=>{
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:true}}));
 const netlist='V1 a 0 12 volt\nR1 a 0 6 ohm\n? current R1';
 await page.route('**/api/recognize',route=>route.fulfill({json:{
  netlist,requires_confirmation:true,model_reported_complete:false,
  uncertainties:['Un quarto simbolo al bordo è tagliato.'],
  observations:netlist.split('\n').map((line,i)=>({line,region:{x1:100+i*100,y1:100,x2:200+i*100,y2:300}})),
  candidates:[
   {netlist,observations:netlist.split('\n').map((line,i)=>({line,region:{x1:100+i*100,y1:100,x2:200+i*100,y2:300}})),uncertainties:[],model_reported_complete:true},
   {netlist:netlist.replace('6 ohm','7 ohm'),observations:netlist.replace('6 ohm','7 ohm').split('\n').map((line,i)=>({line,region:{x1:100+i*100,y1:100,x2:200+i*100,y2:300}})),uncertainties:[],model_reported_complete:true},
  ],
 }}));
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'esame.png',mimeType:'image/png',buffer:image});
 await page.getByRole('button',{name:/Invia a OpenAI/}).click();
 await expect(page.getByRole('region',{name:'Origine delle righe lette'})).toBeVisible();
 await expect(page.getByText(/La lettura è incompleta o discordante/)).toBeVisible();
 await expect(page.getByRole('checkbox',{name:/Ho confrontato/})).toBeDisabled();
 await page.getByRole('button',{name:'Lettura 2'}).click();
 await expect(page.getByRole('textbox',{name:'Circuito da risolvere'})).toHaveValue(netlist.replace('6 ohm','7 ohm'));
 await page.getByRole('button',{name:'Lettura 1'}).click();
 await page.getByRole('button',{name:'R1 a 0 6 ohm'}).click();
 await expect(page.locator('[data-source-region="1"]')).toHaveAttribute('style',/left: 20%/);
 await page.getByRole('textbox',{name:'Circuito da risolvere'}).fill(netlist.replace('6 ohm','7 ohm'));
 await expect(page.getByRole('region',{name:'Origine delle righe lette'})).toHaveCount(0);
 await expect(page.getByRole('checkbox',{name:/Ho confrontato/})).not.toBeChecked();
 await expect(page.getByRole('checkbox',{name:/Ho confrontato/})).toBeEnabled();
});

test('zone fotografiche discordanti restano confrontabili anche con testo identico',async({page})=>{
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:true}}));
 const netlist='V1 a 0 12 volt\nR1 a 0 6 ohm\n? current R1';
 const first=netlist.split('\n').map((line,i)=>({line,region:{x1:100+i*100,y1:100,x2:200+i*100,y2:300}}));
 const second=first.map((item,i)=>i===1?{...item,region:{...item.region,x1:400,x2:500}}:item);
 await page.route('**/api/recognize',route=>route.fulfill({json:{
  netlist,requires_confirmation:true,model_reported_complete:false,
  uncertainties:['Le letture divergono sulle regioni di origine.'],observations:first,
  candidates:[
   {netlist,observations:first,uncertainties:[],model_reported_complete:true},
   {netlist,observations:second,uncertainties:[],model_reported_complete:true},
  ],
 }}));
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'esame.png',mimeType:'image/png',buffer:image});
 await page.getByRole('button',{name:/Invia a OpenAI/}).click();
 await expect(page.getByText(/concordano sul testo ma indicano zone diverse/)).toBeVisible();
 await page.getByRole('button',{name:'R1 a 0 6 ohm'}).click();
 await expect(page.locator('[data-source-region="1"]')).toHaveAttribute('style',/left: 20%/);
 await expect(page.locator('[data-source-region="1"]')).toHaveAttribute('style',/width: 10%/);
 await page.getByRole('button',{name:'Lettura 2'}).click();
 await page.getByRole('button',{name:'R1 a 0 6 ohm'}).click();
 await expect(page.locator('[data-source-region="1"]')).toHaveAttribute('style',/left: 40%/);
 await expect(page.locator('[data-source-region="1"]')).toHaveAttribute('style',/width: 10%/);
});

test('una trascrizione senza stato di completezza non abilita il calcolo',async({page})=>{
 await page.route('**/api/capabilities',route=>route.fulfill({json:{solve:true,vision:true}}));
 await page.route('**/api/recognize',route=>route.fulfill({json:{netlist:'V1 a 0 12 volt\nR1 a 0 6 ohm\n? current R1',observations:[],uncertainties:[]}}));
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file][accept*="image/png"]').setInputFiles({name:'esame.png',mimeType:'image/png',buffer:image});
 await page.getByRole('button',{name:/Invia a OpenAI/}).click();
 await expect(page.getByRole('dialog',{name:'Partiamo dal tuo circuito'}).getByRole('alert')).toContainText('Trascrizione non interpretabile');
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
});
