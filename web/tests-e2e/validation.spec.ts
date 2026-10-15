import { expect, test } from "@playwright/test";
import type { StudentSessionView } from "../src/session/types.ts";

test("un link malformato apre il banco e la navigazione resta utilizzabile", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?view=proof#exercise=%&step=0&frame=before");
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await page.evaluate(() => { window.location.hash = "#exercise=%FF&step=0&frame=after"; });
  await expect(page.getByRole("button", { name: "Dopo", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  expect(errors).toEqual([]);
});

test("una sessione senza claim certificato non mostra una risposta verificata", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    payload.truth.electrical_claim_status = "UNVERIFIED";
    await route.fulfill({ response, json: payload });
  });
  await page.goto("/?view=proof");
  await expect(page.getByRole("heading", { name: "Impossibile caricare la sessione" })).toBeVisible();
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await expect(page.getByRole("status")).toHaveCount(0);
});

const invalidCases: Array<[string, string, (payload: StudentSessionView) => void]> = [
  ["verificatore assente", "partitore-d1", (p) => { p.verification!.claim_verifier = null; }],
  ["disegno nodale vuoto", "ponte-nodale", (p) => { p.states.forEach((s) => { s.svg = " "; }); }],
  ["fotogramma trasformativo assente", "partitore-d1", (p) => { p.steps[0]!.before_svg = null; }],
  ["passi riordinati", "partitore-d1", (p) => { p.steps.reverse(); }],
];
for (const [name, exercise, mutate] of invalidCases) {
  test(`il banco rifiuta la chiusura con ${name}`, async ({ page }) => {
    await page.route(`**/sessions/${exercise}.json`, async (route) => {
      const response = await route.fetch();
      const payload = await response.json() as StudentSessionView;
      mutate(payload);
      await route.fulfill({ response, json: payload });
    });
    await page.goto(`/?view=proof#exercise=${exercise}&step=0&frame=before`);
    await expect(page.getByRole("heading", { name: "Impossibile caricare la sessione" })).toBeVisible();
    await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
    await expect(page.getByRole("status")).toHaveCount(0);
  });
}
