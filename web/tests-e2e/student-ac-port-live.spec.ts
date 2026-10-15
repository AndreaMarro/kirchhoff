import {expect,test} from '@playwright/test';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

const base=process.env.KIRCHHOFF_LIVE_BASE_URL;
const root=resolve(process.cwd(),'..');
const output=resolve(root,'../evidence-20261003/ac-port-browser');
const circuit='@ac 2 rad/s\n@amplitude unspecified\nR1 a b 3 ohm\nL1 b 0 2 henry\n? impedance a 0';
test.skip(!base,'Richiede il server Kirchhoff reale.');

test('impedenza AC da componenti: algebra, PDF e quaderno riaperto',async({page,browser},info)=>{
 await page.goto(base!);
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.getByRole('button',{name:'Componenti e collegamenti',exact:true}).click();
 const remove=page.getByRole('button',{name:/^Rimuovi [RVILC]/});
 while(await remove.count())await remove.first().click();
 await page.getByRole('combobox',{name:'Regime del circuito'}).selectOption('ac');
 await page.getByRole('textbox',{name:'Pulsazione rad/s'}).fill('2');
 for(const [kind,id,value,from,to] of [['resistore','R1','3','a','b'],['induttore','L1','2','b','0']]){
  await page.getByRole('button',{name:`Aggiungi ${kind}`,exact:true}).click();
  await page.getByLabel(`Valore ${id}`,{exact:true}).fill(value);
  await page.getByLabel(`Primo morsetto ${id}`,{exact:true}).fill(from);
  await page.getByLabel(`Secondo morsetto ${id}`,{exact:true}).fill(to);
 }
 await page.getByRole('combobox',{name:'Grandezza da trovare'}).selectOption('impedance');
 await page.getByRole('combobox',{name:'Primo morsetto della porta',exact:true}).selectOption('a');
 await page.getByRole('combobox',{name:'Secondo morsetto della porta',exact:true}).selectOption('0');
 const confirmation=page.getByRole('checkbox',{name:/Ho confrontato/});
 if(await confirmation.isVisible())await confirmation.check();
 await expect(page.getByRole('textbox',{name:'Circuito da risolvere'})).not.toBeVisible();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeEnabled();
 const solved=page.waitForResponse(r=>r.url().endsWith('/api/solve')&&r.request().method()==='POST');
 await page.getByRole('button',{name:/Risolvi e spiega/}).click();
 const response=await solved;expect(response.status()).toBe(200);
 const lesson=await response.json();
 expect(lesson.answer.exact).toBe('(3) + j*(4)');
 expect(lesson.answer.quantity).toBe('equivalent_impedance');
 expect(lesson.answer).not.toHaveProperty('phasor');
 expect(lesson.conventions.amplitude).toBe('unspecified');
 expect(lesson.conventions.power_calculated).toBe(false);
 expect(lesson.verification.product_verified).toBe(false);
 await expect(page.getByRole('dialog')).toBeHidden();
 await expect(page.getByRole('button',{name:'Scarica SPICE ↓'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Scarica CircuitikZ ↓'})).toBeDisabled();
 await expect(page.getByText(/Il tuo procedimento/)).not.toBeVisible();
 for(let index=0;index<lesson.steps.length-1;index++)await page.getByRole('button',{name:'Passo successivo'}).click();
 await expect(page.locator('.student-result')).toContainText('Z =');
 await expect(page.locator('.student-result math')).toBeVisible();
 await page.getByText('Controllo del risultato e provenienza').click();
 await expect(page.getByText(/L’impedenza di porta coincide/)).toBeVisible();
 await mkdir(output,{recursive:true});
 const prefix=resolve(output,info.project.name);
 await writeFile(`${prefix}-lesson.json`,JSON.stringify(lesson,null,2)+'\n');
 const pdf=page.waitForEvent('download');await page.getByRole('button',{name:'Scarica PDF ↓'}).click();
 await (await pdf).saveAs(`${prefix}-lesson.pdf`);
 const notebook=page.waitForEvent('download');await page.getByRole('button',{name:'Salva quaderno ↓'}).click();
 const bytes=await readFile(await (await notebook).path());
 expect(JSON.parse(bytes.toString()).answerExact).toBe(lesson.answer.exact);
 await writeFile(`${prefix}-quaderno.json`,bytes);
 const fresh=await browser.newContext();
 try{
  const reopened=await fresh.newPage();await reopened.goto(base!);
  await reopened.locator('input[type=file][accept*="application/json"]').setInputFiles({name:'impedenza.json',mimeType:'application/json',buffer:bytes});
  await expect(reopened.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
  await expect(reopened.locator('.student-result')).toContainText('Z =');
  await expect(reopened.locator('.student-result math')).toBeVisible();
  await expect(reopened.getByRole('button',{name:'Scarica SPICE ↓'})).toBeDisabled();
  await reopened.locator('.student-result').scrollIntoViewIfNeeded();
  await reopened.screenshot({path:`${prefix}-restored.png`,fullPage:false});
 }finally{await fresh.close();}
});

test('impedenza AC nella MCP App con SDK reale e host locale di prova',async({page},info)=>{
 const python=resolve(root,'.venv/bin/python');
 const html=execFileSync(python,['-c','from kirchhoff.api.mcp_server import app_html; print(app_html())'],{cwd:root,encoding:'utf8'});
 await page.exposeFunction('callKirchhoffPort',async(params:{name:string;arguments?:unknown})=>{
  const code='import asyncio,json,sys\nfrom mcp import Client\nfrom kirchhoff.api.mcp_server import build_server\nasync def run():\n async with Client(build_server()) as client:\n  params=json.loads(sys.argv[1]); result=await client.call_tool(params["name"],params.get("arguments",{})); print(json.dumps(result.model_dump(by_alias=True,exclude_none=True)))\nasyncio.run(run())';
  return JSON.parse(execFileSync(python,['-c',code,JSON.stringify(params)],{cwd:root,encoding:'utf8'}));
 });
 await page.goto(base!);
 await page.setContent('<title>Impedenza AC — host MCP locale di prova</title><iframe title="Kirchhoff MCP App" style="width:100%;height:1100px;border:0"></iframe>');
 await page.evaluate(({html})=>{
  const frame=document.querySelector('iframe')!;
  window.addEventListener('message',async event=>{
   if(event.source!==frame.contentWindow)return;
   const message=event.data;if(message?.jsonrpc!=='2.0'||message.id===undefined)return;
   let result;
   if(message.method==='ui/initialize')result={protocolVersion:message.params.protocolVersion,hostInfo:{name:'Host locale di prova',version:'1.0.0'},hostCapabilities:{serverTools:{}},hostContext:{theme:'light',displayMode:'inline'}};
   else if(message.method==='tools/call')result=await (window as unknown as {callKirchhoffPort:(params:unknown)=>Promise<unknown>}).callKirchhoffPort(message.params);
   else result={};
   frame.contentWindow!.postMessage({jsonrpc:'2.0',id:message.id,result},'*');
  });frame.srcdoc=html;
 },{html});
 const app=page.frameLocator('iframe');
 await expect(app.locator('#status')).toContainText('Host collegato');
 await app.getByRole('textbox',{name:'Circuito confermato e domanda'}).fill(circuit);
 await app.getByRole('button',{name:'Verifica e spiega'}).click();
 await expect(app.locator('#status')).toContainText('L’impedenza di porta coincide');
 for(let index=0;index<64&&await app.getByRole('button',{name:'Dopo →'}).isEnabled();index++)await app.getByRole('button',{name:'Dopo →'}).click();
 await expect(app.locator('#answer')).toContainText('Z =');
 await expect(app.locator('#answer')).toContainText('Ω');
 await expect(app.locator('#answer math')).toBeVisible();
 await mkdir(output,{recursive:true});await app.locator('#answer').scrollIntoViewIfNeeded();
 await page.screenshot({path:resolve(output,`mcp-${info.project.name}.png`),fullPage:false});
});
