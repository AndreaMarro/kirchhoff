import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "./",
  publicDir: "public",
  build: {
    outDir: "dist",
    sourcemap: false,
    target: "es2022",
  },
  server: {
    port: 5173,
  },
  test: {
    // Solo unit test: le specifiche Playwright vivono in tests-e2e/
    // e le esegue `npm run test:e2e`, non vitest.
    include: ["tests/**/*.test.ts"],
  },
});
