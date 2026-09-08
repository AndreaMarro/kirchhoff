/* E2E del ramo guasto: fixture solo in questo file, mai nel corpus prodotto.
   Il guasto reale non esiste nel corpus visibile e non va fabbricato li';
   qui si verifica che la vista del guasto, se mai servisse, resti onesta. */
import { expect, test } from "@playwright/test";

const SESSIONE_GUASTO = {
  schema_version: "student-session.v0.1",
  session_id: "guasto-sintetico-solo-test",
  outcome: "failure",
  question: null,
  answer: null,
  truth: {
    electrical_claim_status: null,
    backend_closure_status: "FAILURE",
    product_verified: false,
  },
  states: [],
  steps: [],
  verification: null,
  provenance: null,
  refusal: null,
  failure: { dove: "orchestrazione-sintetica", messaggio: "cedimento finto per il test" },
};

test("il guasto si dichiara senza inventare risposte", async ({ page }) => {
  await page.route("**/sessions/index.json", async (route) => {
    const risposta = await route.fetch();
    const corpo = (await risposta.json()) as unknown[];
    corpo.push({
      id: "guasto-sintetico",
      titolo: "Guasto sintetico (solo test)",
      outcome: "failure",
      domanda: { quantity: "current", target: "RX" },
    });
    await route.fulfill({ response: risposta, json: corpo });
  });
  await page.route("**/sessions/guasto-sintetico.json", async (route) => {
    await route.fulfill({ json: SESSIONE_GUASTO });
  });
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(12, { timeout: 10_000 });
  await page.locator(".kf-chip").nth(11).click();
  await expect(page.locator(".kf-notice-failure h2")).toContainText("Guasto");
  await expect(page.locator('.kf-notice-failure[role="alert"]')).toHaveCount(1);
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("Product Verified");
  await expect(page.locator(".kf-pill-failure")).toContainText("Guasto");
  await page.locator(".kf-notice-failure .kf-tech summary").click();
  await expect(page.locator(".kf-notice-failure")).toContainText("orchestrazione-sintetica");
  await expect(page.locator(".kf-notice-failure")).toContainText("cedimento finto per il test");
});
