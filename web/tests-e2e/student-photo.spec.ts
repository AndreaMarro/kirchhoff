import {expect,test} from '@playwright/test';

const image=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==','base64');

test('una modifica semantica dopo la conferma della foto invalida il consenso',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:/Il tuo circuito/}).click();
 await page.locator('input[type=file]').setInputFiles({name:'sorgente.png',mimeType:'image/png',buffer:image});
 const circuit=page.getByRole('textbox',{name:'Circuito da risolvere'});
 await circuit.fill('V1 a 0 12 volt\nR1 a 0 100 ohm\n? voltage R1');
 const confirmation=page.getByRole('checkbox',{name:/Ho confrontato/});
 await confirmation.check();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeEnabled();
 await circuit.fill('V1 a 0 12 volt\nR1 a 0 200 ohm\n? voltage R1');
 await expect(confirmation).not.toBeChecked();
 await expect(page.getByRole('button',{name:/Risolvi e spiega/})).toBeDisabled();
});
