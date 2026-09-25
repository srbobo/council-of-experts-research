import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:8642",
  },
  webServer: {
    command: "python3 -m http.server 8642 --bind 127.0.0.1",
    url: "http://127.0.0.1:8642/index.html",
    reuseExistingServer: true,
    timeout: 15_000,
  },
});
