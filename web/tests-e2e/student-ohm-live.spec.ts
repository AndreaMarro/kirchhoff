import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

const base = process.env.KIRCHHOFF_LIVE_BASE_URL;
test.skip(!base, "Avvia il server reale e imposta KIRCHHOFF_LIVE_BASE_URL.");

test("Ohm distingue riferimento e aritmetica e conserva gli operandi dopo riapertura", async ({ page, context, browser }) => {
  const netlist = "V1 a 0 12 volt\nR1 a b 1000 ohm\nR2 b 0 2000 ohm\n? voltage R2";
  await page.goto(base!);
  await page.getByRole("button", { name: /Il tuo circuito/ }).click();
  if (!await page.getByRole("textbox", { name: "Circuito da risolvere" }).isVisible())
    await page.getByText("Vista esperta: testo del circuito", { exact: true }).click();
  await page.getByRole("textbox", { name: "Circuito da risolvere" }).fill(netlist);
  await page.getByRole("button", { name: /Risolvi e spiega/ }).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.locator(".student-lesson")).toHaveAttribute("aria-busy", "false");
  await page.getByRole("combobox", { name: "Operazione passaggio 1" }).selectOption("ohm-tensione");
  await page.getByRole("textbox", { name: "Primo componente passaggio 1" }).fill("R2");
  await page.getByRole("textbox", { name: "Secondo componente passaggio 1" }).fill("R1");
  await page.getByRole("textbox", { name: "Valore passaggio 1" }).fill("4");
  await page.getByRole("button", { name: "Controlla i passaggi" }).click();
  await expect(page.locator(".student-trace-result")).toContainText("Rivedi il riferimento");
  await expect(page.locator(".student-trace-result")).toContainText("1000 ohm");
  await expect(page.locator(".student-trace-result")).toContainText("2000 ohm");

  await page.getByRole("textbox", { name: "Secondo componente passaggio 1" }).fill("R2");
  await page.getByRole("button", { name: "Controlla i passaggi" }).click();
  await expect(page.locator(".student-trace-result")).toContainText("Rivedi il calcolo");
  await page.getByRole("textbox", { name: "Valore passaggio 1" }).fill("8");
  await page.getByRole("button", { name: "Controlla i passaggi" }).click();
  await expect(page.locator(".student-trace-result")).toContainText("Passaggi controllati validi");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Salva quaderno ↓" }).click();
  const buffer = await readFile(await (await download).path());
  const saved = JSON.parse(buffer.toString());
  expect(saved.traceSteps[0]).toMatchObject({ operation: "ohm-tensione", first: "R2", second: "R2", claimed_value: "8" });
  const viewport = page.viewportSize()!;
  await context.close();
  const cold = await browser.newContext({ viewport });
  try {
    const reopened = await cold.newPage();
    await reopened.goto(base!);
    await reopened.locator('input[type=file][accept*="application/json"]').setInputFiles({ name: "quaderno.json", mimeType: "application/json", buffer });
    await expect(reopened.getByText(/Quaderno riaperto e soluzione ricalcolata/)).toBeVisible();
    await expect(reopened.getByRole("combobox", { name: "Operazione passaggio 1" })).toHaveValue("ohm-tensione");
    await expect(reopened.getByRole("textbox", { name: "Secondo componente passaggio 1" })).toHaveValue("R2");
    await reopened.getByRole("button", { name: "Controlla i passaggi" }).click();
    await expect(reopened.locator(".student-trace-result")).toContainText("Passaggi controllati validi");
  } finally {
    await cold.close();
  }
});
