import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

function chromeExe(): string | undefined {
  const base = join(homedir(), "Library", "Caches", "ms-playwright");
  const candidates = ["chromium-1228", "chromium-1223", "chromium-1208"];
  for (const c of candidates) {
    const exe = join(
      base,
      c,
      "chrome-mac-arm64",
      "Google Chrome for Testing.app",
      "Contents",
      "MacOS",
      "Google Chrome for Testing",
    );
    if (existsSync(exe)) return exe;
  }
  return undefined;
}

const exe = chromeExe();

export default defineConfig({
  testDir: "./tests-e2e",
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:4173",
    trace: "retain-on-failure",
    ...(exe ? { launchOptions: { executablePath: exe } } : {}),
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "mobile", use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } } },
  ],
  webServer: {
    command: "npm run preview -- --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
