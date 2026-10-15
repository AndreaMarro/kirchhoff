import { expect, test } from "@playwright/test";

test("un link malformato apre il banco e la navigazione resta utilizzabile", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/#exercise=%&step=0&frame=before");
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
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Impossibile caricare la sessione" })).toBeVisible();
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await expect(page.getByRole("status")).toHaveCount(0);
});
