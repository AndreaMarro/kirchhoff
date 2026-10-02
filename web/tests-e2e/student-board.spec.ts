import { expect, test, type Page } from '@playwright/test';

async function node(page: Page, index: number) {
  await page.getByRole('button', { name: new RegExp(`^Nodo ${index}(?: |$)`) }).click();
}

async function drawCrossing(page: Page, connect: boolean) {
  await page.goto('/');
  await page.getByRole('button', { name: /Il tuo circuito/ }).click();
  await page.getByRole('button', { name: 'Schema a componenti' }).click();
  await page.getByRole('button', { name: 'Filo', exact: true }).click();
  for (const index of [4, 7, 1, 9]) await node(page, index);
  if (connect) {
    await page.getByRole('button', { name: 'Giunzione' }).click();
    await node(page, 5);
    await expect(page.getByRole('button', { name: /Nodo 5 giunzione/ })).toBeVisible();
  } else {
    await expect(page.getByLabel('Incrocio senza giunzione')).toBeVisible();
  }
  await page.getByRole('button', { name: 'Resistore' }).click();
  for (const index of [7, 11, 9, 8]) await node(page, index);
  await page.getByRole('button', { name: /Usa il circuito disegnato/ }).click();
  const text = await page.getByRole('textbox', { name: 'Circuito da risolvere' }).inputValue();
  const rows = text.split('\n').filter(line => line.startsWith('R'));
  return rows.map(row => row.split(' ')[1]);
}

test('la lavagna distingue un incrocio da una giunzione confermata', async ({ page }) => {
  const [first, second] = await drawCrossing(page, false);
  expect(first).not.toBe(second);
});

test('la giunzione della lavagna unisce i nodi esportati', async ({ page }) => {
  const [first, second] = await drawCrossing(page, true);
  expect(first).toBe(second);
});

test('la lavagna conserva la corrente e il componente richiesti', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Il tuo circuito/ }).click();
  await page.getByRole('button', { name: 'Schema a componenti' }).click();
  await page.getByRole('button', { name: 'Tensione', exact: true }).click();
  await node(page, 0); await node(page, 4);
  await page.getByRole('button', { name: 'Resistore' }).click();
  await node(page, 4); await node(page, 8);
  await page.getByLabel('Grandezza richiesta').selectOption('current');
  await page.getByLabel('Componente richiesto').selectOption('V1');
  await page.getByRole('button', { name: /Usa il circuito disegnato/ }).click();
  await expect(page.getByRole('textbox', { name: 'Circuito da risolvere' })).toHaveValue(/\? current V1$/);
});
