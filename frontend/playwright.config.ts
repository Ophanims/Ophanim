import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/application", timeout: 90_000, workers: 1,
  use: { baseURL: process.env.APPLICATION_TEST_URL || "http://127.0.0.1:3000",
    viewport: { width: 1440, height: 1000 },
    launchOptions: { channel: "chrome", args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] },
    screenshot: "only-on-failure", trace: "retain-on-failure" },
});
