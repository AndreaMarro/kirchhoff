import {expect,test} from '@playwright/test';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
const root=resolve(process.cwd(),'..');
const circuit='@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 3 farad\n@initial C1 voltage 4 volt\n? voltage C1';
const output=resolve(process.cwd(),'../../evidence-20261003/laplace-browser');
test.skip(!base,'Richiede il server Kirchhoff reale.');
const cases=[
 {id:'rc-step',waveform:'step',source:'10',initial:'4',target:'C1',quantity:'voltage',numerator:['5/3','4'],denominator:['0','1/6','1']},
 {id:'rc-impulse',waveform:'impulse',source:'3',initial:'0',target:'C1',quantity:'voltage',numerator:['1/2'],denominator:['1/6','1']},
 {id:'rl-free',waveform:null,source:null,initial:'-2',target:'L1',quantity:'current',numerator:['-2'],denominator:['3/2','1']},
] as const;

for(const scenario of cases)test(`${scenario.id}: componenti, stato iniziale, algebra, PDF e quaderno riaperto`,async({page,browser},info)=>{
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Componenti e collegamenti',exact:true}).click();
 const remove=page.getByRole('button',{name:/^Rimuovi [RVILC]/});
 while(await remove.count())await remove.first().click();
 await page.getByRole('combobox',{name:'Regime del circuito'}).selectOption('laplace');
 const rows=scenario.waveform ? [
  ['generatore di tensione','V1',scenario.source,'e','0'],['resistore','R1','2','e','a'],['condensatore','C1','3','a','0'],
 ] : [['resistore','R1','3','a','0'],['induttore','L1','2','a','0']];
 for(const [kind,id,value,from,to] of rows){
  await page.getByRole('button',{name:`Aggiungi ${kind}`,exact:true}).click();
  await page.getByLabel(`Valore ${id}`,{exact:true}).fill(value);
  await page.getByLabel(`Primo morsetto ${id}`,{exact:true}).fill(from);
  await page.getByLabel(`Secondo morsetto ${id}`,{exact:true}).fill(to);
 }
 if(scenario.waveform){
  await page.getByRole('combobox',{name:'Forma sorgente V1'}).selectOption(scenario.waveform);
  if(scenario.waveform==='impulse')await expect(page.getByText('Area dell’impulso (volt*s)',{exact:true})).toBeVisible();
 }
 await page.getByRole('combobox',{name:'Grandezza da trovare'}).selectOption(scenario.quantity);
 await page.getByRole('combobox',{name:'Componente della domanda'}).selectOption(scenario.target);
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
 await page.getByLabel(`Stato iniziale ${scenario.target}`,{exact:true}).fill(scenario.initial);
 await expect(page.getByRole('textbox',{name:'Circuito da risolvere'})).not.toBeVisible();
 const solved=page.waitForResponse(r=>r.url().endsWith('/api/solve')&&r.request().method()==='POST');
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 const response=await solved;expect(response.status()).toBe(200);
 const lesson=await response.json();
 expect(lesson.answer.laplace_transform).toMatchObject({variable:'s',coefficient_order:'ascending',numerator:scenario.numerator,denominator:scenario.denominator});
 expect(lesson.answer.unit).toBe(scenario.quantity==='voltage'?'V*s':'A*s');
 expect(lesson.verification.product_verified).toBe(false);
 expect(lesson.conventions.domain).toBe('laplace');
 await expect(page.getByRole('dialog')).toBeHidden();
 await expect(page.getByRole('button',{name:'Scarica SPICE ↓'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Scarica CircuitikZ ↓'})).toBeDisabled();
 await expect(page.getByText('Il tuo procedimento',{exact:true})).not.toBeVisible();
 for(let index=0;index<lesson.steps.length;index++){
  if(lesson.steps[index].math?.length)await expect(page.locator('.student-equations math').first()).toBeVisible();
  if(index<lesson.steps.length-1)await page.getByRole('button',{name:'Passo successivo'}).click();
 }
 await expect(page.locator('.student-result math mfrac').first()).toBeVisible();
 await expect(page.locator('.student-result')).toContainText(scenario.quantity==='voltage'?'V(s) =':'I(s) =');
 await expect(page.locator('.student-result')).not.toContainText('≈');
 await mkdir(output,{recursive:true});const prefix=resolve(output,`${scenario.id}-${info.project.name}`);
 await writeFile(`${prefix}-lesson.json`,JSON.stringify(lesson,null,2)+'\n');
 const pdf=page.waitForEvent('download');await page.getByRole('button',{name:'Scarica PDF ↓'}).click();
 await(await pdf).saveAs(`${prefix}-lesson.pdf`);
 const save=page.waitForEvent('download');await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const bytes=await readFile(await(await save).path());await writeFile(`${prefix}-quaderno.json`,bytes);
 expect(JSON.parse(bytes.toString()).answerExact).toBe(lesson.answer.exact);
 const fresh=await browser.newContext();
 try{
  const reopened=await fresh.newPage();await reopened.goto(base!);
  await reopened.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'laplace.json',mimeType:'application/json',buffer:bytes});
  await expect(reopened.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
  await expect(reopened.locator('.student-result math')).toBeVisible();
  await expect(reopened.locator('.student-result')).not.toContainText('≈');
  await reopened.locator('.student-result').scrollIntoViewIfNeeded();
  await reopened.screenshot({path:`${prefix}-restored.png`,fullPage:false});
 }finally{await fresh.close();}
});

test('Laplace nella MCP App con SDK reale e host locale di prova',async({page},info)=>{
 const python=resolve(root,'.venv/bin/python');
 const html=execFileSync(python,['-c','from kirchhoff.api.mcp_server import app_html; print(app_html())'],{cwd:root,encoding:'utf8'});
 await page.exposeFunction('callKirchhoffLaplace',async(params:{name:string;arguments?:unknown})=>{
  const code='import asyncio,json,sys\nfrom mcp import Client\nfrom kirchhoff.api.mcp_server import build_server\nasync def run():\n async with Client(build_server()) as client:\n  params=json.loads(sys.argv[1]); result=await client.call_tool(params["name"],params.get("arguments",{})); print(json.dumps(result.model_dump(by_alias=True,exclude_none=True)))\nasyncio.run(run())';
  return JSON.parse(execFileSync(python,['-c',code,JSON.stringify(params)],{cwd:root,encoding:'utf8'}));
 });
 await page.goto(base!);
 await page.setContent('<title>Laplace — host MCP locale di prova</title><iframe title="Kirchhoff MCP App" style="width:100%;height:1100px;border:0"></iframe>');
 await page.evaluate(({html})=>{
  const frame=document.querySelector('iframe')!;
  window.addEventListener('message',async event=>{
   if(event.source!==frame.contentWindow)return;
   const message=event.data;if(message?.jsonrpc!=='2.0'||message.id===undefined)return;
   let result;
   if(message.method==='ui/initialize')result={protocolVersion:message.params.protocolVersion,hostInfo:{name:'Host locale di prova',version:'1.0.0'},hostCapabilities:{serverTools:{}},hostContext:{theme:'light',displayMode:'inline'}};
   else if(message.method==='tools/call')result=await (window as unknown as {callKirchhoffLaplace:(params:unknown)=>Promise<unknown>}).callKirchhoffLaplace(message.params);
   else result={};
   frame.contentWindow!.postMessage({jsonrpc:'2.0',id:message.id,result},'*');
  });frame.srcdoc=html;
 },{html});
 const app=page.frameLocator('iframe');
 await expect(app.locator('#status')).toContainText('Host collegato');
 await app.getByRole('textbox',{name:'Circuito confermato e domanda'}).fill(circuit);
 await app.getByRole('button',{name:'Verifica e spiega'}).click();
 await expect(app.locator('#status')).toContainText('Le trasformate e i passaggi algebrici');
 for(let index=0;index<64&&await app.getByRole('button',{name:'Dopo →'}).isEnabled();index++)await app.getByRole('button',{name:'Dopo →'}).click();
 await expect(app.locator('#answer')).toContainText('V(s) =');
 await expect(app.locator('#answer')).toContainText('V*s');
 await expect(app.locator('#answer math')).toBeVisible();
 await expect(app.locator('#answer')).not.toContainText('≈');
 await mkdir(output,{recursive:true});await app.locator('#answer').scrollIntoViewIfNeeded();
 await page.screenshot({path:resolve(output,`mcp-${info.project.name}.png`),fullPage:false});
});
